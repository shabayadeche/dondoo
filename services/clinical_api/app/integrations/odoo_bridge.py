import json
from dataclasses import dataclass
from http import cookiejar
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urljoin, urlparse

from app.core.settings import get_settings


class OdooBridgeError(RuntimeError):
    pass


class OdooBridgeApplicationError(OdooBridgeError):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class OdooAuthenticatedUser:
    session_id: str
    user_id: str
    login: str
    display_name: str
    primary_role: str
    roles: list[str]
    facility_codes: list[str]


class OdooBridgeClient:
    def __init__(self, base_url: str, db_name: str, api_key: str, timeout_seconds: int = 10):
        self.base_url = base_url.rstrip("/")
        self.db_name = db_name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.db_name and self.api_key)

    @classmethod
    def from_settings(cls) -> "OdooBridgeClient":
        settings = get_settings()
        return cls(
            base_url=settings.odoo_bridge_base_url,
            db_name=settings.odoo_bridge_db_name,
            api_key=settings.odoo_bridge_api_key,
            timeout_seconds=settings.odoo_bridge_timeout_seconds,
        )

    def authenticate_user(self, login: str, password: str) -> OdooAuthenticatedUser:
        if not self.base_url or not self.db_name:
            raise OdooBridgeError("Odoo bridge authentication is not configured.")

        request_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.db_name,
                    "login": login,
                    "password": password,
                },
                "id": 1,
            }
        ).encode("utf-8")

        request_obj = urllib_request.Request(
            f"{self.base_url}/web/session/authenticate",
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        jar = cookiejar.CookieJar()
        opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(jar))
        try:
            with opener.open(request_obj, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8")
        except (urllib_error.HTTPError, urllib_error.URLError) as exc:
            raise OdooBridgeError("Odoo authentication failed.") from exc

        try:
            decoded = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise OdooBridgeError("Odoo authentication returned invalid JSON.") from exc

        if decoded.get("error"):
            error_payload = decoded["error"]
            message = error_payload.get("message") if isinstance(error_payload, dict) else str(error_payload)
            detail = error_payload.get("data") if isinstance(error_payload, dict) else None
            if isinstance(detail, dict):
                message = detail.get("message") or message
            raise OdooBridgeError(f"Odoo authentication failed: {message}")

        session_id = next((item.value for item in jar if item.name == "session_id"), "")
        if not session_id:
            raise OdooBridgeError("Odoo did not return a session cookie.")

        profile = self.get_authenticated_user(session_id)
        if not profile.get("roles"):
            raise OdooBridgeError("Your Odoo user does not have an endoscopy workspace role.")

        return OdooAuthenticatedUser(
            session_id=session_id,
            user_id=str(profile.get("user_id") or ""),
            login=str(profile.get("login") or login),
            display_name=str(profile.get("display_name") or login),
            primary_role=str(profile.get("primary_role") or "user"),
            roles=[str(role) for role in profile.get("roles") or []],
            facility_codes=[str(code) for code in profile.get("facility_codes") or []],
        )

    def get_authenticated_user(self, session_id: str) -> dict:
        return self._call("/phd_ass_bridge/me", {}, session_id=session_id)

    def sync_case(self, session_id: str, payload: dict) -> dict:
        return self._call("/phd_ass_bridge/sync_case", {"payload": payload}, session_id=session_id)

    def list_cases(self, session_id: str) -> list[dict]:
        result = self._call("/phd_ass_bridge/cases", {}, session_id=session_id)
        return result.get("cases", [])

    def get_case(self, session_id: str, external_case_id: str) -> dict | None:
        result = self._call("/phd_ass_bridge/case", {"external_case_id": external_case_id}, session_id=session_id)
        if result.get("status") == "not_found":
            return None
        return result.get("case")

    def list_tasks(self, session_id: str) -> list[dict]:
        result = self._call("/phd_ass_bridge/tasks", {}, session_id=session_id)
        return result.get("tasks", [])

    def get_lookups(self, session_id: str) -> dict:
        return self._call("/phd_ass_bridge/lookups", {}, session_id=session_id)

    def get_patient_relationship(self, session_id: str, patient_identifier: str) -> dict | None:
        result = self._call(
            "/phd_ass_bridge/patient_relationship",
            {"patient_identifier": patient_identifier},
            session_id=session_id,
        )
        return result.get("relationship") if result.get("status") == "ok" else None

    def search_patients(self, session_id: str, query: str) -> list[dict]:
        result = self._call("/phd_ass_bridge/patients/search", {"query": query}, session_id=session_id)
        return result.get("patients", [])

    def get_case_history(self, session_id: str, external_case_id: str) -> dict:
        return self._call("/phd_ass_bridge/case_history", {"external_case_id": external_case_id}, session_id=session_id)

    def update_task(self, session_id: str, external_task_id: str, payload: dict) -> dict:
        params = {"external_task_id": external_task_id, "payload": payload}
        return self._call("/phd_ass_bridge/task_update", params, session_id=session_id)

    def case_action(self, session_id: str, external_case_id: str, action: str, payload: dict | None = None) -> dict:
        params = {
            "external_case_id": external_case_id,
            "action": action,
            "payload": payload or {},
        }
        return self._call("/phd_ass_bridge/case_action", params, session_id=session_id)

    def _call(self, path: str, params: dict, session_id: str | None = None) -> dict:
        if not self.enabled:
            raise OdooBridgeError("Odoo bridge client is not configured.")

        # Odoo controllers receive JSON-RPC parameters reliably on both the
        # local application server and through a reverse proxy.  Retain the
        # header for backward compatibility, but send the bridge key as the
        # controller's explicit parameter as well.
        request_params = {**params, "api_key": self.api_key}
        request_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": request_params,
                "id": 1,
            }
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "X-PhD-Ass-Api-Key": self.api_key,
        }
        if session_id:
            headers["Cookie"] = f"session_id={session_id}"
        request_obj = urllib_request.Request(
            f"{self.base_url}{path}",
            data=request_body,
            headers=headers,
            method="POST",
        )

        try:
            with urllib_request.urlopen(request_obj, timeout=self.timeout_seconds) as response:
                response_text = response.read().decode("utf-8")
        except (urllib_error.HTTPError, urllib_error.URLError) as exc:
            raise OdooBridgeError(f"Odoo bridge request failed: {exc}") from exc

        try:
            decoded = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise OdooBridgeError("Odoo bridge returned invalid JSON.") from exc

        if not isinstance(decoded, dict):
            raise OdooBridgeError("Odoo bridge returned an unexpected response shape.")

        if decoded.get("error"):
            error_payload = decoded["error"]
            message = error_payload.get("message") if isinstance(error_payload, dict) else str(error_payload)
            detail = error_payload.get("data") if isinstance(error_payload, dict) else None
            if isinstance(detail, dict):
                message = detail.get("message") or message
                exception_name = str(detail.get("name") or "")
                if exception_name.endswith(("ValidationError", "UserError")):
                    raise OdooBridgeApplicationError(str(message), 400)
                if exception_name.endswith(("AccessDenied", "AccessError")):
                    raise OdooBridgeApplicationError(str(message), 403)
            raise OdooBridgeError(f"Odoo bridge error: {message}")

        result = decoded.get("result")
        if not isinstance(result, dict):
            raise OdooBridgeError("Odoo bridge returned no result payload.")
        return result

    def download_asset(self, session_id: str, asset_path: str, fallback_name: str) -> tuple[bytes, str]:
        if not asset_path:
            raise OdooBridgeError("The requested Odoo asset path is empty.")

        target = self._resolve_asset_url(asset_path)
        request_obj = urllib_request.Request(
            target,
            headers={
                "Cookie": f"session_id={session_id}",
            },
            method="GET",
        )

        try:
            with urllib_request.urlopen(request_obj, timeout=self.timeout_seconds) as response:
                payload = response.read()
                content_disposition = response.headers.get("Content-Disposition", "")
        except (urllib_error.HTTPError, urllib_error.URLError) as exc:
            raise OdooBridgeError(f"Failed to download Odoo asset: {exc}") from exc

        filename = fallback_name
        if "filename=" in content_disposition:
            filename = content_disposition.split("filename=", 1)[1].strip().strip('"') or fallback_name
        return payload, filename

    def _resolve_asset_url(self, asset_path: str) -> str:
        target = asset_path
        if not asset_path.startswith(("http://", "https://")):
            target = urljoin(f"{self.base_url}/", asset_path.lstrip("/"))

        base = urlparse(self.base_url)
        resolved = urlparse(target)
        if resolved.scheme not in {"http", "https"}:
            raise OdooBridgeError("The requested Odoo asset uses an unsupported URL scheme.")

        if (
            resolved.scheme.lower(),
            (resolved.hostname or "").lower(),
            _normalized_port(resolved.scheme, resolved.port),
        ) != (
            base.scheme.lower(),
            (base.hostname or "").lower(),
            _normalized_port(base.scheme, base.port),
        ):
            raise OdooBridgeError("Refused to download an Odoo asset from an unexpected origin.")

        return target


def _normalized_port(scheme: str, port: int | None) -> int:
    if port is not None:
        return port
    return 443 if scheme.lower() == "https" else 80
