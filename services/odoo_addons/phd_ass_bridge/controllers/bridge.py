from odoo import fields, http
from odoo.exceptions import AccessDenied, ValidationError
from odoo.http import request


DEFAULT_REFERRER_SERVICES = [
    "Emergency Department",
    "Gastroenterology Clinic",
    "General Surgery",
    "Internal Medicine",
    "Oncology",
    "Upper GI Clinic",
]


class PhdAssBridgeController(http.Controller):
    @http.route("/phd_ass_bridge/health", type="jsonrpc", auth="user")
    def health(self):
        config = request.env["ir.config_parameter"].sudo()
        return {
            "status": "ok",
            "module": "phd_ass_bridge",
            "clinical_api_base_url": config.get_param("phd_ass_bridge.clinical_api_base_url", ""),
        }

    @http.route("/phd_ass_bridge/me", type="jsonrpc", auth="user", csrf=False)
    def me(self, api_key=None):
        self._validate_service_key(api_key)
        user = request.env.user
        roles = self._roles_for_user(user)
        return {
            "status": "ok",
            "user_id": user.id,
            "login": user.login,
            "display_name": user.display_name,
            "primary_role": self._primary_role(roles),
            "roles": roles,
            "facility_codes": self._facility_codes_for_user(user),
        }

    @http.route("/phd_ass_bridge/sync_case", type="jsonrpc", auth="user", csrf=False)
    def sync_case(self, api_key=None, payload=None):
        self._validate_service_key(api_key)
        case_record = request.env["phd.ass.case"].sync_from_payload(payload or {})
        return {
            "status": "ok",
            "case_id": case_record.id,
            "external_case_id": case_record.external_case_id,
            "last_synced_at": case_record.last_synced_at,
        }

    @http.route("/phd_ass_bridge/sync_task", type="jsonrpc", auth="user", csrf=False)
    def sync_task(self, api_key=None, payload=None):
        self._validate_service_key(api_key)
        task_record = request.env["phd.ass.followup.task"].sync_from_payload(payload or {})
        return {
            "status": "ok",
            "task_id": task_record.id,
            "external_task_id": task_record.external_task_id,
            "last_synced_at": task_record.last_synced_at,
        }

    @http.route("/phd_ass_bridge/cases", type="jsonrpc", auth="user", csrf=False)
    def list_cases(self, api_key=None):
        self._validate_service_key(api_key)
        case_model = request.env["phd.ass.case"]
        records = case_model.search([], order="procedure_datetime desc, id desc")
        return {
            "status": "ok",
            "cases": [self._case_summary_payload(record) for record in records],
        }

    @http.route("/phd_ass_bridge/case", type="jsonrpc", auth="user", csrf=False)
    def get_case(self, external_case_id=None, api_key=None):
        self._validate_service_key(api_key)
        record = self._find_case_record(external_case_id)
        if not record:
            return {"status": "not_found", "case": False}

        payload = record._serialize_for_clinical_api()
        payload["case_id"] = record.external_case_id
        return {
            "status": "ok",
            "case": payload,
        }

    @http.route("/phd_ass_bridge/case_history", type="jsonrpc", auth="user", csrf=False)
    def get_case_history(self, external_case_id=None, api_key=None):
        self._validate_service_key(api_key)
        record = self._find_case_record(external_case_id)
        if not record:
            return {"status": "not_found", "caseId": external_case_id, "revisions": [], "auditEvents": []}

        return {
            "status": "ok",
            "caseId": record.external_case_id,
            "revisions": [self._revision_payload(record, revision) for revision in sorted(record.sudo().revision_ids, key=lambda item: item.revision_number, reverse=True)],
            "auditEvents": [self._audit_event_payload(event) for event in sorted(record.sudo().audit_event_ids, key=lambda item: item.create_date or item.id, reverse=True)],
        }

    @http.route("/phd_ass_bridge/tasks", type="jsonrpc", auth="user", csrf=False)
    def list_tasks(self, api_key=None):
        self._validate_service_key(api_key)
        task_model = request.env["phd.ass.followup.task"]
        records = task_model.search([], order="due_date desc, id desc")
        return {
            "status": "ok",
            "tasks": [self._task_payload(record) for record in records],
        }

    @http.route("/phd_ass_bridge/lookups", type="jsonrpc", auth="user", csrf=False)
    def get_lookups(self, api_key=None):
        self._validate_service_key(api_key)
        facility_model = request.env["phd.ass.facility"].sudo().with_context(active_test=False)
        unit_model = request.env["phd.ass.facility.unit"].sudo().with_context(active_test=False)
        facility_domain = [("active", "=", True)]
        allowed_facility_ids = self._allowed_facility_ids_for_user(request.env.user)
        if allowed_facility_ids is not None:
            facility_domain.append(("id", "in", allowed_facility_ids))
        facilities = facility_model.search(facility_domain, order="name, id")
        units = unit_model.search([("active", "=", True), ("facility_id", "in", facilities.ids)], order="facility_id, name, id")
        return {
            "status": "ok",
            "facilities": [
                {
                    "code": facility.code or facility.name,
                    "label": facility.name,
                }
                for facility in facilities
            ],
            "facilityUnits": [
                {
                    "code": unit.code or unit.full_name or unit.name,
                    "label": unit.full_name or unit.name,
                    "facilityCode": unit.facility_id.code or unit.facility_id.name or False,
                }
                for unit in units
            ],
            "endoscopists": self._clinician_payloads("phd_ass_bridge.group_phd_ass_endoscopist", "endoscopist", facilities),
            "nurses": self._nurse_payloads(facilities),
            "referrerServices": self._referrer_service_payloads(),
        }

    @http.route("/phd_ass_bridge/patient_relationship", type="jsonrpc", auth="user", csrf=False)
    def get_patient_relationship(self, patient_identifier=None, api_key=None):
        self._validate_service_key(api_key)
        identifier = str(patient_identifier or "").strip()
        if not identifier:
            return {"status": "not_found", "relationship": False}

        patient = request.env["phd.ass.patient"].search(
            [("patient_identifier", "=", identifier), ("active", "=", True)], limit=1
        )
        if not patient:
            return {"status": "not_found", "relationship": False}

        today = fields.Date.today()
        relationships = request.env["phd.ass.patient.care.relationship"].search([
            ("patient_id", "=", patient.id),
            ("active", "=", True),
            ("relationship_type", "=", "primary_endoscopist"),
            ("is_primary", "=", True),
            ("start_date", "<=", today),
            "|", ("end_date", "=", False), ("end_date", ">=", today),
        ], order="start_date desc, id desc", limit=1)
        if not relationships:
            return {"status": "not_found", "relationship": False}

        relationship = relationships[0]
        allowed_facility_ids = self._allowed_facility_ids_for_user(request.env.user)
        if allowed_facility_ids is not None and relationship.facility_id.id not in allowed_facility_ids:
            return {"status": "not_found", "relationship": False}
        return {
            "status": "ok",
            "relationship": {
                "relationshipId": relationship.id,
                "patientIdentifier": patient.patient_identifier,
                "facilityCode": relationship.facility_id.code or relationship.facility_id.name,
                "facilityLabel": relationship.facility_id.name,
                "facilityUnitCode": relationship.facility_unit_id.code if relationship.facility_unit_id else False,
                "facilityUnitLabel": relationship.facility_unit_id.full_name if relationship.facility_unit_id else False,
                "endoscopistUserId": relationship.endoscopist_user_id.login or str(relationship.endoscopist_user_id.id),
                "endoscopistLabel": relationship.endoscopist_user_id.display_name,
            },
        }

    @http.route("/phd_ass_bridge/patients/search", type="jsonrpc", auth="user", csrf=False)
    def search_patients(self, query=None, api_key=None):
        self._validate_service_key(api_key)
        term = str(query or "").strip()
        if len(term) < 2:
            return {"status": "ok", "patients": []}
        patient_model = request.env["phd.ass.patient"]
        patients = patient_model.search([
            "|", "|",
            ("patient_identifier", "ilike", term),
            ("full_name", "ilike", term),
            ("medical_record_number", "ilike", term),
        ], order="full_name, patient_identifier, id", limit=20)
        return {
            "status": "ok",
            "patients": [
                {
                    "patientIdentifier": patient.patient_identifier,
                    "displayName": patient.name,
                    "medicalRecordNumber": patient.medical_record_number or False,
                    "dobOrAge": patient.dob_or_age or False,
                    "sex": patient.sex or False,
                }
                for patient in patients
            ],
        }

    @http.route("/phd_ass_bridge/case_action", type="jsonrpc", auth="user", csrf=False)
    def case_action(self, external_case_id=None, action=None, payload=None, api_key=None):
        self._validate_service_key(api_key)
        record = self._find_case_record(external_case_id)
        if not record:
            return {"status": "not_found", "case": False}

        case_record = record.with_user(request.env.user)
        action_payload = payload or {}
        if action == "preview":
            case_record.action_generate_report_preview()
        elif action == "mark_ready_for_signoff":
            case_record.action_mark_ready_for_signoff()
        elif action == "finalize":
            case_record.action_finalize_report()
        elif action == "return_to_draft":
            case_record.action_return_to_draft()
        elif action == "reopen":
            case_record._reopen_case(str(action_payload.get("reason") or "").strip())
        else:
            raise ValidationError("Unsupported clinical case action.")

        refreshed = self._find_case_record(external_case_id)
        case_payload = refreshed._serialize_for_clinical_api()
        case_payload["case_id"] = refreshed.external_case_id
        return {
            "status": "ok",
            "case": case_payload,
        }

    @http.route("/phd_ass_bridge/task_update", type="jsonrpc", auth="user", csrf=False)
    def update_task(self, external_task_id=None, payload=None, api_key=None):
        self._validate_service_key(api_key)
        task_model = request.env["phd.ass.followup.task"]
        record = task_model.search([("external_task_id", "=", external_task_id)], limit=1)
        if not record:
            return {"status": "not_found", "task": False}

        vals = self._task_write_vals(payload or {})
        if vals:
            record.with_user(request.env.user).write(vals)
            if vals.get("task_status") not in {"closed", "cancelled"}:
                record.sudo().with_context(phd_ass_bridge_sync=True).write(
                    {
                        "closed_at": False,
                        "closed_by_user_id": False,
                        "closed_by_user_ref": False,
                    }
                )

        return {
            "status": "ok",
            "external_case_id": record.case_id.external_case_id,
            "task": self._task_payload(record),
        }

    def _validate_service_key(self, api_key=None):
        config = request.env["ir.config_parameter"].sudo()
        configured_key = config.get_param("phd_ass_bridge.clinical_api_key", "")
        provided_key = api_key or request.httprequest.headers.get("X-PhD-Ass-Api-Key")

        if not configured_key:
            raise AccessDenied("The bridge service key is not configured in Odoo settings.")
        if not provided_key:
            raise AccessDenied("A bridge service key is required.")
        if provided_key != configured_key:
            raise AccessDenied("The provided bridge service key is invalid.")

    def _roles_for_user(self, user):
        roles = []
        if user.has_group("phd_ass_bridge.group_phd_ass_endoscopist"):
            roles.append("endoscopist")
        if user.has_group("phd_ass_bridge.group_phd_ass_nurse"):
            roles.append("nurse")
        if user.has_group("phd_ass_bridge.group_phd_ass_operations_admin"):
            roles.append("operations_admin")
        if user.has_group("phd_ass_bridge.group_phd_ass_admin"):
            roles.append("workspace_admin")
        return roles

    def _primary_role(self, roles):
        for candidate in ("workspace_admin", "operations_admin", "endoscopist", "nurse"):
            if candidate in roles:
                return candidate
        return "user"

    def _allowed_facility_ids_for_user(self, user):
        if user.has_group("phd_ass_bridge.group_phd_ass_admin"):
            return None
        return user.sudo().phd_ass_facility_ids.ids

    def _facility_codes_for_user(self, user):
        facilities = request.env["phd.ass.facility"].sudo()
        facility_ids = self._allowed_facility_ids_for_user(user)
        if facility_ids is not None:
            facilities = facilities.browse(facility_ids)
        else:
            facilities = facilities.search([("active", "=", True)], order="name, id")
        return [facility.code or facility.name for facility in facilities if facility.active]

    def _find_case_record(self, external_case_id):
        case_model = request.env["phd.ass.case"]
        return case_model.search([("external_case_id", "=", external_case_id)], limit=1)

    def _case_summary_payload(self, case_record):
        payload = case_record._serialize_for_clinical_api()
        return {
            "external_case_id": case_record.external_case_id,
            "patient_identifier": payload.get("patient_identifier"),
            "procedure_type": payload.get("procedure_type"),
            "case_status": payload.get("case_status"),
            "procedure_datetime": payload.get("procedure_datetime"),
            "endoscopist_user_id": payload.get("endoscopist_user_id"),
            "endoscopist_user_ref": payload.get("endoscopist_user_ref"),
        }

    def _task_payload(self, task_record):
        return {
            "external_task_id": task_record.external_task_id,
            "followup_task_id": task_record.external_task_id,
            "external_case_id": task_record.case_id.external_case_id,
            "task_type": task_record.task_type,
            "task_owner_user_id": task_record.task_owner_user_id.login or str(task_record.task_owner_user_id.id) if task_record.task_owner_user_id else False,
            "task_owner_user_ref": task_record.task_owner_user_ref,
            "due_date": task_record.due_date.isoformat() if task_record.due_date else False,
            "task_status": task_record.task_status,
            "resolution_note": task_record.resolution_note,
            "closed_at": task_record.closed_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task_record.closed_at else False,
            "closed_by_user_id": task_record.closed_by_user_id.login or str(task_record.closed_by_user_id.id) if task_record.closed_by_user_id else False,
            "closed_by_user_ref": task_record.closed_by_user_ref,
        }

    def _clinician_payloads(self, group_xmlid, role, facilities):
        group = request.env.ref(group_xmlid)
        user_model = request.env["res.users"].sudo().with_context(active_test=False)
        users = user_model.search(
            [
                ("group_ids", "=", group.id),
                ("share", "=", False),
                ("phd_ass_facility_ids", "in", facilities.ids),
            ],
            order="name, id",
        )
        return [
            {
                "userId": user.login or str(user.id),
                "label": user.display_name or user.name or user.login,
                "role": role,
                "facilityCodes": [facility.code or facility.name for facility in user.phd_ass_facility_ids if facility in facilities],
            }
            for user in users
        ]

    def _nurse_payloads(self, facilities):
        team_model = request.env["phd.ass.care.team"].sudo().with_context(active_test=False)
        teams = team_model.search([("active", "=", True), ("facility_id", "in", facilities.ids)], order="nurse_user_id, endoscopist_user_id, id")
        by_nurse = {}
        for team in teams:
            nurse = team.nurse_user_id
            endoscopist = team.endoscopist_user_id
            if not nurse.active or nurse.share or not endoscopist.active or endoscopist.share:
                continue
            nurse_id = nurse.login or str(nurse.id)
            endoscopist_id = endoscopist.login or str(endoscopist.id)
            payload = by_nurse.setdefault(
                nurse_id,
                {
                    "userId": nurse_id,
                    "label": nurse.display_name or nurse.name or nurse.login,
                    "role": "nurse",
                    "endoscopistUserIds": [],
                    "facilityCodes": [],
                },
            )
            if endoscopist_id not in payload["endoscopistUserIds"]:
                payload["endoscopistUserIds"].append(endoscopist_id)
            facility_code = team.facility_id.code or team.facility_id.name
            if facility_code and facility_code not in payload["facilityCodes"]:
                payload["facilityCodes"].append(facility_code)

        return sorted(by_nurse.values(), key=lambda item: item["label"])

    def _referrer_service_payloads(self):
        case_model = request.env["phd.ass.case"].with_context(active_test=False)
        values = {value for value in case_model.search([("referrer_service", "!=", False)]).mapped("referrer_service") if value}
        values.update(DEFAULT_REFERRER_SERVICES)
        return [{"value": value, "label": value} for value in sorted(values)]

    def _task_write_vals(self, payload):
        vals = {}

        if "task_owner_user_id" in payload:
            owner_ref = str(payload.get("task_owner_user_id") or "").strip()
            vals["task_owner_user_ref"] = owner_ref or False
        elif "task_owner_user_ref" in payload:
            owner_ref = str(payload.get("task_owner_user_ref") or "").strip()
            vals["task_owner_user_ref"] = owner_ref or False

        if "due_date" in payload:
            due_date = str(payload.get("due_date") or "").strip()
            vals["due_date"] = due_date or False

        if "task_status" in payload:
            vals["task_status"] = payload.get("task_status") or False

        if "resolution_note" in payload:
            note = str(payload.get("resolution_note") or "").strip()
            vals["resolution_note"] = note or False

        return vals

    def _serialize_datetime(self, value):
        if not value:
            return False
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _revision_payload(self, case_record, revision):
        return {
            "revisionNumber": revision.revision_number,
            "finalizedAt": self._serialize_datetime(revision.finalized_at),
            "finalizedBy": revision.finalized_by_user_ref,
            "templateVersion": revision.template_version,
            "pdfAssetRef": revision.pdf_asset_ref,
            "reportNarrativeSnapshot": revision.report_narrative_snapshot,
        }

    def _audit_event_payload(self, event):
        payload = False
        if event.payload_json:
            try:
                payload = json.loads(event.payload_json)
            except Exception:
                payload = event.payload_json

        return {
            "id": str(event.id),
            "createdAt": self._serialize_datetime(event.create_date),
            "actorDisplayName": event.actor_user_id.display_name if event.actor_user_id else False,
            "actorRole": event.actor_role,
            "eventType": event.event_type,
            "entityType": event.entity_type or "case",
            "entityRef": event.entity_ref,
            "reason": event.reason,
            "payload": payload,
        }
