from __future__ import annotations

import importlib
import base64
import os
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.auth import reset_authenticated_sessions
from app.core.settings import get_settings
from app.database import reset_database_runtime
from app.integrations.odoo_bridge import OdooBridgeClient, OdooBridgeError


class ClinicalApiAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(self.temp_dir.name, "clinical-api-test.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{database_path.replace(os.sep, '/')}"
        os.environ["CLINICAL_API_LOCAL_AUTH_PASSWORD"] = "test-secret"
        os.environ["CLINICAL_API_SEED_SAMPLE_DATA"] = "false"
        os.environ["CLINICAL_API_LOGIN_MAX_ATTEMPTS"] = "2"
        os.environ["CLINICAL_API_LOGIN_WINDOW_SECONDS"] = "60"
        os.environ["ODOO_BRIDGE_BASE_URL"] = ""
        os.environ["ODOO_BRIDGE_DB_NAME"] = ""
        os.environ["ODOO_BRIDGE_API_KEY"] = ""

        get_settings.cache_clear()
        reset_authenticated_sessions()
        reset_database_runtime()

        import app.main

        self.main_module = importlib.reload(app.main)
        self.client_context = TestClient(self.main_module.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)
        reset_authenticated_sessions()
        reset_database_runtime()
        get_settings.cache_clear()
        self.temp_dir.cleanup()

    def test_can_save_and_resume_a_draft_case(self) -> None:
        headers = self._login("dr.njoroge", "test-secret")
        create_response = self.client.post(
            "/api/cases",
            headers=headers,
            json=self._start_case_payload(),
        )
        self.assertEqual(create_response.status_code, 201)
        draft = create_response.json()["payload"]
        case_id = draft["external_case_id"]

        draft.update(
            {
                "indication": "Positive FIT and iron deficiency anaemia.",
                "consent_documented": True,
                "team_pause_completed": True,
                "sedation_anesthesia": "Conscious sedation",
                "prep_quality": "adequate",
                "bbps_right": 3,
                "bbps_transverse": 3,
                "bbps_left": 3,
                "cecum_reached": True,
                "cecal_landmark_appendiceal_orifice": True,
                "cecal_landmark_ileocecal_valve": True,
                "photo_cecum": True,
                "segment_exam": [{"segment_name": "cecum", "normal": True, "photo_taken": True}],
                "impression": "Normal colonoscopy.",
                "adverse_event_plan": "routine_discharge",
            }
        )

        save_response = self.client.put(f"/api/cases/{case_id}", headers=headers, json=draft)
        self.assertEqual(save_response.status_code, 200)
        reload_response = self.client.get(f"/api/cases/{case_id}", headers=headers)
        self.assertEqual(reload_response.status_code, 200)
        reloaded = reload_response.json()
        self.assertEqual(reloaded["indication"], "Positive FIT and iron deficiency anaemia.")
        self.assertEqual(reloaded["segment_exam"][0]["segment_name"], "cecum")

    def test_security_headers_are_present(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "no-referrer")
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_can_finalize_case_and_download_pdf(self) -> None:
        headers = self._login("dr.njoroge", "test-secret")
        case_id = self._create_ready_case(headers)

        ready_response = self.client.post(f"/api/cases/{case_id}/actions/mark_ready_for_signoff", headers=headers, json={})
        self.assertEqual(ready_response.status_code, 200, ready_response.text)

        finalize_response = self.client.post(f"/api/cases/{case_id}/actions/finalize", headers=headers, json={})
        self.assertEqual(finalize_response.status_code, 200)
        finalized = finalize_response.json()["payload"]
        self.assertEqual(finalized["case_status"], "finalized")

        pdf_response = self.client.get(f"/api/cases/{case_id}/pdf", headers=headers)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.headers["content-type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

        history_response = self.client.get(f"/api/cases/{case_id}/history", headers=headers)
        self.assertEqual(history_response.status_code, 200)
        history = history_response.json()
        self.assertEqual(len(history["revisions"]), 1)
        self.assertTrue(any(event["eventType"] == "report_finalized" for event in history["auditEvents"]))

    def test_can_attach_fetch_and_remove_case_image(self) -> None:
        headers = self._login("dr.njoroge", "test-secret")
        create_response = self.client.post(
            "/api/cases",
            headers=headers,
            json=self._start_case_payload(patient_identifier="PT-IMG-001"),
        )
        self.assertEqual(create_response.status_code, 201)
        case_id = create_response.json()["payload"]["external_case_id"]
        image_bytes = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
        )

        upload_response = self.client.post(
            f"/api/cases/{case_id}/images",
            headers=headers,
            data={"caption": "Cecal landmark"},
            files={"file": ("cecum.png", image_bytes, "image/png")},
        )
        self.assertEqual(upload_response.status_code, 201)
        uploaded_payload = upload_response.json()["payload"]
        self.assertEqual(len(uploaded_payload["image_attachments"]), 1)
        image_payload = uploaded_payload["image_attachments"][0]
        image_id = image_payload["external_image_id"]
        self.assertEqual(image_payload["caption"], "Cecal landmark")
        self.assertEqual(image_payload["content_type"], "image/png")

        image_response = self.client.get(f"/api/cases/{case_id}/images/{image_id}", headers=headers)
        self.assertEqual(image_response.status_code, 200)
        self.assertEqual(image_response.headers["content-type"], "image/png")
        self.assertEqual(image_response.content, image_bytes)

        delete_response = self.client.delete(f"/api/cases/{case_id}/images/{image_id}", headers=headers)
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["payload"]["image_attachments"], [])

        missing_response = self.client.get(f"/api/cases/{case_id}/images/{image_id}", headers=headers)
        self.assertEqual(missing_response.status_code, 404)
        history_response = self.client.get(f"/api/cases/{case_id}/history", headers=headers)
        history = history_response.json()
        self.assertTrue(any(event["eventType"] == "case_image_attached" for event in history["auditEvents"]))
        self.assertTrue(any(event["eventType"] == "case_image_removed" for event in history["auditEvents"]))

    def test_only_admin_can_reopen_finalized_case(self) -> None:
        endoscopist_headers = self._login("dr.njoroge", "test-secret")
        case_id = self._create_ready_case(endoscopist_headers)
        self.client.post(f"/api/cases/{case_id}/actions/mark_ready_for_signoff", headers=endoscopist_headers, json={})
        self.client.post(f"/api/cases/{case_id}/actions/finalize", headers=endoscopist_headers, json={})

        admin_headers = self._login("ops.admin", "test-secret")
        reopen_response = self.client.post(
            f"/api/cases/{case_id}/actions/reopen",
            headers=admin_headers,
            json={"reason": "Correction required after pathology review."},
        )
        self.assertEqual(reopen_response.status_code, 200)
        reopened = reopen_response.json()["payload"]
        self.assertEqual(reopened["case_status"], "draft_reopened")

        current_pdf_response = self.client.get(f"/api/cases/{case_id}/pdf", headers=admin_headers)
        self.assertEqual(current_pdf_response.status_code, 404)

        history_response = self.client.get(f"/api/cases/{case_id}/history", headers=admin_headers)
        history = history_response.json()
        self.assertTrue(any(event["eventType"] == "report_reopened" for event in history["auditEvents"]))
        revision_pdf_response = self.client.get(f"/api/cases/{case_id}/revisions/1/pdf", headers=admin_headers)
        self.assertEqual(revision_pdf_response.status_code, 200)

    def test_followup_task_closure_requires_resolution_note(self) -> None:
        headers = self._login("dr.njoroge", "test-secret")
        create_response = self.client.post(
            "/api/cases",
            headers=headers,
            json=self._start_case_payload(patient_identifier="PT-2026-004"),
        )
        draft = create_response.json()["payload"]
        case_id = draft["external_case_id"]
        draft.update(
            {
                "indication": "Positive FIT.",
                "consent_documented": True,
                "team_pause_completed": True,
                "sedation_anesthesia": "Conscious sedation",
                "prep_quality": "adequate",
                "bbps_right": 3,
                "bbps_transverse": 3,
                "bbps_left": 3,
                "cecum_reached": True,
                "cecal_landmark_appendiceal_orifice": True,
                "cecal_landmark_ileocecal_valve": True,
                "photo_cecum": True,
                "segment_exam": [{"segment_name": "cecum", "normal": True, "photo_taken": True}],
                "impression": "Single polyp removed.",
                "pathology_status": "pending_tracking_required",
                "adverse_event_plan": "routine_discharge",
                "followup_tasks": [
                    {
                        "task_type": "pathology_review",
                        "task_status": "open",
                        "task_owner_user_id": "dr.njoroge",
                        "task_owner_user_ref": "Dr. A. Njoroge",
                        "due_date": "2026-08-30",
                    }
                ],
            }
        )
        save_response = self.client.put(f"/api/cases/{case_id}", headers=headers, json=draft)
        self.assertEqual(save_response.status_code, 200)
        task_id = save_response.json()["payload"]["followup_tasks"][0]["followup_task_id"]

        invalid_close = self.client.put(
            f"/api/tasks/{task_id}",
            headers=headers,
            json={"task_status": "closed"},
        )
        self.assertEqual(invalid_close.status_code, 400)

        valid_close = self.client.put(
            f"/api/tasks/{task_id}",
            headers=headers,
            json={"task_status": "closed", "resolution_note": "Pathology reviewed and patient contacted."},
        )
        self.assertEqual(valid_close.status_code, 200)

        history_response = self.client.get(f"/api/cases/{case_id}/history", headers=headers)
        history = history_response.json()
        self.assertTrue(any(event["eventType"] == "followup_task_closed" for event in history["auditEvents"]))

    def test_facility_scope_prevents_cross_hospital_access(self) -> None:
        main_headers = self._login("dr.njoroge", "test-secret")
        day_headers = self._login("dr.kamau", "test-secret")
        workspace_headers = self._login("workspace.admin", "test-secret")

        day_create = self.client.post(
            "/api/cases",
            headers=day_headers,
            json=self._start_case_payload(
                patient_identifier="PT-DAY-001",
                facility_unit="DAY-BAY",
                endoscopist_user_id="dr.kamau",
                assistant_nurse_user_id="nurse.atieno",
            ),
        )
        self.assertEqual(day_create.status_code, 201)
        day_case_id = day_create.json()["payload"]["external_case_id"]

        hidden_from_main = self.client.get(f"/api/cases/{day_case_id}", headers=main_headers)
        self.assertEqual(hidden_from_main.status_code, 404)
        main_cases = self.client.get("/api/cases", headers=main_headers)
        self.assertEqual(main_cases.status_code, 200)
        self.assertNotIn(day_case_id, [item["id"] for item in main_cases.json()])

        visible_to_workspace = self.client.get(f"/api/cases/{day_case_id}", headers=workspace_headers)
        self.assertEqual(visible_to_workspace.status_code, 200)

        invalid_cross_facility_create = self.client.post(
            "/api/cases",
            headers=main_headers,
            json=self._start_case_payload(
                patient_identifier="PT-DAY-002",
                facility_unit="DAY-BAY",
                endoscopist_user_id="dr.kamau",
                assistant_nurse_user_id="nurse.atieno",
            ),
        )
        self.assertEqual(invalid_cross_facility_create.status_code, 403)

        therapeutic_create = self.client.post(
            "/api/cases",
            headers=main_headers,
            json=self._start_case_payload(patient_identifier="PT-THER-001", facility_unit="THER-SUITE"),
        )
        self.assertEqual(therapeutic_create.status_code, 201)

    def test_start_case_allows_an_unassigned_unit_and_nurse(self) -> None:
        headers = self._login("dr.njoroge", "test-secret")
        payload = self._start_case_payload(patient_identifier="PT-OPTIONAL-UNIT-001")
        payload["facilityUnit"] = ""
        payload["facilityCode"] = "MAIN"
        payload.pop("dobOrAge")
        payload.pop("assistantNurseUserId")

        response = self.client.post("/api/cases", headers=headers, json=payload)

        self.assertEqual(response.status_code, 201)
        created = response.json()["payload"]
        self.assertEqual(created["facility_code"], "MAIN")
        self.assertEqual(created["facility_unit"], "")
        self.assertIsNone(created["dob_or_age"])
        self.assertIsNone(created["assistant_nurse_user_id"])

    def test_start_case_infers_a_single_endoscopist_facility(self) -> None:
        headers = self._login("dr.kamau", "test-secret")
        payload = self._start_case_payload(
            patient_identifier="PT-INFERRED-FACILITY-001",
            facility_unit="",
            endoscopist_user_id="dr.kamau",
            assistant_nurse_user_id="",
        )
        payload.pop("facilityCode", None)

        response = self.client.post("/api/cases", headers=headers, json=payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["payload"]["facility_code"], "DAY")

    def test_login_is_throttled_after_repeated_failures(self) -> None:
        for _ in range(2):
            failed = self.client.post("/api/session/login", json={"login": "dr.njoroge", "password": "wrong-secret"})
            self.assertEqual(failed.status_code, 401)

        throttled = self.client.post("/api/session/login", json={"login": "dr.njoroge", "password": "wrong-secret"})
        self.assertEqual(throttled.status_code, 429)
        self.assertIn("Retry-After", throttled.headers)

    def test_production_settings_reject_default_local_password(self) -> None:
        original_environment = os.environ.get("ENVIRONMENT")
        original_password = os.environ.get("CLINICAL_API_LOCAL_AUTH_PASSWORD")

        try:
            os.environ["ENVIRONMENT"] = "production"
            os.environ["CLINICAL_API_LOCAL_AUTH_PASSWORD"] = "phd-ass-demo"
            get_settings.cache_clear()
            with self.assertRaises(ValueError):
                get_settings()
        finally:
            if original_environment is None:
                os.environ.pop("ENVIRONMENT", None)
            else:
                os.environ["ENVIRONMENT"] = original_environment

            if original_password is None:
                os.environ.pop("CLINICAL_API_LOCAL_AUTH_PASSWORD", None)
            else:
                os.environ["CLINICAL_API_LOCAL_AUTH_PASSWORD"] = original_password
            get_settings.cache_clear()

    def test_odoo_asset_download_rejects_unexpected_origin(self) -> None:
        client = OdooBridgeClient("https://odoo.internal", "phd_ass", "bridge-key")
        with self.assertRaises(OdooBridgeError):
            client.download_asset("session-token", "https://evil.example/reports/report.pdf", "report.pdf")

    def _login(self, login: str, password: str) -> dict[str, str]:
        response = self.client.post("/api/session/login", json={"login": login, "password": password})
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def _start_case_payload(
        self,
        patient_identifier: str = "PT-2026-003",
        facility_unit: str = "MAIN-R1",
        endoscopist_user_id: str = "dr.njoroge",
        assistant_nurse_user_id: str = "nurse.akinyi",
    ) -> dict[str, object]:
        return {
            "procedureType": "colonoscopy",
            "patientIdentifier": patient_identifier,
            "procedureDatetime": "2026-08-25T08:30:00Z",
            "dobOrAge": "54 years",
            "sex": "female",
            "patientIdentityVerified": True,
            "facilityUnit": facility_unit,
            "endoscopistUserId": endoscopist_user_id,
            "referrerService": "Gastroenterology Clinic",
            "assistantNurseUserId": assistant_nurse_user_id,
        }

    def _create_ready_case(self, headers: dict[str, str]) -> str:
        create_response = self.client.post("/api/cases", headers=headers, json=self._start_case_payload())
        self.assertEqual(create_response.status_code, 201)
        draft = create_response.json()["payload"]
        case_id = draft["external_case_id"]
        draft.update(
            {
                "indication": "Positive FIT and iron deficiency anaemia.",
                "consent_documented": True,
                "team_pause_completed": True,
                "sedation_anesthesia": "Conscious sedation",
                "prep_quality": "adequate",
                "bbps_right": 3,
                "bbps_transverse": 3,
                "bbps_left": 3,
                "cecum_reached": True,
                "cecal_landmark_appendiceal_orifice": True,
                "cecal_landmark_ileocecal_valve": True,
                "photo_cecum": True,
                "segment_exam": [{"segment_name": "cecum", "normal": True, "photo_taken": True}],
                "impression": "Normal colonoscopy.",
                "adverse_event_plan": "routine_discharge",
            }
        )
        save_response = self.client.put(f"/api/cases/{case_id}", headers=headers, json=draft)
        self.assertEqual(save_response.status_code, 200)
        return case_id


if __name__ == "__main__":
    unittest.main()
