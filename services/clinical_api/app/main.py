from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import router
from app.core.settings import get_settings, is_local_host
from app.database import init_database
from app.repositories.cases import bootstrap_local_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    init_database()
    bootstrap_local_database()
    yield


def _request_scheme(request: Request) -> str:
    if settings.clinical_api_trust_forwarded_proto:
        forwarded = request.headers.get("x-forwarded-proto", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip().lower()
    return request.url.scheme.lower()


def _is_local_request(request: Request) -> bool:
    if is_local_host(request.url.hostname):
        return True
    if request.client and is_local_host(request.client.host):
        return True
    return False


def _apply_security_headers(request: Request, response: Response) -> None:
    if not settings.clinical_api_security_headers_enabled:
        return

    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

    if request.url.path == "/health" or request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("Pragma", "no-cache")

    if settings.https_required and _request_scheme(request) == "https" and not _is_local_request(request):
        response.headers.setdefault(
            "Strict-Transport-Security",
            f"max-age={settings.clinical_api_hsts_max_age_seconds}; includeSubDomains",
        )


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-PhD-Ass-Api-Key"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next) -> Response:
    if settings.https_required and not _is_local_request(request) and _request_scheme(request) != "https":
        return JSONResponse(status_code=400, content={"detail": "HTTPS is required for the clinical API."})

    response = await call_next(request)
    _apply_security_headers(request, response)
    return response


app.include_router(router)
