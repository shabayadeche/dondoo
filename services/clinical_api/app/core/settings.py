from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "testserver"}


def parse_csv_setting(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def is_local_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.strip().lower()
    return normalized in LOCAL_HOSTS or normalized.endswith(".localhost")


class Settings(BaseSettings):
    app_name: str = "Dondoo"
    environment: str = "development"
    allow_origins: str = "http://127.0.0.1:4173,http://localhost:4173,http://127.0.0.1:4174,http://localhost:4174"
    clinical_api_trusted_hosts: str = "127.0.0.1,localhost,::1,testserver"
    clinical_api_enable_docs: bool | None = None
    clinical_api_require_https: bool | None = None
    clinical_api_trust_forwarded_proto: bool = True
    clinical_api_security_headers_enabled: bool = True
    clinical_api_hsts_max_age_seconds: int = 31536000
    clinical_api_login_window_seconds: int = 900
    clinical_api_login_max_attempts: int = 5
    clinical_api_max_active_sessions_per_user: int = 3
    database_url: str = "sqlite:///./clinical_api.db"
    odoo_bridge_base_url: str = ""
    odoo_bridge_db_name: str = ""
    odoo_bridge_api_key: str = ""
    odoo_bridge_timeout_seconds: int = 10
    odoo_recommended_module: str = "phd_ass_bridge"
    odoo_recommended_module_label: str = "Dondoo Clinical Workspace"
    clinical_api_session_ttl_minutes: int = 120
    clinical_api_local_auth_password: str = "phd-ass-demo"
    clinical_api_seed_sample_data: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_development_like(self) -> bool:
        return self.environment.strip().lower() in {"development", "test"}

    @property
    def allow_origins_list(self) -> list[str]:
        return parse_csv_setting(self.allow_origins)

    @property
    def trusted_hosts_list(self) -> list[str]:
        return parse_csv_setting(self.clinical_api_trusted_hosts)

    @property
    def docs_enabled(self) -> bool:
        if self.clinical_api_enable_docs is not None:
            return self.clinical_api_enable_docs
        return self.is_development_like

    @property
    def https_required(self) -> bool:
        if self.clinical_api_require_https is not None:
            return self.clinical_api_require_https
        return not self.is_development_like

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        if self.clinical_api_session_ttl_minutes <= 0:
            raise ValueError("CLINICAL_API_SESSION_TTL_MINUTES must be greater than zero.")
        if self.clinical_api_login_window_seconds <= 0:
            raise ValueError("CLINICAL_API_LOGIN_WINDOW_SECONDS must be greater than zero.")
        if self.clinical_api_login_max_attempts <= 0:
            raise ValueError("CLINICAL_API_LOGIN_MAX_ATTEMPTS must be greater than zero.")
        if self.clinical_api_max_active_sessions_per_user <= 0:
            raise ValueError("CLINICAL_API_MAX_ACTIVE_SESSIONS_PER_USER must be greater than zero.")
        if self.clinical_api_hsts_max_age_seconds < 0:
            raise ValueError("CLINICAL_API_HSTS_MAX_AGE_SECONDS cannot be negative.")

        if "*" in self.allow_origins_list:
            raise ValueError("Wildcard CORS origins are not allowed for the clinical API.")

        if not self.is_development_like and self.clinical_api_local_auth_password == "phd-ass-demo":
            raise ValueError("Set CLINICAL_API_LOCAL_AUTH_PASSWORD before running outside development.")

        if self.https_required:
            for origin in self.allow_origins_list:
                parsed = urlparse(origin)
                if parsed.scheme != "https" and not is_local_host(parsed.hostname):
                    raise ValueError("Non-local CORS origins must use HTTPS when HTTPS enforcement is enabled.")

            if self.odoo_bridge_base_url:
                parsed = urlparse(self.odoo_bridge_base_url)
                if parsed.scheme != "https" and not is_local_host(parsed.hostname):
                    raise ValueError("ODOO_BRIDGE_BASE_URL must use HTTPS outside local development.")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
