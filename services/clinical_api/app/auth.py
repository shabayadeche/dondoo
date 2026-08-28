from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import Header, HTTPException, status

from app.core.settings import get_settings


SESSION_HEADER_PREFIX = "Bearer "


@dataclass
class AuthenticatedSession:
    token: str
    user_id: str
    login: str
    display_name: str
    primary_role: str
    roles: tuple[str, ...]
    facility_codes: tuple[str, ...]
    odoo_session_id: str
    issued_at: datetime
    expires_at: datetime


_session_store: dict[str, AuthenticatedSession] = {}
_user_sessions: dict[str, list[str]] = {}
_failed_login_attempts: dict[str, list[datetime]] = {}


def create_authenticated_session(
    *,
    user_id: str,
    login: str,
    display_name: str,
    primary_role: str,
    roles: list[str],
    facility_codes: list[str] | None = None,
    odoo_session_id: str,
) -> AuthenticatedSession:
    settings = get_settings()
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.clinical_api_session_ttl_minutes)
    token = token_urlsafe(48)
    session = AuthenticatedSession(
        token=token,
        user_id=user_id,
        login=login,
        display_name=display_name,
        primary_role=primary_role,
        roles=tuple(roles),
        facility_codes=tuple(sorted({code.strip() for code in facility_codes or [] if code and code.strip()})),
        odoo_session_id=odoo_session_id,
        issued_at=issued_at,
        expires_at=expires_at,
    )
    _purge_expired_sessions()
    _enforce_session_limit(user_id, settings.clinical_api_max_active_sessions_per_user)
    _session_store[token] = session
    _user_sessions.setdefault(user_id, []).append(token)
    return session


def revoke_authenticated_session(token: str) -> None:
    _remove_session_token(token)


def get_authenticated_session(authorization: str | None = Header(default=None)) -> AuthenticatedSession:
    if not authorization or not authorization.startswith(SESSION_HEADER_PREFIX):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    token = authorization[len(SESSION_HEADER_PREFIX) :].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    _purge_expired_sessions()
    session = _session_store.get(token)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session is invalid or expired.")
    return session


def get_optional_authenticated_session(authorization: str | None = Header(default=None)) -> AuthenticatedSession | None:
    if not authorization:
        return None
    return get_authenticated_session(authorization)


def _purge_expired_sessions() -> None:
    now = datetime.now(timezone.utc)
    expired_tokens = [token for token, session in _session_store.items() if session.expires_at <= now]
    for token in expired_tokens:
        _remove_session_token(token)


def _enforce_session_limit(user_id: str, max_active_sessions: int) -> None:
    active_tokens = _user_sessions.get(user_id, [])
    while len(active_tokens) >= max_active_sessions:
        _remove_session_token(active_tokens[0])
        active_tokens = _user_sessions.get(user_id, [])


def _remove_session_token(token: str) -> None:
    session = _session_store.pop(token, None)
    if not session:
        return
    active_tokens = _user_sessions.get(session.user_id, [])
    if token in active_tokens:
        active_tokens.remove(token)
    if active_tokens:
        _user_sessions[session.user_id] = active_tokens
    else:
        _user_sessions.pop(session.user_id, None)


def get_login_retry_after_seconds(login: str, client_host: str | None) -> int | None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window = timedelta(seconds=settings.clinical_api_login_window_seconds)
    key = _login_attempt_key(login, client_host)
    attempts = [stamp for stamp in _failed_login_attempts.get(key, []) if stamp > now - window]
    if attempts:
        _failed_login_attempts[key] = attempts
    else:
        _failed_login_attempts.pop(key, None)

    if len(attempts) < settings.clinical_api_login_max_attempts:
        return None

    retry_after = int((attempts[0] + window - now).total_seconds())
    return max(retry_after, 1)


def record_failed_login_attempt(login: str, client_host: str | None) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window = timedelta(seconds=settings.clinical_api_login_window_seconds)
    key = _login_attempt_key(login, client_host)
    attempts = [stamp for stamp in _failed_login_attempts.get(key, []) if stamp > now - window]
    attempts.append(now)
    _failed_login_attempts[key] = attempts


def clear_failed_login_attempts(login: str, client_host: str | None) -> None:
    _failed_login_attempts.pop(_login_attempt_key(login, client_host), None)


def _login_attempt_key(login: str, client_host: str | None) -> str:
    normalized_login = login.strip().lower()
    normalized_host = (client_host or "unknown").strip().lower()
    return f"{normalized_host}|{normalized_login}"


def reset_authenticated_sessions() -> None:
    _session_store.clear()
    _user_sessions.clear()
    _failed_login_attempts.clear()
