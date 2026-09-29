import logging
from secrets import compare_digest

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import (
    clear_failed_login_attempts,
    create_authenticated_session,
    get_authenticated_session,
    get_login_retry_after_seconds,
    record_failed_login_attempt,
    revoke_authenticated_session,
)
from app.core.settings import get_settings
from app.integrations.odoo_bridge import OdooBridgeClient, OdooBridgeError
from app.reference_data import DEFAULT_LOCAL_AUTH_USERS
from app.schemas import AuthenticatedSessionPayload, LoginPayload

router = APIRouter()
logger = logging.getLogger(__name__)


def _client() -> OdooBridgeClient:
    client = OdooBridgeClient.from_settings()
    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Odoo bridge authentication is not configured for the clinical API.",
        )
    return client


@router.post("/session/login", response_model=AuthenticatedSessionPayload)
def login(payload: LoginPayload, request: Request) -> AuthenticatedSessionPayload:
    client_host = request.client.host if request.client and request.client.host else "unknown"
    retry_after = get_login_retry_after_seconds(payload.login, client_host)
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    client = OdooBridgeClient.from_settings()
    if client.enabled:
        try:
            odoo_session = client.authenticate_user(payload.login, payload.password)
        except OdooBridgeError as exc:
            # Keep the client response intentionally generic, but retain the
            # underlying bridge failure in the protected service logs so
            # production authentication incidents can be diagnosed safely.
            logger.warning("Odoo workspace login failed for %r: %s", payload.login, exc)
            record_failed_login_attempt(payload.login, client_host)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Workspace login failed.") from exc

        session = create_authenticated_session(
            user_id=odoo_session.user_id,
            login=odoo_session.login,
            display_name=odoo_session.display_name,
            primary_role=odoo_session.primary_role,
            roles=odoo_session.roles,
            facility_codes=odoo_session.facility_codes,
            odoo_session_id=odoo_session.session_id,
        )
    else:
        settings = get_settings()
        profile = DEFAULT_LOCAL_AUTH_USERS.get(payload.login)
        if not profile or not compare_digest(payload.password, settings.clinical_api_local_auth_password):
            record_failed_login_attempt(payload.login, client_host)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Workspace login failed.")

        session = create_authenticated_session(
            user_id=str(profile["user_id"]),
            login=payload.login,
            display_name=str(profile["display_name"]),
            primary_role=str(profile["primary_role"]),
            roles=[str(role) for role in profile["roles"]],
            facility_codes=[str(code) for code in profile.get("facility_codes", [])],
            odoo_session_id="",
        )

    clear_failed_login_attempts(payload.login, client_host)
    return AuthenticatedSessionPayload(
        token=session.token,
        userId=session.user_id,
        login=session.login,
        displayName=session.display_name,
        primaryRole=session.primary_role,
        roles=list(session.roles),
        facilityCodes=list(session.facility_codes),
        expiresAt=session.expires_at.isoformat(),
    )


@router.get("/session/me", response_model=AuthenticatedSessionPayload)
def me(session=Depends(get_authenticated_session)) -> AuthenticatedSessionPayload:
    return AuthenticatedSessionPayload(
        token=session.token,
        userId=session.user_id,
        login=session.login,
        displayName=session.display_name,
        primaryRole=session.primary_role,
        roles=list(session.roles),
        facilityCodes=list(session.facility_codes),
        expiresAt=session.expires_at.isoformat(),
    )


@router.post("/session/logout")
def logout(session=Depends(get_authenticated_session)) -> dict[str, str]:
    revoke_authenticated_session(session.token)
    return {"status": "ok"}
