import base64
import json
import mimetypes
import textwrap
import uuid
from datetime import date, datetime, timezone
from io import BytesIO
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import quote

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


PROCEDURE_TYPE_SELECTION = [
    ("colonoscopy", "Colonoscopy"),
    ("egd", "EGD"),
    ("ercp", "ERCP"),
    ("eus", "EUS"),
]
SEX_SELECTION = [
    ("female", "Female"),
    ("male", "Male"),
    ("intersex", "Intersex"),
    ("unknown", "Unknown"),
]
CASE_STATUS_SELECTION = [
    ("draft", "Draft"),
    ("ready_for_signoff", "Ready For Sign-Off"),
    ("finalized", "Finalized"),
    ("draft_reopened", "Draft Reopened"),
]
PRIORITY_SELECTION = [("elective", "Elective"), ("urgent", "Urgent"), ("emergency", "Emergency")]
ASA_CLASS_SELECTION = [("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV"), ("V", "V")]
ANTITHROMBOTIC_PLAN_SELECTION = [
    ("na", "Not Applicable"),
    ("continue", "Continue"),
    ("hold", "Hold"),
    ("bridging_other", "Bridging Or Other"),
]
ANTIBIOTICS_STATUS_SELECTION = [("na", "Not Applicable"), ("indicated_given", "Indicated And Given")]
PREGNANCY_STATUS_SELECTION = [("na", "Not Applicable"), ("negative", "Negative"), ("positive_known", "Positive Known")]
PREP_QUALITY_SELECTION = [("adequate", "Adequate"), ("inadequate", "Inadequate")]
TERMINAL_ILEUM_STATUS_SELECTION = [
    ("not_attempted", "Not Attempted"),
    ("intubated", "Intubated"),
    ("abnormal", "Abnormal"),
]
TECHNICAL_LIMITATION_SELECTION = [
    ("none", "None"),
    ("poor_prep", "Poor Prep"),
    ("stricture", "Stricture"),
    ("pain", "Pain"),
    ("other", "Other"),
]
SMALL_POLYP_TECHNIQUE_SELECTION = [
    ("cold_snare", "Cold Snare"),
    ("hot_snare", "Hot Snare"),
    ("forceps", "Forceps"),
    ("other", "Other"),
]
TATTOO_STATUS_SELECTION = [("na", "Not Applicable"), ("placed", "Placed")]
PATHOLOGY_STATUS_SELECTION = [("none", "None"), ("pending_tracking_required", "Pending Tracking Required")]
SURVEILLANCE_INTERVAL_REASON_SELECTION = [
    ("guideline_based", "Guideline Based"),
    ("prep_quality", "Prep Quality"),
    ("piecemeal_resection", "Piecemeal Resection"),
    ("other", "Other"),
]
ADVERSE_EVENT_PLAN_SELECTION = [
    ("routine_discharge", "Routine Discharge"),
    ("observe_admit", "Observe Or Admit"),
    ("other", "Other"),
]
EGD_EXTENT_REACHED_SELECTION = [
    ("esophagus", "Esophagus"),
    ("stomach", "Stomach"),
    ("duodenal_bulb", "Duodenal Bulb"),
    ("second_duodenum", "Second Part Of Duodenum"),
    ("jejunum_other", "Jejunum Or Other"),
]
PROCEDURE_TOLERANCE_SELECTION = [("good", "Good"), ("fair", "Fair"), ("poor", "Poor")]
EGD_LA_GRADE_SELECTION = [
    ("na", "Not Applicable"),
    ("A", "LA Grade A"),
    ("B", "LA Grade B"),
    ("C", "LA Grade C"),
    ("D", "LA Grade D"),
]
FORREST_CLASSIFICATION_SELECTION = [
    ("na", "Not Applicable"),
    ("Ia", "Ia"),
    ("Ib", "Ib"),
    ("IIa", "IIa"),
    ("IIb", "IIb"),
    ("IIc", "IIc"),
    ("III", "III"),
]
THERAPY_OUTCOME_SELECTION = [("complete", "Complete"), ("partial", "Partial"), ("failed", "Failed")]
ERCP_PAPILLA_STATUS_SELECTION = [
    ("native", "Native"),
    ("prior_sphincterotomy", "Prior Sphincterotomy"),
    ("altered_anatomy", "Altered Anatomy"),
]
ERCP_ANTIBIOTIC_PROPHYLAXIS_SELECTION = [("na", "Not Applicable"), ("given_indicated", "Given / Indicated")]
ERCP_RECTAL_NSAID_SELECTION = [
    ("na_contraindicated", "Not Applicable / Contraindicated"),
    ("indomethacin", "Indomethacin"),
    ("diclofenac", "Diclofenac"),
]
ERCP_CANNULATION_TECHNIQUE_SELECTION = [("wire_guided", "Wire-Guided"), ("other", "Other")]
ERCP_PANCREATIC_DUCT_STATUS_SELECTION = [
    ("not_cannulated", "Not Cannulated"),
    ("wire_only", "Wire Only"),
    ("contrast", "Contrast"),
]
ERCP_INTRAHEPATIC_DUCTS_SELECTION = [("normal", "Normal"), ("dilated", "Dilated")]
ERCP_DRAINAGE_ACHIEVED_SELECTION = [
    ("complete", "Complete"),
    ("partial", "Partial"),
    ("not_achieved", "Not Achieved"),
]
PARTIAL_SUCCESS_SELECTION = [("yes", "Yes"), ("partial", "Partial"), ("no", "No")]
NA_PARTIAL_SUCCESS_SELECTION = [("na", "Not Applicable"), ("yes", "Yes"), ("partial", "Partial"), ("no", "No")]
ERCP_STONE_CLEARANCE_SELECTION = [
    ("na", "Not Applicable"),
    ("complete", "Complete"),
    ("incomplete_stented", "Incomplete / Stented"),
]
ERCP_BILIARY_DRAINAGE_OUTCOME_SELECTION = [
    ("na", "Not Applicable"),
    ("complete", "Complete"),
    ("partial", "Partial"),
    ("failed", "Failed"),
]
ERCP_MIGRATION_PASSAGE_CHECK_SELECTION = [("na", "Not Applicable"), ("planned", "Planned")]
EUS_ROUTE_SELECTION = [("upper", "Upper EUS"), ("lower", "Lower EUS")]
EUS_ECHOENDOSCOPE_SELECTION = [("radial", "Radial"), ("linear", "Linear"), ("miniprobe", "Miniprobe")]
EUS_INTENT_SELECTION = [
    ("diagnostic", "Diagnostic"),
    ("tissue_acquisition", "Tissue Acquisition"),
    ("therapeutic", "Therapeutic"),
]
YES_NO_LIMITED_SELECTION = [("yes", "Yes"), ("no_limited", "No / Limited")]
EUS_TISSUE_APPROACH_SELECTION = [
    ("transgastric", "Transgastric"),
    ("transduodenal", "Transduodenal"),
    ("transesophageal", "Transesophageal"),
    ("other", "Other"),
]
EUS_NEEDLE_TYPE_SELECTION = [("fna", "FNA"), ("fnb", "FNB")]
EUS_NEEDLE_GAUGE_SELECTION = [
    ("19g", "19G"),
    ("20g", "20G"),
    ("22g", "22G"),
    ("25g", "25G"),
    ("other", "Other"),
]
EUS_ROSE_STATUS_SELECTION = [("na", "Not Applicable"), ("available", "Available"), ("adequate", "Adequate")]
EUS_MOSE_STATUS_SELECTION = [("na", "Not Applicable"), ("adequate", "Adequate"), ("inadequate", "Inadequate")]
EUS_ADEQUACY_STATUS_SELECTION = [("unknown", "Unknown"), ("adequate", "Adequate"), ("inadequate", "Inadequate")]
NA_GIVEN_SELECTION = [("na", "Not Applicable"), ("given", "Given")]
NA_ADDRESSED_SELECTION = [("na", "Not Applicable"), ("addressed", "Addressed")]
TASK_TYPE_SELECTION = [
    ("pathology_review", "Pathology Review"),
    ("result_communication", "Result Communication"),
    ("specimen_resolution", "Specimen Resolution"),
    ("surveillance_followup", "Surveillance Follow-Up"),
]
TASK_STATUS_SELECTION = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("closed", "Closed"),
    ("cancelled", "Cancelled"),
]
FOLLOWUP_STATE_SELECTION = [
    ("not_required", "Not Required"),
    ("open", "Open"),
    ("closed", "Closed"),
]
SYNC_STATUS_SELECTION = [
    ("draft_local", "Local Draft"),
    ("synced", "Synced"),
    ("sync_failed", "Sync Failed"),
]
SEGMENT_NAME_SELECTION = [
    ("terminal_ileum", "Terminal Ileum"),
    ("cecum", "Cecum"),
    ("ascending_colon", "Ascending Colon"),
    ("transverse_colon", "Transverse Colon"),
    ("descending_colon", "Descending Colon"),
    ("sigmoid_colon", "Sigmoid Colon"),
    ("rectum_retroflexion", "Rectum Retroflexion"),
]
LOCAL_TEMPLATE_VERSION = "odoo-19-clinical-v1"


def _to_datetime_value(value):
    if not value:
        return False

    if isinstance(value, datetime):
        dt_value = value
    else:
        raw = str(value).strip()
        if not raw:
            return False
        normalized = raw.replace("Z", "+00:00")
        try:
            dt_value = datetime.fromisoformat(normalized)
        except ValueError:
            return False

    if dt_value.tzinfo:
        dt_value = dt_value.astimezone(timezone.utc).replace(tzinfo=None)
    return fields.Datetime.to_string(dt_value)


def _to_date_value(value):
    if not value:
        return False

    if isinstance(value, date) and not isinstance(value, datetime):
        date_value = value
    else:
        raw = str(value).strip()
        if not raw:
            return False
        if "T" in raw:
            raw = raw.split("T", 1)[0]
        try:
            date_value = date.fromisoformat(raw)
        except ValueError:
            return False
    return fields.Date.to_string(date_value)


def _to_text_json(value):
    if value in (None, "", [], {}):
        return False
    return json.dumps(value, indent=2, sort_keys=True)


def _to_api_datetime(value):
    if not value:
        return False
    if isinstance(value, str):
        return value
    naive = value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value
    return naive.strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_api_date(value):
    if not value:
        return False
    if isinstance(value, str):
        return value
    return value.isoformat()


def _display_name(patient_identifier, procedure_datetime, external_case_id):
    if patient_identifier and procedure_datetime:
        return f"{patient_identifier} - {procedure_datetime}"
    return patient_identifier or external_case_id


def _unique_match(model, domain):
    records = model.search(domain, limit=2)
    return records if len(records) == 1 else model.browse()


def _user_reference(user):
    if not user:
        return False
    return user.display_name or user.name or user.login or False


def _find_user_by_ref(env, user_ref):
    ref = str(user_ref or "").strip()
    if not ref:
        return env["res.users"].browse()

    user_model = env["res.users"].sudo().with_context(active_test=False)
    user = _unique_match(user_model, [("login", "=", ref)])
    if user:
        return user
    return _unique_match(user_model, [("name", "=", ref)])


def _find_facility_by_ref(env, facility_ref):
    ref = str(facility_ref or "").strip()
    if not ref:
        return env["phd.ass.facility"].browse()

    facility_model = env["phd.ass.facility"].sudo().with_context(active_test=False)
    facility = _unique_match(facility_model, [("name", "=", ref)])
    if facility:
        return facility
    return _unique_match(facility_model, [("code", "=", ref)])


def _find_facility_unit_by_ref(env, facility_unit_ref, facility=False):
    ref = str(facility_unit_ref or "").strip()
    if not ref:
        return env["phd.ass.facility.unit"].browse()

    unit_model = env["phd.ass.facility.unit"].sudo().with_context(active_test=False)
    base_domain = [("facility_id", "=", facility.id)] if facility else []
    for domain in (
        base_domain + [("full_name", "=", ref)],
        base_domain + [("name", "=", ref)],
        base_domain + [("code", "=", ref)],
    ):
        unit = _unique_match(unit_model, domain)
        if unit:
            return unit
    return unit_model.browse()


def _actor_role(env, user=False):
    actor = user or env.user
    if actor.has_group("phd_ass_bridge.group_phd_ass_endoscopist"):
        return "endoscopist"
    if actor.has_group("phd_ass_bridge.group_phd_ass_nurse"):
        return "nurse"
    if actor.has_group("phd_ass_bridge.group_phd_ass_operations_admin"):
        return "operations_admin"
    if actor.has_group("phd_ass_bridge.group_phd_ass_admin"):
        return "workspace_admin"
    return "user"


def _user_identifier(user):
    if not user:
        return False
    return user.login or str(user.id)


def _allowed_actor_refs(user):
    refs = {
        str(user.id) if user and user.id else False,
        user.login if user else False,
        user.name if user else False,
        user.display_name if user else False,
        _user_identifier(user),
        _user_reference(user),
    }
    return {str(ref).strip() for ref in refs if str(ref or "").strip()}


def _safe_attachment_filename(file_name, fallback="case-image"):
    cleaned = str(file_name or "").replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = cleaned.replace("\r", "").replace("\n", "").replace('"', "").strip()
    return cleaned[:255] or fallback


def _guess_image_content_type(content_type, file_name):
    normalized = str(content_type or "").split(";", 1)[0].strip().lower()
    if normalized == "image/jpg":
        normalized = "image/jpeg"
    if normalized and normalized != "application/octet-stream":
        return normalized
    guessed, _ = mimetypes.guess_type(file_name or "")
    return (guessed or "image/jpeg").lower()


def _base64_payload_size(payload):
    if not payload:
        return 0
    try:
        return len(base64.b64decode(payload, validate=False))
    except Exception:
        return 0


def _minimal_sync_excerpt(payload):
    if not isinstance(payload, dict):
        return False

    excerpt = {}
    for field_name in (
        "external_case_id",
        "case_id",
        "case_status",
        "procedure_type",
        "payload_version",
        "template_version",
        "external_task_id",
        "followup_task_id",
        "task_type",
        "task_status",
    ):
        value = payload.get(field_name)
        if value not in (None, "", [], {}):
            excerpt[field_name] = value

    if "segment_exam" in payload or "segments" in payload:
        excerpt["segment_count"] = len(payload.get("segment_exam") or payload.get("segments") or [])
    if "lesions" in payload:
        excerpt["lesion_count"] = len(payload.get("lesions") or [])
    if "specimens" in payload:
        excerpt["specimen_count"] = len(payload.get("specimens") or [])
    if "image_attachments" in payload:
        excerpt["image_attachment_count"] = len(payload.get("image_attachments") or [])
    if "followup_tasks" in payload or "tasks" in payload:
        excerpt["followup_task_count"] = len(payload.get("followup_tasks") or payload.get("tasks") or [])

    return excerpt or False


def _to_audit_value(value):
    if isinstance(value, models.BaseModel):
        if not value:
            return False
        if len(value) == 1:
            return value.display_name
        return value.mapped("display_name")
    if isinstance(value, datetime):
        return _to_api_datetime(value)
    if isinstance(value, date):
        return _to_api_date(value)
    if isinstance(value, dict):
        return {key: _to_audit_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_audit_value(item) for item in value]
    return value


class PhdAssResUsers(models.Model):
    _inherit = "res.users"

    phd_ass_facility_ids = fields.Many2many(
        "phd.ass.facility",
        "phd_ass_user_facility_rel",
        "user_id",
        "facility_id",
        string="Endoscopy Facilities",
        help="Facilities this user can access in the endoscopy workspace.",
    )


class PhdAssFacility(models.Model):
    _name = "phd.ass.facility"
    _description = "PhD-Ass Facility"
    _order = "name, id"

    name = fields.Char(required=True)
    code = fields.Char()
    active = fields.Boolean(default=True)
    unit_ids = fields.One2many("phd.ass.facility.unit", "facility_id", string="Units")

    _name_unique = models.Constraint(
        "unique(name)",
        "Facility name must be unique.",
    )
    _code_unique = models.Constraint(
        "unique(code)",
        "Facility code must be unique.",
    )


class PhdAssFacilityUnit(models.Model):
    _name = "phd.ass.facility.unit"
    _description = "PhD-Ass Facility Unit"
    _order = "facility_id, name, id"
    _rec_name = "full_name"

    name = fields.Char(required=True)
    code = fields.Char()
    facility_id = fields.Many2one("phd.ass.facility", required=True, ondelete="cascade", index=True)
    full_name = fields.Char(compute="_compute_full_name", store=True)
    active = fields.Boolean(default=True)

    _facility_name_unique = models.Constraint(
        "unique(facility_id, name)",
        "Unit name must be unique within a facility.",
    )
    _facility_code_unique = models.Constraint(
        "unique(facility_id, code)",
        "Unit code must be unique within a facility.",
    )

    @api.depends("facility_id.name", "name")
    def _compute_full_name(self):
        for record in self:
            record.full_name = f"{record.facility_id.name} / {record.name}" if record.facility_id and record.name else record.name


class PhdAssCareTeam(models.Model):
    _name = "phd.ass.care.team"
    _description = "PhD-Ass Endoscopist Nurse Team"
    _order = "facility_id, endoscopist_user_id, nurse_user_id, id"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True)
    active = fields.Boolean(default=True)
    facility_id = fields.Many2one("phd.ass.facility", required=True, ondelete="cascade", index=True)
    endoscopist_user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True, domain=[("share", "=", False)])
    nurse_user_id = fields.Many2one("res.users", required=True, ondelete="cascade", index=True, domain=[("share", "=", False)])
    note = fields.Char()

    _team_unique = models.Constraint(
        "unique(facility_id, endoscopist_user_id, nurse_user_id)",
        "This nurse is already assigned to the selected endoscopist for this facility.",
    )

    @api.depends("facility_id.name", "endoscopist_user_id.display_name", "nurse_user_id.display_name")
    def _compute_name(self):
        for record in self:
            facility = record.facility_id.name or "Facility"
            endoscopist = record.endoscopist_user_id.display_name or "Endoscopist"
            nurse = record.nurse_user_id.display_name or "Nurse"
            record.name = f"{facility} / {endoscopist} / {nurse}"

    @api.constrains("facility_id", "endoscopist_user_id", "nurse_user_id")
    def _check_role_groups(self):
        endoscopist_group = self.env.ref("phd_ass_bridge.group_phd_ass_endoscopist", raise_if_not_found=False)
        nurse_group = self.env.ref("phd_ass_bridge.group_phd_ass_nurse", raise_if_not_found=False)
        for record in self:
            if endoscopist_group and endoscopist_group not in record.endoscopist_user_id.group_ids:
                raise ValidationError("Care team endoscopist must belong to the Endoscopist workspace role.")
            if nurse_group and nurse_group not in record.nurse_user_id.group_ids:
                raise ValidationError("Care team nurse must belong to the Nurse workspace role.")
            if record.endoscopist_user_id == record.nurse_user_id:
                raise ValidationError("Care team endoscopist and nurse must be different users.")
            if record.facility_id and record.facility_id not in record.endoscopist_user_id.phd_ass_facility_ids:
                raise ValidationError("Care team endoscopist must have access to the selected facility.")
            if record.facility_id and record.facility_id not in record.nurse_user_id.phd_ass_facility_ids:
                raise ValidationError("Care team nurse must have access to the selected facility.")


class PhdAssCase(models.Model):
    _name = "phd.ass.case"
    _description = "PhD-Ass Clinical Case"
    _order = "procedure_datetime desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True)
    external_case_id = fields.Char(required=True, default=lambda self: str(uuid.uuid4()), index=True, copy=False)
    case_status = fields.Selection(CASE_STATUS_SELECTION, default="draft", index=True)
    procedure_type = fields.Selection(PROCEDURE_TYPE_SELECTION, default="colonoscopy", required=True, index=True)
    patient_identifier = fields.Char(required=True, index=True)
    procedure_datetime = fields.Datetime(required=True, index=True)
    dob_or_age = fields.Char()
    sex = fields.Selection(SEX_SELECTION, required=True)
    facility_id = fields.Many2one("phd.ass.facility", string="Facility")
    facility_unit_id = fields.Many2one("phd.ass.facility.unit", string="Unit")
    facility_unit = fields.Char()
    endoscopist_user_id = fields.Many2one("res.users", string="Endoscopist", domain=[("share", "=", False)])
    endoscopist_user_ref = fields.Char(required=True)
    available_nurse_user_ids = fields.Many2many("res.users", compute="_compute_available_nurse_user_ids", string="Available Nurses")
    assistant_nurse_user_id = fields.Many2one("res.users", string="Assistant or Nurse", domain="[('id', 'in', available_nurse_user_ids)]")
    assistant_nurse_user_ref = fields.Char()
    referrer_service = fields.Char()

    indication = fields.Text()
    priority = fields.Selection(PRIORITY_SELECTION)
    relevant_history = fields.Text()
    asa_class = fields.Selection(ASA_CLASS_SELECTION)
    allergies = fields.Text()
    antithrombotic_plan = fields.Selection(ANTITHROMBOTIC_PLAN_SELECTION)
    consent_documented = fields.Boolean()
    patient_identity_verified = fields.Boolean(string="Two patient identifiers verified")
    team_pause_completed = fields.Boolean()
    sedation_anesthesia = fields.Char()
    monitor_spo2 = fields.Boolean()
    monitor_hr = fields.Boolean()
    monitor_bp = fields.Boolean()
    monitor_ecg = fields.Boolean()
    monitor_capnography = fields.Boolean()
    antibiotics_status = fields.Selection(ANTIBIOTICS_STATUS_SELECTION)
    pregnancy_status = fields.Selection(PREGNANCY_STATUS_SELECTION)

    bowel_prep_agent = fields.Char()
    prep_quality = fields.Selection(PREP_QUALITY_SELECTION)
    bbps_right = fields.Integer()
    bbps_transverse = fields.Integer()
    bbps_left = fields.Integer()
    bbps_total = fields.Integer(compute="_compute_bbps_total", store=True, readonly=True)
    insertion_time = fields.Char()
    cecum_reached = fields.Boolean()
    cecal_landmark_appendiceal_orifice = fields.Boolean()
    cecal_landmark_ileocecal_valve = fields.Boolean()
    photo_cecum = fields.Boolean()
    photo_pathology = fields.Boolean()
    terminal_ileum_status = fields.Selection(TERMINAL_ILEUM_STATUS_SELECTION)
    withdrawal_time_minutes = fields.Integer()
    technical_limitation = fields.Selection(TECHNICAL_LIMITATION_SELECTION)
    technical_limitation_note = fields.Text()
    adverse_event_during_procedure = fields.Boolean()
    adverse_event_note = fields.Text()

    uc_mayo_score = fields.Selection([("0", "0"), ("1", "1"), ("2", "2"), ("3", "3")])
    crohn_score = fields.Char()
    disease_extent = fields.Text()

    small_polyp_technique = fields.Selection(SMALL_POLYP_TECHNIQUE_SELECTION)
    small_polyp_technique_note = fields.Text()
    advanced_resection_type = fields.Char()
    tattoo_status = fields.Selection(TATTOO_STATUS_SELECTION)
    tattoo_location_note = fields.Text()
    hemostasis_or_closure = fields.Char()
    impression = fields.Text()
    pathology_status = fields.Selection(PATHOLOGY_STATUS_SELECTION)
    surveillance_interval_value = fields.Char()
    surveillance_interval_pending_pathology = fields.Boolean()
    surveillance_interval_reason = fields.Selection(SURVEILLANCE_INTERVAL_REASON_SELECTION)
    surveillance_interval_reason_note = fields.Text()
    adverse_event_plan = fields.Selection(ADVERSE_EVENT_PLAN_SELECTION)
    adverse_event_plan_note = fields.Text()
    informed_patient = fields.Boolean()
    informed_referrer = fields.Boolean()
    written_instructions_given = fields.Boolean()

    egd_scope_id = fields.Char()
    egd_extent_reached = fields.Selection(EGD_EXTENT_REACHED_SELECTION)
    egd_start_time = fields.Char()
    egd_end_time = fields.Char()
    egd_preparation_status = fields.Selection(PREP_QUALITY_SELECTION)
    egd_tolerance = fields.Selection(PROCEDURE_TOLERANCE_SELECTION)
    egd_photo_landmarks = fields.Boolean()
    egd_specimens_obtained = fields.Boolean()
    egd_exam_esophagus_normal = fields.Boolean()
    egd_exam_esophagus_note = fields.Text()
    egd_exam_esophagus_photo = fields.Boolean()
    egd_exam_z_line_normal = fields.Boolean()
    egd_exam_z_line_note = fields.Text()
    egd_exam_z_line_photo = fields.Boolean()
    egd_exam_cardia_fundus_normal = fields.Boolean()
    egd_exam_cardia_fundus_note = fields.Text()
    egd_exam_cardia_fundus_photo = fields.Boolean()
    egd_exam_gastric_body_normal = fields.Boolean()
    egd_exam_gastric_body_note = fields.Text()
    egd_exam_gastric_body_photo = fields.Boolean()
    egd_exam_incisura_antrum_normal = fields.Boolean()
    egd_exam_incisura_antrum_note = fields.Text()
    egd_exam_incisura_antrum_photo = fields.Boolean()
    egd_exam_pylorus_normal = fields.Boolean()
    egd_exam_pylorus_note = fields.Text()
    egd_exam_pylorus_photo = fields.Boolean()
    egd_exam_duodenal_bulb_normal = fields.Boolean()
    egd_exam_duodenal_bulb_note = fields.Text()
    egd_exam_duodenal_bulb_photo = fields.Boolean()
    egd_exam_second_duodenum_normal = fields.Boolean()
    egd_exam_second_duodenum_note = fields.Text()
    egd_exam_second_duodenum_photo = fields.Boolean()
    egd_erosive_esophagitis_la_grade = fields.Selection(EGD_LA_GRADE_SELECTION)
    egd_barrett_circumference_cm = fields.Char()
    egd_barrett_maximal_cm = fields.Char()
    egd_barrett_visible_lesion = fields.Boolean()
    egd_erefs_edema = fields.Char()
    egd_erefs_rings = fields.Char()
    egd_erefs_exudates = fields.Char()
    egd_erefs_furrows = fields.Char()
    egd_erefs_stricture = fields.Char()
    egd_forrest_classification = fields.Selection(FORREST_CLASSIFICATION_SELECTION)
    egd_standardized_score_name = fields.Char()
    egd_standardized_score_value = fields.Char()
    egd_esophagus_finding = fields.Text()
    egd_stomach_finding = fields.Text()
    egd_duodenum_finding = fields.Text()
    egd_hiatal_hernia = fields.Boolean()
    egd_retroflexion_performed = fields.Boolean()
    egd_biopsy_taken = fields.Boolean()
    egd_therapy_performed = fields.Char()
    egd_hemostasis_method = fields.Char()
    egd_dilation_type = fields.Char()
    egd_dilation_diameter_mm = fields.Integer()
    egd_variceal_other_therapy = fields.Char()
    egd_therapy_outcome = fields.Selection(THERAPY_OUTCOME_SELECTION)
    egd_outcome_details = fields.Text()
    egd_impression = fields.Text()
    egd_h_pylori_plan = fields.Char()
    egd_medication_therapy = fields.Text()
    egd_followup_surveillance = fields.Text()
    egd_result_communication_planned = fields.Boolean()
    egd_referrer_communication_planned = fields.Boolean()

    ercp_indication = fields.Text()
    ercp_papilla_status = fields.Selection(ERCP_PAPILLA_STATUS_SELECTION)
    ercp_papilla_appearance = fields.Char()
    ercp_therapeutic_intent = fields.Text()
    ercp_imaging_reviewed = fields.Text()
    ercp_antibiotic_prophylaxis = fields.Selection(ERCP_ANTIBIOTIC_PROPHYLAXIS_SELECTION)
    ercp_rectal_nsaid = fields.Selection(ERCP_RECTAL_NSAID_SELECTION)
    ercp_hydration_plan = fields.Text()
    ercp_pancreatic_stent_plan = fields.Text()
    ercp_rescue_plan = fields.Char()
    ercp_radiation_protection_verified = fields.Boolean()
    ercp_pregnancy_precautions = fields.Selection(NA_ADDRESSED_SELECTION)
    ercp_cannulation_success = fields.Boolean()
    ercp_cannulation_technique = fields.Selection(ERCP_CANNULATION_TECHNIQUE_SELECTION)
    ercp_cannulation_contacts = fields.Integer()
    ercp_cannulation_time_minutes = fields.Integer()
    ercp_unintended_pd_access_count = fields.Integer()
    ercp_pancreatic_duct_status = fields.Selection(ERCP_PANCREATIC_DUCT_STATUS_SELECTION)
    ercp_prophylactic_pd_stent = fields.Boolean()
    ercp_prophylactic_pd_stent_details = fields.Char()
    ercp_cholangiogram_cbd_mm = fields.Integer()
    ercp_intrahepatic_ducts = fields.Selection(ERCP_INTRAHEPATIC_DUCTS_SELECTION)
    ercp_stone_count = fields.Integer()
    ercp_largest_stone_mm = fields.Integer()
    ercp_stricture_site = fields.Char()
    ercp_leak_note = fields.Text()
    ercp_anatomy_other_findings = fields.Text()
    ercp_drainage_achieved = fields.Selection(ERCP_DRAINAGE_ACHIEVED_SELECTION)
    ercp_ducts_accessed = fields.Char()
    ercp_sphincterotomy_performed = fields.Boolean()
    ercp_sphincterotomy_type = fields.Char()
    ercp_sphincterotomy_details = fields.Text()
    ercp_papillary_dilation_balloon_mm = fields.Integer()
    ercp_stone_extraction_performed = fields.Boolean()
    ercp_stone_therapy = fields.Text()
    ercp_stricture_therapy = fields.Text()
    ercp_stent_placed = fields.Boolean()
    ercp_biliary_stent_type = fields.Char()
    ercp_stent_details = fields.Text()
    ercp_other_intervention = fields.Text()
    ercp_fluoroscopy_time_minutes = fields.Integer()
    ercp_dose_area_product = fields.Char()
    ercp_reference_air_kerma = fields.Char()
    ercp_images_acquired = fields.Integer()
    ercp_dose_reduction_measures = fields.Text()
    ercp_dose_reduction_other = fields.Text()
    ercp_intended_therapy = fields.Text()
    ercp_technical_success = fields.Selection(PARTIAL_SUCCESS_SELECTION)
    ercp_stone_clearance = fields.Selection(ERCP_STONE_CLEARANCE_SELECTION)
    ercp_biliary_drainage_outcome = fields.Selection(ERCP_BILIARY_DRAINAGE_OUTCOME_SELECTION)
    ercp_immediate_adverse_event = fields.Char()
    ercp_temporary_stent = fields.Boolean()
    ercp_removal_exchange_due = fields.Date()
    ercp_pd_stent = fields.Boolean()
    ercp_migration_passage_check = fields.Selection(ERCP_MIGRATION_PASSAGE_CHECK_SELECTION)
    ercp_patient_contact_note = fields.Text()
    ercp_tracking_register_entered = fields.Boolean()
    ercp_repeat_intervention = fields.Char()
    ercp_repeat_intervention_timing = fields.Char()
    ercp_post_ercp_pancreatitis = fields.Text()
    ercp_significant_bleeding = fields.Text()
    ercp_cholangitis_or_cholecystitis = fields.Text()
    ercp_unplanned_hospital_visit = fields.Text()
    ercp_complication_note = fields.Text()
    ercp_impression = fields.Text()

    eus_route = fields.Selection(EUS_ROUTE_SELECTION)
    eus_echoendoscope = fields.Selection(EUS_ECHOENDOSCOPE_SELECTION)
    eus_intent = fields.Selection(EUS_INTENT_SELECTION)
    eus_upper_esophagus = fields.Boolean()
    eus_upper_stomach = fields.Boolean()
    eus_upper_duodenum = fields.Boolean()
    eus_pancreas_examined = fields.Boolean()
    eus_cbd_examined = fields.Boolean()
    eus_gallbladder_examined = fields.Boolean()
    eus_liver_examined = fields.Boolean()
    eus_adrenal_examined = fields.Boolean()
    eus_mediastinum_examined = fields.Boolean()
    eus_nodes_examined = fields.Boolean()
    eus_doppler_used = fields.Boolean()
    eus_relevant_anatomy_documented = fields.Selection(YES_NO_LIMITED_SELECTION)
    eus_photo_anatomy = fields.Boolean()
    eus_technical_limitation = fields.Char()
    eus_immediate_adverse_event_note = fields.Text()
    eus_regions_examined = fields.Text()
    eus_target_lesion_present = fields.Boolean()
    eus_target_location = fields.Char()
    eus_target_size_mm = fields.Integer()
    eus_echogenicity = fields.Char()
    eus_margins = fields.Char()
    eus_vascular_relation = fields.Char()
    eus_nodes_note = fields.Text()
    eus_image_reference = fields.Char()
    eus_cancer_site = fields.Char()
    eus_staging_system = fields.Char()
    eus_t_stage = fields.Char()
    eus_n_stage = fields.Char()
    eus_m_features = fields.Char()
    eus_vascular_invasion = fields.Char()
    eus_overall_stage = fields.Char()
    eus_management_implication = fields.Text()
    eus_tissue_target = fields.Char()
    eus_approach = fields.Selection(EUS_TISSUE_APPROACH_SELECTION)
    eus_needle_type = fields.Selection(EUS_NEEDLE_TYPE_SELECTION)
    eus_needle_gauge = fields.Selection(EUS_NEEDLE_GAUGE_SELECTION)
    eus_needle_design = fields.Char()
    eus_fna_performed = fields.Boolean()
    eus_fnb_performed = fields.Boolean()
    eus_passes_count = fields.Integer()
    eus_rose_status = fields.Selection(EUS_ROSE_STATUS_SELECTION)
    eus_mose_status = fields.Selection(EUS_MOSE_STATUS_SELECTION)
    eus_specimen_type = fields.Text()
    eus_container_labels = fields.Text()
    eus_adequacy_status = fields.Selection(EUS_ADEQUACY_STATUS_SELECTION)
    eus_adequacy_note = fields.Text()
    eus_label_verified = fields.Boolean()
    eus_complication_type = fields.Char()
    eus_antibiotics_after_sampling = fields.Selection(NA_GIVEN_SELECTION)
    eus_intervention_procedure = fields.Char()
    eus_intervention_target_route = fields.Char()
    eus_device_stent = fields.Char()
    eus_technical_success = fields.Selection(NA_PARTIAL_SUCCESS_SELECTION)
    eus_clinical_plan = fields.Text()
    eus_immediate_adverse_event = fields.Char()
    eus_impression = fields.Text()
    eus_pathology_cytology_status = fields.Char()
    eus_followup_imaging_or_procedure = fields.Text()
    eus_multidisciplinary_referral = fields.Char()

    requires_followup = fields.Boolean(compute="_compute_followup_state", store=True, readonly=True)
    followup_state = fields.Selection(FOLLOWUP_STATE_SELECTION, compute="_compute_followup_state", store=True, readonly=True)
    finalized_at = fields.Datetime(readonly=True)
    finalized_by_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    finalized_by_user_ref = fields.Char(readonly=True)
    template_version = fields.Char(readonly=True)
    report_narrative_snapshot = fields.Text(readonly=True)
    pdf_attachment_id = fields.Many2one("ir.attachment", readonly=True, ondelete="set null")
    pdf_asset_ref = fields.Char(readonly=True)
    validation_summary = fields.Text(readonly=True)
    reopen_reason = fields.Text(readonly=True)
    reopened_at = fields.Datetime(readonly=True)
    reopened_by_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    reopened_by_user_ref = fields.Char(readonly=True)

    payload_version = fields.Char(readonly=True)
    last_synced_at = fields.Datetime(readonly=True)
    last_push_to_api_at = fields.Datetime(readonly=True)
    sync_status = fields.Selection(SYNC_STATUS_SELECTION, default="draft_local", readonly=True, index=True)
    last_sync_error = fields.Text(readonly=True)
    clinical_payload_json = fields.Text(readonly=True)

    segment_ids = fields.One2many("phd.ass.case.segment", "case_id", string="Segments")
    lesion_ids = fields.One2many("phd.ass.case.lesion", "case_id", string="Lesions")
    specimen_ids = fields.One2many("phd.ass.case.specimen", "case_id", string="Specimens")
    image_attachment_ids = fields.One2many("phd.ass.case.image", "case_id", string="Case Images")
    task_ids = fields.One2many("phd.ass.followup.task", "case_id", string="Follow-Up Tasks")
    sync_event_ids = fields.One2many("phd.ass.sync.event", "case_id", string="Sync Events", readonly=True)
    audit_event_ids = fields.One2many("phd.ass.audit.event", "case_id", string="Audit Events", readonly=True)
    revision_ids = fields.One2many("phd.ass.case.revision", "case_id", string="Finalized Revisions", readonly=True)

    _external_case_id_unique = models.Constraint(
        "unique(external_case_id)",
        "Clinical case ID must be unique.",
    )

    @api.depends("patient_identifier", "procedure_datetime", "external_case_id")
    def _compute_name(self):
        for record in self:
            record.name = _display_name(
                record.patient_identifier,
                _to_api_datetime(record.procedure_datetime),
                record.external_case_id,
            )

    @api.depends("bbps_right", "bbps_transverse", "bbps_left")
    def _compute_bbps_total(self):
        for record in self:
            record.bbps_total = (record.bbps_right or 0) + (record.bbps_transverse or 0) + (record.bbps_left or 0)

    @api.depends("facility_id", "endoscopist_user_id")
    def _compute_available_nurse_user_ids(self):
        team_model = self.env["phd.ass.care.team"].sudo().with_context(active_test=False)
        empty_users = self.env["res.users"].browse()
        for record in self:
            if not record.facility_id or not record.endoscopist_user_id:
                record.available_nurse_user_ids = empty_users
                continue
            teams = team_model.search(
                [
                    ("active", "=", True),
                    ("facility_id", "=", record.facility_id.id),
                    ("endoscopist_user_id", "=", record.endoscopist_user_id.id),
                ]
            )
            record.available_nurse_user_ids = teams.mapped("nurse_user_id")

    @api.depends(
        "case_status",
        "pathology_status",
        "surveillance_interval_pending_pathology",
        "specimen_ids",
        "task_ids.task_status",
        "egd_specimens_obtained",
        "eus_fna_performed",
        "eus_fnb_performed",
    )
    def _compute_followup_state(self):
        for record in self:
            requires = bool(record.specimen_ids)
            requires = requires or record.pathology_status == "pending_tracking_required"
            requires = requires or bool(record.surveillance_interval_pending_pathology)
            requires = requires or bool(record.egd_specimens_obtained)
            requires = requires or bool(record.eus_fna_performed) or bool(record.eus_fnb_performed)
            record.requires_followup = requires
            if not requires:
                record.followup_state = "not_required"
            elif not record.task_ids or any(task.task_status in {"open", "in_progress"} for task in record.task_ids):
                record.followup_state = "open"
            else:
                record.followup_state = "closed"

    def _prepare_audit_field_values(self, field_names):
        self.ensure_one()
        return {field_name: _to_audit_value(self[field_name]) for field_name in field_names if field_name in self._fields}

    def _procedure_impression_value(self):
        self.ensure_one()
        if self.procedure_type == "egd":
            return self.egd_impression
        if self.procedure_type == "ercp":
            return self.ercp_impression
        if self.procedure_type == "eus":
            return self.eus_impression
        return self.impression

    def _communication_plan_present(self):
        self.ensure_one()
        if self.procedure_type == "egd":
            return any(
                [
                    self.egd_followup_surveillance,
                    self.egd_h_pylori_plan,
                    self.egd_medication_therapy,
                    self.egd_result_communication_planned,
                    self.egd_referrer_communication_planned,
                ]
            )
        if self.procedure_type == "ercp":
            return any(
                [
                    self.ercp_repeat_intervention,
                    self.ercp_repeat_intervention_timing,
                    self.ercp_patient_contact_note,
                    self.ercp_tracking_register_entered,
                    self.ercp_temporary_stent,
                ]
            )
        if self.procedure_type == "eus":
            return any(
                [
                    self.eus_clinical_plan,
                    self.eus_followup_imaging_or_procedure,
                    self.eus_multidisciplinary_referral,
                    self.informed_patient,
                    self.informed_referrer,
                ]
            )
        return any(
            [
                self.adverse_event_plan,
                self.surveillance_interval_value,
                self.informed_patient,
                self.informed_referrer,
                self.written_instructions_given,
            ]
        )

    def _egd_exam_documented(self):
        self.ensure_one()
        return any(
            [
                self.egd_esophagus_finding,
                self.egd_stomach_finding,
                self.egd_duodenum_finding,
                self.egd_exam_esophagus_note,
                self.egd_exam_z_line_note,
                self.egd_exam_cardia_fundus_note,
                self.egd_exam_gastric_body_note,
                self.egd_exam_incisura_antrum_note,
                self.egd_exam_pylorus_note,
                self.egd_exam_duodenal_bulb_note,
                self.egd_exam_second_duodenum_note,
            ]
        )

    def _signoff_validation_errors(self):
        self.ensure_one()
        errors = []

        if not self.patient_identifier:
            errors.append("Patient identifier is required.")
        if not self.procedure_datetime:
            errors.append("Procedure date and time are required.")
        if not (self.endoscopist_user_id or self.endoscopist_user_ref):
            errors.append("An endoscopist must be assigned.")
        if not self.indication:
            errors.append("Indication is required.")
        if not self.consent_documented:
            errors.append("Consent must be documented before sign-off.")
        if not self.patient_identity_verified:
            errors.append("Two patient identifiers must be verified before sign-off.")
        if not self.team_pause_completed:
            errors.append("Team pause must be completed before sign-off.")
        if not self.sedation_anesthesia:
            errors.append("Sedation or anesthesia status is required.")
        if not self._procedure_impression_value():
            errors.append("A procedure impression is required.")
        if not self._communication_plan_present():
            errors.append("A communication or follow-up plan is required.")
        if self.requires_followup and not self.task_ids:
            errors.append("At least one follow-up task is required for cases with specimens or pending pathology.")

        if self.procedure_type == "colonoscopy":
            if not self.prep_quality:
                errors.append("Bowel prep quality is required for colonoscopy sign-off.")
            if any(not value for value in (self.bbps_right, self.bbps_transverse, self.bbps_left)):
                errors.append("Record BBPS for the right, transverse, and left colon before sign-off.")
            if not self.cecum_reached and not self.technical_limitation_note:
                errors.append("Record cecal completion or document why the cecum was not reached.")
            if self.cecum_reached:
                if not self.cecal_landmark_appendiceal_orifice or not self.cecal_landmark_ileocecal_valve:
                    errors.append("Document both cecal landmarks when the cecum is reached.")
                if not self.photo_cecum:
                    errors.append("Capture cecal photodocumentation when the cecum is reached.")
            if not self.segment_ids:
                errors.append("At least one segment examination row is required.")

        if self.adverse_event_during_procedure and not self.adverse_event_note:
            errors.append("Document the adverse event, response, and escalation plan.")
        elif self.procedure_type == "egd":
            if not self.egd_extent_reached:
                errors.append("Extent reached is required for EGD sign-off.")
            if not self._egd_exam_documented():
                errors.append("Document the key EGD examination findings before sign-off.")
            if self.egd_specimens_obtained and not self.specimen_ids:
                errors.append("Add specimen records for an EGD with specimens obtained.")
        elif self.procedure_type == "ercp":
            if not self.ercp_papilla_status:
                errors.append("Papilla status is required for ERCP sign-off.")
            if not self.ercp_technical_success:
                errors.append("Technical success is required for ERCP sign-off.")
            if not self.ercp_drainage_achieved:
                errors.append("Drainage outcome is required for ERCP sign-off.")
            if not self.ercp_radiation_protection_verified:
                errors.append("Radiation protection verification is required for ERCP sign-off.")
        elif self.procedure_type == "eus":
            if not self.eus_route:
                errors.append("EUS route is required for sign-off.")
            if not self.eus_echoendoscope:
                errors.append("Echoendoscope type is required for EUS sign-off.")
            if not self.eus_intent:
                errors.append("EUS intent is required for sign-off.")
            if not self.eus_relevant_anatomy_documented:
                errors.append("Relevant anatomy documentation status is required for EUS sign-off.")
            if (self.eus_fna_performed or self.eus_fnb_performed) and not self.eus_passes_count:
                errors.append("Document pass count for EUS tissue acquisition before sign-off.")
            if (self.eus_fna_performed or self.eus_fnb_performed) and not self.eus_adequacy_status:
                errors.append("Adequacy status is required when EUS tissue acquisition is performed.")

        return errors

    def _validation_summary_text(self, errors):
        if not errors:
            return "Ready for sign-off."
        bullet_lines = [f"- {message}" for message in errors]
        return "\n".join(["Sign-off blocked until these issues are resolved:"] + bullet_lines)

    def _narrative_lines(self):
        self.ensure_one()
        procedure_label = dict(PROCEDURE_TYPE_SELECTION).get(self.procedure_type, self.procedure_type)
        lines = [
            f"{procedure_label} Report",
            f"Patient: {self.patient_identifier}",
            f"Procedure Date/Time: {_to_api_datetime(self.procedure_datetime)}",
            f"Facility: {self.facility_unit or self.facility_id.name or 'Not recorded'}",
            f"Endoscopist: {self.endoscopist_user_ref or self.endoscopist_user_id.display_name or 'Not recorded'}",
            f"Assistant/Nurse: {self.assistant_nurse_user_ref or self.assistant_nurse_user_id.display_name or 'Not recorded'}",
            f"Indication: {self.indication or 'Not recorded'}",
            f"Relevant History: {self.relevant_history or 'Not recorded'}",
            f"Sedation/Anesthesia: {self.sedation_anesthesia or 'Not recorded'}",
        ]

        if self.procedure_type == "colonoscopy":
            cecum_text = "Reached" if self.cecum_reached else f"Not reached ({self.technical_limitation_note or 'reason not documented'})"
            lines.extend(
                [
                    f"Prep Quality: {self.prep_quality or 'Not recorded'}",
                    f"BBPS: {self.bbps_total or 0} (R {self.bbps_right or 0}, T {self.bbps_transverse or 0}, L {self.bbps_left or 0})",
                    f"Cecum: {cecum_text}",
                    f"Segments Examined: {len(self.segment_ids)}",
                    f"Lesions Recorded: {len(self.lesion_ids)}",
                    f"Impression: {self.impression or 'Not recorded'}",
                    "Follow-Up Plan: "
                    + (
                        self.adverse_event_plan
                        or self.surveillance_interval_value
                        or ("Pending pathology" if self.surveillance_interval_pending_pathology else False)
                        or "Not recorded"
                    ),
                ]
            )
        elif self.procedure_type == "egd":
            lines.extend(
                [
                    f"Extent Reached: {self.egd_extent_reached or 'Not recorded'}",
                    f"Specimens Obtained: {'Yes' if self.egd_specimens_obtained else 'No'}",
                    f"Impression: {self.egd_impression or 'Not recorded'}",
                    "Follow-Up Plan: " + (self.egd_followup_surveillance or self.egd_h_pylori_plan or "Not recorded"),
                ]
            )
        elif self.procedure_type == "ercp":
            lines.extend(
                [
                    f"Papilla Status: {self.ercp_papilla_status or 'Not recorded'}",
                    f"Drainage Achieved: {self.ercp_drainage_achieved or 'Not recorded'}",
                    f"Technical Success: {self.ercp_technical_success or 'Not recorded'}",
                    f"Impression: {self.ercp_impression or 'Not recorded'}",
                    "Follow-Up Plan: " + (self.ercp_repeat_intervention or self.ercp_patient_contact_note or "Not recorded"),
                ]
            )
        else:
            lines.extend(
                [
                    f"Intent: {self.eus_intent or 'Not recorded'}",
                    f"Tissue Acquisition: {'Yes' if (self.eus_fna_performed or self.eus_fnb_performed) else 'No'}",
                    f"Target Lesion: {self.eus_target_location or 'Not recorded'}",
                    f"Impression: {self.eus_impression or 'Not recorded'}",
                    "Follow-Up Plan: " + (self.eus_clinical_plan or self.eus_followup_imaging_or_procedure or "Not recorded"),
                ]
            )

        if self.task_ids:
            lines.append("Follow-Up Tasks:")
            for task in self.task_ids.sorted("id"):
                owner = task.task_owner_user_ref or task.task_owner_user_id.display_name or "Unassigned"
                lines.append(f"- {task.name}: {task.task_status} (Owner: {owner})")

        return [line for line in lines if line]

    def _generate_narrative_snapshot(self):
        self.ensure_one()
        return "\n".join(self._narrative_lines())

    def _render_pdf_bytes(self, narrative):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y_position = height - 48
        pdf.setFont("Helvetica-Bold", 14)
        for index, line in enumerate(narrative.splitlines() or [self.name]):
            wrapped_lines = textwrap.wrap(line, width=95) or [""]
            for wrapped in wrapped_lines:
                if y_position < 48:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 11)
                    y_position = height - 48
                if index == 0 and y_position == height - 48:
                    pdf.drawString(40, y_position, wrapped)
                    pdf.setFont("Helvetica", 11)
                else:
                    pdf.drawString(40, y_position, wrapped)
                y_position -= 16
        pdf.save()
        return buffer.getvalue()

    def _create_pdf_attachment(self, narrative):
        self.ensure_one()
        pdf_bytes = self._render_pdf_bytes(narrative)
        attachment = self.env["ir.attachment"].sudo().create(
            {
                "name": f"{self.external_case_id}-final-report.pdf",
                "res_model": "phd.ass.case",
                "res_id": self.id,
                "type": "binary",
                "mimetype": "application/pdf",
                "datas": base64.b64encode(pdf_bytes).decode("ascii"),
            }
        )
        return attachment

    def _finalized_snapshot_payload(self):
        self.ensure_one()
        payload = self._serialize_for_clinical_api()
        payload.update(
            {
                "followup_state": self.followup_state,
                "requires_followup": self.requires_followup,
                "finalized_at": _to_api_datetime(self.finalized_at),
                "finalized_by_user_id": _user_identifier(self.finalized_by_user_id),
                "finalized_by_user_ref": self.finalized_by_user_ref,
                "template_version": self.template_version,
                "pdf_asset_ref": self.pdf_asset_ref,
            }
        )
        return payload

    def _create_final_revision(self):
        self.ensure_one()
        revision_model = self.env["phd.ass.case.revision"].sudo()
        existing_revisions = revision_model.search([("case_id", "=", self.id)])
        next_revision = (max(existing_revisions.mapped("revision_number")) if existing_revisions else 0) + 1
        return revision_model.create(
            {
                "case_id": self.id,
                "revision_number": next_revision,
                "finalized_at": self.finalized_at,
                "finalized_by_user_id": self.finalized_by_user_id.id,
                "finalized_by_user_ref": self.finalized_by_user_ref,
                "template_version": self.template_version,
                "report_narrative_snapshot": self.report_narrative_snapshot,
                "pdf_attachment_id": self.pdf_attachment_id.id,
                "pdf_asset_ref": self.pdf_asset_ref,
                "snapshot_json": _to_text_json(self._finalized_snapshot_payload()),
            }
        )

    def _log_audit_event(self, event_type, entity_type="case", entity_ref=False, reason=False, payload=False):
        self.ensure_one()
        self.env["phd.ass.audit.event"].sudo().create(
            {
                "case_id": self.id,
                "actor_user_id": self.env.user.id,
                "actor_role": _actor_role(self.env),
                "event_type": event_type,
                "entity_type": entity_type,
                "entity_ref": entity_ref or self.external_case_id,
                "reason": reason,
                "payload_json": _to_text_json(_to_audit_value(payload)),
            }
        )

    def _ensure_endoscopist_signoff_role(self):
        if not self.env.user.has_group("phd_ass_bridge.group_phd_ass_endoscopist"):
            raise ValidationError("Only a user with the Endoscopist role can finalize a report.")

    def _ensure_reopen_role(self):
        if not (
            self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin")
            or self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")
        ):
            raise ValidationError("Only a clinical operations admin can reopen a finalized report.")

    def _ensure_return_to_draft_role(self):
        if not (
            self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin")
            or self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")
        ):
            raise ValidationError("Only a clinical operations admin can return a case to draft.")

    def _actor_can_override_case_scope(self):
        return self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")

    def _actor_can_manage_facility_cases(self):
        return self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin") or self._actor_can_override_case_scope()

    def _user_allowed_facility_ids(self, user):
        return set(user.sudo().phd_ass_facility_ids.ids)

    def _ensure_actor_can_access_facility_id(self, facility_id):
        if self._actor_can_override_case_scope():
            return
        if not facility_id:
            raise ValidationError("Select a facility before saving this clinical case.")
        if facility_id not in self._user_allowed_facility_ids(self.env.user):
            raise ValidationError("You can only access clinical cases for your assigned facilities.")

    def _ensure_actor_can_sync_case_payload(self, payload, existing_record=False, prepared_vals=None):
        if existing_record:
            actor_record = existing_record.with_user(self.env.user)
            actor_record.check_access_rights("write")
            actor_record.check_access_rule("write")
        else:
            self.check_access_rights("create")

        facility_id = (prepared_vals or {}).get("facility_id") or (existing_record.facility_id.id if existing_record and existing_record.facility_id else False)
        self._ensure_actor_can_access_facility_id(facility_id)

        if self._actor_can_override_case_scope():
            return
        if self._actor_can_manage_facility_cases():
            return

        actor_refs = _allowed_actor_refs(self.env.user)
        assigned_refs = {
            str(payload.get("endoscopist_user_id") or "").strip(),
            str(payload.get("endoscopist_user_ref") or "").strip(),
            str(payload.get("assistant_nurse_user_id") or "").strip(),
            str(payload.get("assistant_nurse_user_ref") or "").strip(),
        }
        assigned_refs = {ref for ref in assigned_refs if ref}
        if not actor_refs.intersection(assigned_refs):
            raise ValidationError("Clinical authors can only create or update cases that are assigned to them.")

    @api.onchange("facility_id")
    def _onchange_facility_id(self):
        if self.facility_unit_id and self.facility_unit_id.facility_id != self.facility_id:
            self.facility_unit_id = False
        if self.assistant_nurse_user_id and not self._nurse_belongs_to_endoscopist(self.assistant_nurse_user_id, self.endoscopist_user_id, self.facility_id):
            self.assistant_nurse_user_id = False
            self.assistant_nurse_user_ref = False

    @api.onchange("facility_unit_id")
    def _onchange_facility_unit_id(self):
        if self.facility_unit_id:
            self.facility_id = self.facility_unit_id.facility_id
        if self.assistant_nurse_user_id and not self._nurse_belongs_to_endoscopist(self.assistant_nurse_user_id, self.endoscopist_user_id, self.facility_id):
            self.assistant_nurse_user_id = False
            self.assistant_nurse_user_ref = False

    @api.onchange("endoscopist_user_id")
    def _onchange_endoscopist_user_id(self):
        if not self.facility_id:
            inferred_facility = self._single_facility_for_endoscopist(self.endoscopist_user_id)
            if inferred_facility:
                self.facility_id = inferred_facility
        if self.assistant_nurse_user_id and not self._nurse_belongs_to_endoscopist(self.assistant_nurse_user_id, self.endoscopist_user_id, self.facility_id):
            self.assistant_nurse_user_id = False
            self.assistant_nurse_user_ref = False

    def _single_facility_for_endoscopist(self, endoscopist):
        if not endoscopist:
            return self.env["phd.ass.facility"].browse()
        facility_ids = self.env["phd.ass.care.team"].sudo().search(
            [("active", "=", True), ("endoscopist_user_id", "=", endoscopist.id)]
        ).mapped("facility_id")
        return facility_ids if len(facility_ids) == 1 else self.env["phd.ass.facility"].browse()

    @api.constrains("facility_id", "endoscopist_user_id", "assistant_nurse_user_id")
    def _check_nurse_belongs_to_endoscopist(self):
        for record in self:
            if record.assistant_nurse_user_id and not record.endoscopist_user_id:
                raise ValidationError("Select an endoscopist before assigning a nurse.")
            if record.assistant_nurse_user_id and not record.facility_id:
                raise ValidationError("Select a facility before assigning a nurse.")
            if record.assistant_nurse_user_id and not record._nurse_belongs_to_endoscopist(record.assistant_nurse_user_id, record.endoscopist_user_id, record.facility_id):
                raise ValidationError("The selected nurse is not assigned to this endoscopist's care team for this facility.")

    def _nurse_belongs_to_endoscopist(self, nurse, endoscopist, facility):
        if not nurse:
            return True
        if not endoscopist or not facility:
            return False
        return bool(
            self.env["phd.ass.care.team"].sudo().search_count(
                [
                    ("active", "=", True),
                    ("facility_id", "=", facility.id),
                    ("endoscopist_user_id", "=", endoscopist.id),
                    ("nurse_user_id", "=", nurse.id),
                ]
            )
        )

    @api.constrains("facility_id", "facility_unit_id")
    def _check_facility_unit_alignment(self):
        for record in self:
            if record.facility_id and record.facility_unit_id and record.facility_unit_id.facility_id != record.facility_id:
                raise ValidationError("The selected unit must belong to the selected facility.")

    def _prepare_reference_vals(self, vals):
        prepared = dict(vals)
        facility_model = self.env["phd.ass.facility"].with_context(active_test=False)
        unit_model = self.env["phd.ass.facility.unit"].with_context(active_test=False)
        user_model = self.env["res.users"].with_context(active_test=False)

        if not prepared.get("facility_id") and prepared.get("endoscopist_user_id"):
            inferred_facility = self._single_facility_for_endoscopist(user_model.browse(prepared["endoscopist_user_id"]))
            if inferred_facility:
                prepared["facility_id"] = inferred_facility.id

        if "facility_id" in prepared and "facility_unit_id" not in prepared and len(self) == 1:
            record = self[0]
            if record.facility_unit_id and record.facility_unit_id.facility_id.id != prepared.get("facility_id"):
                prepared["facility_unit_id"] = False

        if "facility_unit_id" in prepared:
            if prepared["facility_unit_id"]:
                unit = unit_model.browse(prepared["facility_unit_id"])
                prepared["facility_id"] = unit.facility_id.id or False
                prepared["facility_unit"] = unit.full_name or unit.name
            elif prepared.get("facility_id"):
                facility = facility_model.browse(prepared["facility_id"])
                prepared["facility_unit"] = facility.name or False
            else:
                # Preserve free-text unit labels when master facility data is not configured yet.
                prepared["facility_unit"] = prepared.get("facility_unit") or False
        elif "facility_unit" in prepared:
            unit = _find_facility_unit_by_ref(self.env, prepared.get("facility_unit"))
            if unit:
                prepared["facility_id"] = unit.facility_id.id
                prepared["facility_unit_id"] = unit.id
                prepared["facility_unit"] = unit.full_name or unit.name
            else:
                facility = _find_facility_by_ref(self.env, prepared.get("facility_unit"))
                prepared["facility_id"] = facility.id if facility else False
                prepared["facility_unit_id"] = False
                prepared["facility_unit"] = facility.name if facility else prepared.get("facility_unit")
        elif "facility_id" in prepared:
            if prepared.get("facility_id"):
                facility = facility_model.browse(prepared["facility_id"])
                prepared["facility_unit"] = facility.name or False
            else:
                prepared["facility_unit"] = False
                prepared["facility_unit_id"] = False

        if "endoscopist_user_id" in prepared:
            if prepared["endoscopist_user_id"]:
                user = user_model.browse(prepared["endoscopist_user_id"])
                prepared["endoscopist_user_ref"] = _user_reference(user)
            else:
                prepared["endoscopist_user_ref"] = prepared.get("endoscopist_user_ref") or False
        elif "endoscopist_user_ref" in prepared:
            user = _find_user_by_ref(self.env, prepared.get("endoscopist_user_ref"))
            prepared["endoscopist_user_id"] = user.id if user else False
            prepared["endoscopist_user_ref"] = _user_reference(user) if user else prepared.get("endoscopist_user_ref")

        if "assistant_nurse_user_id" in prepared:
            if prepared["assistant_nurse_user_id"]:
                user = user_model.browse(prepared["assistant_nurse_user_id"])
                prepared["assistant_nurse_user_ref"] = _user_reference(user)
            else:
                prepared["assistant_nurse_user_ref"] = prepared.get("assistant_nurse_user_ref") or False
        elif "assistant_nurse_user_ref" in prepared:
            user = _find_user_by_ref(self.env, prepared.get("assistant_nurse_user_ref"))
            prepared["assistant_nurse_user_id"] = user.id if user else False
            prepared["assistant_nurse_user_ref"] = _user_reference(user) if user else prepared.get("assistant_nurse_user_ref")

        return prepared

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        for vals in vals_list:
            draft_vals = self._prepare_reference_vals(vals)
            draft_vals.setdefault("external_case_id", str(uuid.uuid4()))
            draft_vals.setdefault("case_status", "draft")
            draft_vals.setdefault("procedure_type", "colonoscopy")
            if not self.env.context.get("phd_ass_bridge_sync"):
                self._ensure_actor_can_access_facility_id(draft_vals.get("facility_id"))
                draft_vals.setdefault("sync_status", "draft_local")
                draft_vals["last_sync_error"] = False
            prepared_vals.append(draft_vals)

        records = super().create(prepared_vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            for record, draft_vals in zip(records, prepared_vals):
                record._log_audit_event(
                    event_type="case_created",
                    payload={
                        "procedure_type": record.procedure_type,
                        "created_fields": sorted(draft_vals.keys()),
                    },
                )
            records._auto_push_if_enabled()
        return records

    def write(self, vals):
        prepared_vals = self._prepare_reference_vals(vals)
        if self.env.context.get("phd_ass_bridge_sync"):
            return super().write(prepared_vals)

        self._ensure_case_editable()
        self._ensure_manual_fields_allowed(prepared_vals)
        for record in self:
            facility_id = prepared_vals.get("facility_id") if "facility_id" in prepared_vals else record.facility_id.id
            record._ensure_actor_can_access_facility_id(facility_id)

        audit_fields = [field_name for field_name in prepared_vals.keys() if field_name in self._fields]
        previous_values = {record.id: record._prepare_audit_field_values(audit_fields) for record in self}
        manual_vals = dict(prepared_vals)
        manual_vals["sync_status"] = "draft_local"
        manual_vals["last_sync_error"] = False
        result = super().write(manual_vals)
        for record in self:
            changes = {}
            deleted_fields = []
            for field_name in audit_fields:
                before_value = previous_values[record.id].get(field_name)
                after_value = _to_audit_value(record[field_name])
                if before_value != after_value:
                    changes[field_name] = {"before": before_value, "after": after_value}
                    if before_value not in (False, None, "", [], {}) and after_value in (False, None, "", [], {}):
                        deleted_fields.append(field_name)
            if changes:
                record._log_audit_event(
                    "draft_updated",
                    payload={"changed_fields": sorted(changes.keys()), "changed_field_count": len(changes)},
                )
            if deleted_fields:
                record._log_audit_event("field_deleted", payload={"fields": deleted_fields})
        self._auto_push_if_enabled()
        return result

    def unlink(self):
        if not self.env.context.get("phd_ass_bridge_sync"):
            self._ensure_case_editable()
        return super().unlink()

    def _ensure_case_editable(self):
        finalized_records = self.filtered(lambda record: record.case_status == "finalized")
        if finalized_records:
            raise ValidationError("Finalized clinical cases are locked in Odoo. Reopen them in the clinical workflow first.")

    def _ensure_manual_fields_allowed(self, vals):
        locked_fields = {
            "external_case_id",
            "finalized_at",
            "finalized_by_user_ref",
            "template_version",
            "report_narrative_snapshot",
            "pdf_attachment_id",
            "pdf_asset_ref",
            "validation_summary",
            "reopen_reason",
            "reopened_at",
            "reopened_by_user_ref",
            "payload_version",
            "last_synced_at",
            "last_push_to_api_at",
            "sync_status",
            "last_sync_error",
            "clinical_payload_json",
        }

        invalid_fields = sorted(locked_fields.intersection(vals.keys()))
        if invalid_fields:
            raise ValidationError(f"These fields are managed by the clinical integration: {', '.join(invalid_fields)}.")

        if vals.get("case_status") == "finalized":
            raise ValidationError("Finalization must come from the clinical API and sign-off workflow.")

    @api.model
    def sync_from_payload(self, payload):
        payload = payload or {}
        external_case_id = payload.get("case_id") or payload.get("external_case_id")
        if not external_case_id:
            raise ValidationError("The sync payload must include case_id or external_case_id.")

        sync_model = self.with_context(phd_ass_bridge_sync=True)
        existing_record = self.sudo().with_context(phd_ass_bridge_sync=True).search([("external_case_id", "=", external_case_id)], limit=1)
        vals = self._prepare_case_vals(payload)
        self._ensure_actor_can_sync_case_payload(payload, existing_record=existing_record, prepared_vals=vals)
        record = existing_record.with_user(self.env.user).with_context(phd_ass_bridge_sync=True) if existing_record else sync_model.browse()

        if "segment_exam" in payload or "segments" in payload:
            vals["segment_ids"] = self._segment_commands(payload.get("segment_exam") or payload.get("segments") or [])
        if "lesions" in payload:
            vals["lesion_ids"] = self._lesion_commands(payload.get("lesions") or [])
        if "specimens" in payload:
            vals["specimen_ids"] = self._specimen_commands(payload.get("specimens") or [])
        if record:
            record.write(vals)
        else:
            record = sync_model.create(vals)

        if "image_attachments" in payload:
            self._sync_image_attachments(record, payload.get("image_attachments") or [])
        if "followup_tasks" in payload or "tasks" in payload:
            self._sync_tasks(record, payload.get("followup_tasks") or payload.get("tasks") or [])

        if record.case_status == "finalized" and record.finalized_at:
            existing_revision = record.revision_ids.filtered(lambda revision: revision.finalized_at == record.finalized_at)
            if not existing_revision:
                record._create_final_revision()

        record._log_sync_event(
            event_type="case_sync",
            status="success",
            direction="api_to_odoo",
            message="Clinical case synchronized from the clinical API into Odoo.",
            payload_version=payload.get("payload_version") or payload.get("template_version"),
            payload_excerpt=_minimal_sync_excerpt(payload),
        )
        return record

    def _prepare_case_vals(self, payload):
        procedure_datetime = _to_datetime_value(payload.get("procedure_datetime"))
        vals = {
            "external_case_id": payload.get("case_id") or payload.get("external_case_id"),
            "case_status": payload.get("case_status") or "draft",
            "procedure_type": payload.get("procedure_type") or "colonoscopy",
            "patient_identifier": payload.get("patient_identifier"),
            "procedure_datetime": procedure_datetime,
            "dob_or_age": payload.get("dob_or_age"),
            "sex": payload.get("sex"),
            "facility_unit": payload.get("facility_unit"),
            "endoscopist_user_ref": payload.get("endoscopist_user_id") or payload.get("endoscopist_user_ref"),
            "assistant_nurse_user_ref": payload.get("assistant_nurse_user_id") or payload.get("assistant_nurse_user_ref"),
            "referrer_service": payload.get("referrer_service"),
            "indication": payload.get("indication"),
            "priority": payload.get("priority"),
            "relevant_history": payload.get("relevant_history"),
            "asa_class": payload.get("asa_class"),
            "allergies": payload.get("allergies"),
            "antithrombotic_plan": payload.get("antithrombotic_plan"),
            "consent_documented": bool(payload.get("consent_documented")),
            "patient_identity_verified": bool(payload.get("patient_identity_verified")),
            "team_pause_completed": bool(payload.get("team_pause_completed")),
            "sedation_anesthesia": payload.get("sedation_anesthesia"),
            "monitor_spo2": bool(payload.get("monitor_spo2")),
            "monitor_hr": bool(payload.get("monitor_hr")),
            "monitor_bp": bool(payload.get("monitor_bp")),
            "monitor_ecg": bool(payload.get("monitor_ecg")),
            "monitor_capnography": bool(payload.get("monitor_capnography")),
            "antibiotics_status": payload.get("antibiotics_status"),
            "pregnancy_status": payload.get("pregnancy_status"),
            "bowel_prep_agent": payload.get("bowel_prep_agent"),
            "prep_quality": payload.get("prep_quality"),
            "bbps_right": payload.get("bbps_right") or 0,
            "bbps_transverse": payload.get("bbps_transverse") or 0,
            "bbps_left": payload.get("bbps_left") or 0,
            "insertion_time": payload.get("insertion_time"),
            "cecum_reached": bool(payload.get("cecum_reached")),
            "cecal_landmark_appendiceal_orifice": bool(payload.get("cecal_landmark_appendiceal_orifice")),
            "cecal_landmark_ileocecal_valve": bool(payload.get("cecal_landmark_ileocecal_valve")),
            "photo_cecum": bool(payload.get("photo_cecum")),
            "photo_pathology": bool(payload.get("photo_pathology")),
            "terminal_ileum_status": payload.get("terminal_ileum_status"),
            "withdrawal_time_minutes": payload.get("withdrawal_time_minutes") or 0,
            "technical_limitation": payload.get("technical_limitation"),
            "technical_limitation_note": payload.get("technical_limitation_note"),
            "adverse_event_during_procedure": bool(payload.get("adverse_event_during_procedure")),
            "adverse_event_note": payload.get("adverse_event_note"),
            "uc_mayo_score": payload.get("uc_mayo_score"),
            "crohn_score": payload.get("crohn_score"),
            "disease_extent": payload.get("disease_extent"),
            "small_polyp_technique": payload.get("small_polyp_technique"),
            "small_polyp_technique_note": payload.get("small_polyp_technique_note"),
            "advanced_resection_type": ", ".join(payload.get("advanced_resection_type", []))
            if isinstance(payload.get("advanced_resection_type"), list)
            else payload.get("advanced_resection_type"),
            "tattoo_status": payload.get("tattoo_status"),
            "tattoo_location_note": payload.get("tattoo_location_note"),
            "hemostasis_or_closure": payload.get("hemostasis_or_closure"),
            "impression": payload.get("impression"),
            "pathology_status": payload.get("pathology_status"),
            "surveillance_interval_value": payload.get("surveillance_interval_value"),
            "surveillance_interval_pending_pathology": bool(payload.get("surveillance_interval_pending_pathology")),
            "surveillance_interval_reason": payload.get("surveillance_interval_reason"),
            "surveillance_interval_reason_note": payload.get("surveillance_interval_reason_note"),
            "adverse_event_plan": payload.get("adverse_event_plan"),
            "adverse_event_plan_note": payload.get("adverse_event_plan_note"),
            "informed_patient": bool(payload.get("informed_patient")),
            "informed_referrer": bool(payload.get("informed_referrer")),
            "written_instructions_given": bool(payload.get("written_instructions_given")),
            "egd_scope_id": payload.get("egd_scope_id"),
            "egd_extent_reached": payload.get("egd_extent_reached"),
            "egd_start_time": payload.get("egd_start_time"),
            "egd_end_time": payload.get("egd_end_time"),
            "egd_preparation_status": payload.get("egd_preparation_status"),
            "egd_tolerance": payload.get("egd_tolerance"),
            "egd_photo_landmarks": bool(payload.get("egd_photo_landmarks")),
            "egd_specimens_obtained": bool(payload.get("egd_specimens_obtained")),
            "egd_exam_esophagus_normal": bool(payload.get("egd_exam_esophagus_normal")),
            "egd_exam_esophagus_note": payload.get("egd_exam_esophagus_note"),
            "egd_exam_esophagus_photo": bool(payload.get("egd_exam_esophagus_photo")),
            "egd_exam_z_line_normal": bool(payload.get("egd_exam_z_line_normal")),
            "egd_exam_z_line_note": payload.get("egd_exam_z_line_note"),
            "egd_exam_z_line_photo": bool(payload.get("egd_exam_z_line_photo")),
            "egd_exam_cardia_fundus_normal": bool(payload.get("egd_exam_cardia_fundus_normal")),
            "egd_exam_cardia_fundus_note": payload.get("egd_exam_cardia_fundus_note"),
            "egd_exam_cardia_fundus_photo": bool(payload.get("egd_exam_cardia_fundus_photo")),
            "egd_exam_gastric_body_normal": bool(payload.get("egd_exam_gastric_body_normal")),
            "egd_exam_gastric_body_note": payload.get("egd_exam_gastric_body_note"),
            "egd_exam_gastric_body_photo": bool(payload.get("egd_exam_gastric_body_photo")),
            "egd_exam_incisura_antrum_normal": bool(payload.get("egd_exam_incisura_antrum_normal")),
            "egd_exam_incisura_antrum_note": payload.get("egd_exam_incisura_antrum_note"),
            "egd_exam_incisura_antrum_photo": bool(payload.get("egd_exam_incisura_antrum_photo")),
            "egd_exam_pylorus_normal": bool(payload.get("egd_exam_pylorus_normal")),
            "egd_exam_pylorus_note": payload.get("egd_exam_pylorus_note"),
            "egd_exam_pylorus_photo": bool(payload.get("egd_exam_pylorus_photo")),
            "egd_exam_duodenal_bulb_normal": bool(payload.get("egd_exam_duodenal_bulb_normal")),
            "egd_exam_duodenal_bulb_note": payload.get("egd_exam_duodenal_bulb_note"),
            "egd_exam_duodenal_bulb_photo": bool(payload.get("egd_exam_duodenal_bulb_photo")),
            "egd_exam_second_duodenum_normal": bool(payload.get("egd_exam_second_duodenum_normal")),
            "egd_exam_second_duodenum_note": payload.get("egd_exam_second_duodenum_note"),
            "egd_exam_second_duodenum_photo": bool(payload.get("egd_exam_second_duodenum_photo")),
            "egd_erosive_esophagitis_la_grade": payload.get("egd_erosive_esophagitis_la_grade"),
            "egd_barrett_circumference_cm": payload.get("egd_barrett_circumference_cm"),
            "egd_barrett_maximal_cm": payload.get("egd_barrett_maximal_cm"),
            "egd_barrett_visible_lesion": bool(payload.get("egd_barrett_visible_lesion")),
            "egd_erefs_edema": payload.get("egd_erefs_edema"),
            "egd_erefs_rings": payload.get("egd_erefs_rings"),
            "egd_erefs_exudates": payload.get("egd_erefs_exudates"),
            "egd_erefs_furrows": payload.get("egd_erefs_furrows"),
            "egd_erefs_stricture": payload.get("egd_erefs_stricture"),
            "egd_forrest_classification": payload.get("egd_forrest_classification"),
            "egd_standardized_score_name": payload.get("egd_standardized_score_name"),
            "egd_standardized_score_value": payload.get("egd_standardized_score_value"),
            "egd_esophagus_finding": payload.get("egd_esophagus_finding"),
            "egd_stomach_finding": payload.get("egd_stomach_finding"),
            "egd_duodenum_finding": payload.get("egd_duodenum_finding"),
            "egd_hiatal_hernia": bool(payload.get("egd_hiatal_hernia")),
            "egd_retroflexion_performed": bool(payload.get("egd_retroflexion_performed")),
            "egd_biopsy_taken": bool(payload.get("egd_biopsy_taken")),
            "egd_therapy_performed": payload.get("egd_therapy_performed"),
            "egd_hemostasis_method": payload.get("egd_hemostasis_method"),
            "egd_dilation_type": payload.get("egd_dilation_type"),
            "egd_dilation_diameter_mm": payload.get("egd_dilation_diameter_mm") or 0,
            "egd_variceal_other_therapy": payload.get("egd_variceal_other_therapy"),
            "egd_therapy_outcome": payload.get("egd_therapy_outcome"),
            "egd_outcome_details": payload.get("egd_outcome_details"),
            "egd_impression": payload.get("egd_impression"),
            "egd_h_pylori_plan": payload.get("egd_h_pylori_plan"),
            "egd_medication_therapy": payload.get("egd_medication_therapy"),
            "egd_followup_surveillance": payload.get("egd_followup_surveillance"),
            "egd_result_communication_planned": bool(payload.get("egd_result_communication_planned")),
            "egd_referrer_communication_planned": bool(payload.get("egd_referrer_communication_planned")),
            "ercp_indication": payload.get("ercp_indication"),
            "ercp_papilla_status": payload.get("ercp_papilla_status"),
            "ercp_papilla_appearance": payload.get("ercp_papilla_appearance"),
            "ercp_therapeutic_intent": payload.get("ercp_therapeutic_intent"),
            "ercp_imaging_reviewed": payload.get("ercp_imaging_reviewed"),
            "ercp_antibiotic_prophylaxis": payload.get("ercp_antibiotic_prophylaxis"),
            "ercp_rectal_nsaid": payload.get("ercp_rectal_nsaid"),
            "ercp_hydration_plan": payload.get("ercp_hydration_plan"),
            "ercp_pancreatic_stent_plan": payload.get("ercp_pancreatic_stent_plan"),
            "ercp_rescue_plan": payload.get("ercp_rescue_plan"),
            "ercp_radiation_protection_verified": bool(payload.get("ercp_radiation_protection_verified")),
            "ercp_pregnancy_precautions": payload.get("ercp_pregnancy_precautions"),
            "ercp_cannulation_success": bool(payload.get("ercp_cannulation_success")),
            "ercp_cannulation_technique": payload.get("ercp_cannulation_technique"),
            "ercp_cannulation_contacts": payload.get("ercp_cannulation_contacts") or 0,
            "ercp_cannulation_time_minutes": payload.get("ercp_cannulation_time_minutes") or 0,
            "ercp_unintended_pd_access_count": payload.get("ercp_unintended_pd_access_count") or 0,
            "ercp_pancreatic_duct_status": payload.get("ercp_pancreatic_duct_status"),
            "ercp_prophylactic_pd_stent": bool(payload.get("ercp_prophylactic_pd_stent")),
            "ercp_prophylactic_pd_stent_details": payload.get("ercp_prophylactic_pd_stent_details"),
            "ercp_cholangiogram_cbd_mm": payload.get("ercp_cholangiogram_cbd_mm") or 0,
            "ercp_intrahepatic_ducts": payload.get("ercp_intrahepatic_ducts"),
            "ercp_stone_count": payload.get("ercp_stone_count") or 0,
            "ercp_largest_stone_mm": payload.get("ercp_largest_stone_mm") or 0,
            "ercp_stricture_site": payload.get("ercp_stricture_site"),
            "ercp_leak_note": payload.get("ercp_leak_note"),
            "ercp_anatomy_other_findings": payload.get("ercp_anatomy_other_findings"),
            "ercp_drainage_achieved": payload.get("ercp_drainage_achieved"),
            "ercp_ducts_accessed": payload.get("ercp_ducts_accessed"),
            "ercp_sphincterotomy_performed": bool(payload.get("ercp_sphincterotomy_performed")),
            "ercp_sphincterotomy_type": payload.get("ercp_sphincterotomy_type"),
            "ercp_sphincterotomy_details": payload.get("ercp_sphincterotomy_details"),
            "ercp_papillary_dilation_balloon_mm": payload.get("ercp_papillary_dilation_balloon_mm") or 0,
            "ercp_stone_extraction_performed": bool(payload.get("ercp_stone_extraction_performed")),
            "ercp_stone_therapy": payload.get("ercp_stone_therapy"),
            "ercp_stricture_therapy": payload.get("ercp_stricture_therapy"),
            "ercp_stent_placed": bool(payload.get("ercp_stent_placed")),
            "ercp_biliary_stent_type": payload.get("ercp_biliary_stent_type"),
            "ercp_stent_details": payload.get("ercp_stent_details"),
            "ercp_other_intervention": payload.get("ercp_other_intervention"),
            "ercp_fluoroscopy_time_minutes": payload.get("ercp_fluoroscopy_time_minutes") or 0,
            "ercp_dose_area_product": payload.get("ercp_dose_area_product"),
            "ercp_reference_air_kerma": payload.get("ercp_reference_air_kerma"),
            "ercp_images_acquired": payload.get("ercp_images_acquired") or 0,
            "ercp_dose_reduction_measures": payload.get("ercp_dose_reduction_measures"),
            "ercp_dose_reduction_other": payload.get("ercp_dose_reduction_other"),
            "ercp_intended_therapy": payload.get("ercp_intended_therapy"),
            "ercp_technical_success": payload.get("ercp_technical_success"),
            "ercp_stone_clearance": payload.get("ercp_stone_clearance"),
            "ercp_biliary_drainage_outcome": payload.get("ercp_biliary_drainage_outcome"),
            "ercp_immediate_adverse_event": payload.get("ercp_immediate_adverse_event"),
            "ercp_temporary_stent": bool(payload.get("ercp_temporary_stent")),
            "ercp_removal_exchange_due": _to_date_value(payload.get("ercp_removal_exchange_due")),
            "ercp_pd_stent": bool(payload.get("ercp_pd_stent")),
            "ercp_migration_passage_check": payload.get("ercp_migration_passage_check"),
            "ercp_patient_contact_note": payload.get("ercp_patient_contact_note"),
            "ercp_tracking_register_entered": bool(payload.get("ercp_tracking_register_entered")),
            "ercp_repeat_intervention": payload.get("ercp_repeat_intervention"),
            "ercp_repeat_intervention_timing": payload.get("ercp_repeat_intervention_timing"),
            "ercp_post_ercp_pancreatitis": payload.get("ercp_post_ercp_pancreatitis"),
            "ercp_significant_bleeding": payload.get("ercp_significant_bleeding"),
            "ercp_cholangitis_or_cholecystitis": payload.get("ercp_cholangitis_or_cholecystitis"),
            "ercp_unplanned_hospital_visit": payload.get("ercp_unplanned_hospital_visit"),
            "ercp_complication_note": payload.get("ercp_complication_note"),
            "ercp_impression": payload.get("ercp_impression"),
            "eus_route": payload.get("eus_route"),
            "eus_echoendoscope": payload.get("eus_echoendoscope"),
            "eus_intent": payload.get("eus_intent"),
            "eus_upper_esophagus": bool(payload.get("eus_upper_esophagus")),
            "eus_upper_stomach": bool(payload.get("eus_upper_stomach")),
            "eus_upper_duodenum": bool(payload.get("eus_upper_duodenum")),
            "eus_pancreas_examined": bool(payload.get("eus_pancreas_examined")),
            "eus_cbd_examined": bool(payload.get("eus_cbd_examined")),
            "eus_gallbladder_examined": bool(payload.get("eus_gallbladder_examined")),
            "eus_liver_examined": bool(payload.get("eus_liver_examined")),
            "eus_adrenal_examined": bool(payload.get("eus_adrenal_examined")),
            "eus_mediastinum_examined": bool(payload.get("eus_mediastinum_examined")),
            "eus_nodes_examined": bool(payload.get("eus_nodes_examined")),
            "eus_doppler_used": bool(payload.get("eus_doppler_used")),
            "eus_relevant_anatomy_documented": payload.get("eus_relevant_anatomy_documented"),
            "eus_photo_anatomy": bool(payload.get("eus_photo_anatomy")),
            "eus_technical_limitation": payload.get("eus_technical_limitation"),
            "eus_immediate_adverse_event_note": payload.get("eus_immediate_adverse_event_note"),
            "eus_regions_examined": payload.get("eus_regions_examined"),
            "eus_target_lesion_present": bool(payload.get("eus_target_lesion_present")),
            "eus_target_location": payload.get("eus_target_location"),
            "eus_target_size_mm": payload.get("eus_target_size_mm") or 0,
            "eus_echogenicity": payload.get("eus_echogenicity"),
            "eus_margins": payload.get("eus_margins"),
            "eus_vascular_relation": payload.get("eus_vascular_relation"),
            "eus_nodes_note": payload.get("eus_nodes_note"),
            "eus_image_reference": payload.get("eus_image_reference"),
            "eus_cancer_site": payload.get("eus_cancer_site"),
            "eus_staging_system": payload.get("eus_staging_system"),
            "eus_t_stage": payload.get("eus_t_stage"),
            "eus_n_stage": payload.get("eus_n_stage"),
            "eus_m_features": payload.get("eus_m_features"),
            "eus_vascular_invasion": payload.get("eus_vascular_invasion"),
            "eus_overall_stage": payload.get("eus_overall_stage"),
            "eus_management_implication": payload.get("eus_management_implication"),
            "eus_tissue_target": payload.get("eus_tissue_target"),
            "eus_approach": payload.get("eus_approach"),
            "eus_needle_type": payload.get("eus_needle_type"),
            "eus_needle_gauge": payload.get("eus_needle_gauge"),
            "eus_needle_design": payload.get("eus_needle_design"),
            "eus_fna_performed": bool(payload.get("eus_fna_performed")),
            "eus_fnb_performed": bool(payload.get("eus_fnb_performed")),
            "eus_passes_count": payload.get("eus_passes_count") or 0,
            "eus_rose_status": payload.get("eus_rose_status"),
            "eus_mose_status": payload.get("eus_mose_status"),
            "eus_specimen_type": payload.get("eus_specimen_type"),
            "eus_container_labels": payload.get("eus_container_labels"),
            "eus_adequacy_status": payload.get("eus_adequacy_status"),
            "eus_adequacy_note": payload.get("eus_adequacy_note"),
            "eus_label_verified": bool(payload.get("eus_label_verified")),
            "eus_complication_type": payload.get("eus_complication_type"),
            "eus_antibiotics_after_sampling": payload.get("eus_antibiotics_after_sampling"),
            "eus_intervention_procedure": payload.get("eus_intervention_procedure"),
            "eus_intervention_target_route": payload.get("eus_intervention_target_route"),
            "eus_device_stent": payload.get("eus_device_stent"),
            "eus_technical_success": payload.get("eus_technical_success"),
            "eus_clinical_plan": payload.get("eus_clinical_plan"),
            "eus_immediate_adverse_event": payload.get("eus_immediate_adverse_event"),
            "eus_impression": payload.get("eus_impression"),
            "eus_pathology_cytology_status": payload.get("eus_pathology_cytology_status"),
            "eus_followup_imaging_or_procedure": payload.get("eus_followup_imaging_or_procedure"),
            "eus_multidisciplinary_referral": payload.get("eus_multidisciplinary_referral"),
            "finalized_at": _to_datetime_value(payload.get("finalized_at")),
            "finalized_by_user_id": _find_user_by_ref(self.env, payload.get("finalized_by_user_id") or payload.get("finalized_by_user_ref")).id or False,
            "finalized_by_user_ref": payload.get("finalized_by_user_id") or payload.get("finalized_by_user_ref"),
            "template_version": payload.get("template_version"),
            "report_narrative_snapshot": payload.get("report_narrative_snapshot"),
            "pdf_asset_ref": payload.get("pdf_asset_ref"),
            "validation_summary": payload.get("validation_summary"),
            "payload_version": payload.get("payload_version") or payload.get("template_version"),
            "last_synced_at": fields.Datetime.now(),
            "sync_status": "synced",
            "last_sync_error": False,
            "clinical_payload_json": False,
        }
        facility = _find_facility_by_ref(self.env, payload.get("facility_code")) if payload.get("facility_code") else self.env["phd.ass.facility"].browse()
        unit_ref = payload.get("facility_unit_code") or payload.get("facility_unit")
        if unit_ref:
            facility_unit = _find_facility_unit_by_ref(self.env, unit_ref, facility=facility)
            if facility_unit:
                vals["facility_id"] = facility_unit.facility_id.id
                vals["facility_unit_id"] = facility_unit.id
                vals["facility_unit"] = facility_unit.full_name or facility_unit.name
        elif facility:
            vals["facility_id"] = facility.id
        return self._prepare_reference_vals(vals)

    def _segment_commands(self, rows):
        commands = [(5, 0, 0)]
        for index, row in enumerate(rows, start=1):
            commands.append(
                (
                    0,
                    0,
                    {
                        "sequence": index,
                        "segment_name": row.get("segment_name") or row.get("name"),
                        "normal": bool(row.get("normal")),
                        "finding_note": row.get("finding_note"),
                        "photo_taken": bool(row.get("photo_taken")),
                    },
                )
            )
        return commands

    def _lesion_commands(self, rows):
        commands = [(5, 0, 0)]
        for index, row in enumerate(rows, start=1):
            commands.append(
                (
                    0,
                    0,
                    {
                        "sequence": row.get("lesion_index") or index,
                        "lesion_location": row.get("lesion_location"),
                        "lesion_size_mm": row.get("lesion_size_mm") or 0,
                        "lesion_morphology": row.get("lesion_morphology"),
                        "resection_method": row.get("resection_method"),
                        "complete_resection": bool(row.get("complete_resection")),
                        "retrieved": bool(row.get("retrieved")),
                        "specimen_container_ref": row.get("specimen_container_ref"),
                    },
                )
            )
        return commands

    def _specimen_commands(self, rows):
        commands = [(5, 0, 0)]
        for index, row in enumerate(rows, start=1):
            commands.append(
                (
                    0,
                    0,
                    {
                        "sequence": index,
                        "container_label": row.get("container_label"),
                        "specimen_site": row.get("specimen_site"),
                        "specimen_count": row.get("specimen_count") or 0,
                        "test_question": row.get("test_question"),
                        "label_verified": bool(row.get("label_verified")),
                    },
                )
            )
        return commands

    def _sync_image_attachments(self, case_record, rows):
        image_model = self.env["phd.ass.case.image"].sudo().with_context(phd_ass_bridge_sync=True)
        synced_external_ids = set()

        for row in rows:
            external_image_id = row.get("external_image_id") or row.get("image_id")
            if not external_image_id:
                continue
            synced_external_ids.add(external_image_id)
            vals = image_model._prepare_vals_from_payload(case_record, row)
            existing = image_model.search(
                [
                    ("case_id", "=", case_record.id),
                    ("external_image_id", "=", external_image_id),
                ],
                limit=1,
            )
            if existing:
                existing.write(vals)
            else:
                vals.setdefault("case_id", case_record.id)
                vals.setdefault("external_image_id", external_image_id)
                image_model.create(vals)

        stale_images = case_record.sudo().image_attachment_ids.filtered(lambda image: image.external_image_id not in synced_external_ids)
        if stale_images:
            stale_images.with_context(phd_ass_bridge_sync=True).unlink()

    def _sync_tasks(self, case_record, rows):
        task_model = self.env["phd.ass.followup.task"].with_context(phd_ass_bridge_sync=True)
        synced_external_ids = set()

        for row in rows:
            external_task_id = row.get("followup_task_id") or row.get("task_id") or row.get("external_task_id")
            if not external_task_id:
                continue
            synced_external_ids.add(external_task_id)
            task_payload = dict(row)
            task_payload["external_case_id"] = case_record.external_case_id
            task_model.sync_from_payload(task_payload)

        stale_tasks = case_record.task_ids.filtered(lambda task: task.external_task_id not in synced_external_ids)
        if stale_tasks:
            stale_tasks.with_context(phd_ass_bridge_sync=True).unlink()

    def _bridge_config(self):
        config = self.env["ir.config_parameter"].sudo()
        return {
            "base_url": (config.get_param("phd_ass_bridge.clinical_api_base_url", "") or "").rstrip("/"),
            "api_key": config.get_param("phd_ass_bridge.clinical_api_key", "") or "",
            "timeout": int(config.get_param("phd_ass_bridge.request_timeout_seconds", 10) or 10),
            "auto_push_on_save": config.get_param("phd_ass_bridge.auto_push_on_save", "False") == "True",
        }

    def _serialize_for_clinical_api(self):
        self.ensure_one()
        return {
            "external_case_id": self.external_case_id,
            "case_status": self.case_status,
            "procedure_type": self.procedure_type,
            "patient_identifier": self.patient_identifier,
            "procedure_datetime": _to_api_datetime(self.procedure_datetime),
            "dob_or_age": self.dob_or_age,
            "sex": self.sex,
            "facility_unit": self.facility_unit,
            "facility_code": self.facility_id.code or self.facility_id.name or False,
            "facility_unit_code": self.facility_unit_id.code or self.facility_unit_id.full_name or False,
            "endoscopist_user_id": _user_identifier(self.endoscopist_user_id),
            "endoscopist_user_ref": self.endoscopist_user_ref,
            "assistant_nurse_user_id": _user_identifier(self.assistant_nurse_user_id),
            "assistant_nurse_user_ref": self.assistant_nurse_user_ref,
            "referrer_service": self.referrer_service,
            "indication": self.indication,
            "priority": self.priority,
            "relevant_history": self.relevant_history,
            "asa_class": self.asa_class,
            "allergies": self.allergies,
            "antithrombotic_plan": self.antithrombotic_plan,
            "consent_documented": self.consent_documented,
            "patient_identity_verified": self.patient_identity_verified,
            "team_pause_completed": self.team_pause_completed,
            "sedation_anesthesia": self.sedation_anesthesia,
            "monitor_spo2": self.monitor_spo2,
            "monitor_hr": self.monitor_hr,
            "monitor_bp": self.monitor_bp,
            "monitor_ecg": self.monitor_ecg,
            "monitor_capnography": self.monitor_capnography,
            "antibiotics_status": self.antibiotics_status,
            "pregnancy_status": self.pregnancy_status,
            "bowel_prep_agent": self.bowel_prep_agent,
            "prep_quality": self.prep_quality,
            "bbps_right": self.bbps_right,
            "bbps_transverse": self.bbps_transverse,
            "bbps_left": self.bbps_left,
            "bbps_total": self.bbps_total,
            "insertion_time": self.insertion_time,
            "cecum_reached": self.cecum_reached,
            "cecal_landmark_appendiceal_orifice": self.cecal_landmark_appendiceal_orifice,
            "cecal_landmark_ileocecal_valve": self.cecal_landmark_ileocecal_valve,
            "photo_cecum": self.photo_cecum,
            "photo_pathology": self.photo_pathology,
            "terminal_ileum_status": self.terminal_ileum_status,
            "withdrawal_time_minutes": self.withdrawal_time_minutes,
            "technical_limitation": self.technical_limitation,
            "technical_limitation_note": self.technical_limitation_note,
            "adverse_event_during_procedure": self.adverse_event_during_procedure,
            "adverse_event_note": self.adverse_event_note,
            "uc_mayo_score": self.uc_mayo_score,
            "crohn_score": self.crohn_score,
            "disease_extent": self.disease_extent,
            "small_polyp_technique": self.small_polyp_technique,
            "small_polyp_technique_note": self.small_polyp_technique_note,
            "advanced_resection_type": self.advanced_resection_type.split(", ") if self.advanced_resection_type else [],
            "tattoo_status": self.tattoo_status,
            "tattoo_location_note": self.tattoo_location_note,
            "hemostasis_or_closure": self.hemostasis_or_closure,
            "impression": self.impression,
            "pathology_status": self.pathology_status,
            "surveillance_interval_value": self.surveillance_interval_value,
            "surveillance_interval_pending_pathology": self.surveillance_interval_pending_pathology,
            "surveillance_interval_reason": self.surveillance_interval_reason,
            "surveillance_interval_reason_note": self.surveillance_interval_reason_note,
            "adverse_event_plan": self.adverse_event_plan,
            "adverse_event_plan_note": self.adverse_event_plan_note,
            "informed_patient": self.informed_patient,
            "informed_referrer": self.informed_referrer,
            "written_instructions_given": self.written_instructions_given,
            "egd_scope_id": self.egd_scope_id,
            "egd_extent_reached": self.egd_extent_reached,
            "egd_start_time": self.egd_start_time,
            "egd_end_time": self.egd_end_time,
            "egd_preparation_status": self.egd_preparation_status,
            "egd_tolerance": self.egd_tolerance,
            "egd_photo_landmarks": self.egd_photo_landmarks,
            "egd_specimens_obtained": self.egd_specimens_obtained,
            "egd_exam_esophagus_normal": self.egd_exam_esophagus_normal,
            "egd_exam_esophagus_note": self.egd_exam_esophagus_note,
            "egd_exam_esophagus_photo": self.egd_exam_esophagus_photo,
            "egd_exam_z_line_normal": self.egd_exam_z_line_normal,
            "egd_exam_z_line_note": self.egd_exam_z_line_note,
            "egd_exam_z_line_photo": self.egd_exam_z_line_photo,
            "egd_exam_cardia_fundus_normal": self.egd_exam_cardia_fundus_normal,
            "egd_exam_cardia_fundus_note": self.egd_exam_cardia_fundus_note,
            "egd_exam_cardia_fundus_photo": self.egd_exam_cardia_fundus_photo,
            "egd_exam_gastric_body_normal": self.egd_exam_gastric_body_normal,
            "egd_exam_gastric_body_note": self.egd_exam_gastric_body_note,
            "egd_exam_gastric_body_photo": self.egd_exam_gastric_body_photo,
            "egd_exam_incisura_antrum_normal": self.egd_exam_incisura_antrum_normal,
            "egd_exam_incisura_antrum_note": self.egd_exam_incisura_antrum_note,
            "egd_exam_incisura_antrum_photo": self.egd_exam_incisura_antrum_photo,
            "egd_exam_pylorus_normal": self.egd_exam_pylorus_normal,
            "egd_exam_pylorus_note": self.egd_exam_pylorus_note,
            "egd_exam_pylorus_photo": self.egd_exam_pylorus_photo,
            "egd_exam_duodenal_bulb_normal": self.egd_exam_duodenal_bulb_normal,
            "egd_exam_duodenal_bulb_note": self.egd_exam_duodenal_bulb_note,
            "egd_exam_duodenal_bulb_photo": self.egd_exam_duodenal_bulb_photo,
            "egd_exam_second_duodenum_normal": self.egd_exam_second_duodenum_normal,
            "egd_exam_second_duodenum_note": self.egd_exam_second_duodenum_note,
            "egd_exam_second_duodenum_photo": self.egd_exam_second_duodenum_photo,
            "egd_erosive_esophagitis_la_grade": self.egd_erosive_esophagitis_la_grade,
            "egd_barrett_circumference_cm": self.egd_barrett_circumference_cm,
            "egd_barrett_maximal_cm": self.egd_barrett_maximal_cm,
            "egd_barrett_visible_lesion": self.egd_barrett_visible_lesion,
            "egd_erefs_edema": self.egd_erefs_edema,
            "egd_erefs_rings": self.egd_erefs_rings,
            "egd_erefs_exudates": self.egd_erefs_exudates,
            "egd_erefs_furrows": self.egd_erefs_furrows,
            "egd_erefs_stricture": self.egd_erefs_stricture,
            "egd_forrest_classification": self.egd_forrest_classification,
            "egd_standardized_score_name": self.egd_standardized_score_name,
            "egd_standardized_score_value": self.egd_standardized_score_value,
            "egd_esophagus_finding": self.egd_esophagus_finding,
            "egd_stomach_finding": self.egd_stomach_finding,
            "egd_duodenum_finding": self.egd_duodenum_finding,
            "egd_hiatal_hernia": self.egd_hiatal_hernia,
            "egd_retroflexion_performed": self.egd_retroflexion_performed,
            "egd_biopsy_taken": self.egd_biopsy_taken,
            "egd_therapy_performed": self.egd_therapy_performed,
            "egd_hemostasis_method": self.egd_hemostasis_method,
            "egd_dilation_type": self.egd_dilation_type,
            "egd_dilation_diameter_mm": self.egd_dilation_diameter_mm,
            "egd_variceal_other_therapy": self.egd_variceal_other_therapy,
            "egd_therapy_outcome": self.egd_therapy_outcome,
            "egd_outcome_details": self.egd_outcome_details,
            "egd_impression": self.egd_impression,
            "egd_h_pylori_plan": self.egd_h_pylori_plan,
            "egd_medication_therapy": self.egd_medication_therapy,
            "egd_followup_surveillance": self.egd_followup_surveillance,
            "egd_result_communication_planned": self.egd_result_communication_planned,
            "egd_referrer_communication_planned": self.egd_referrer_communication_planned,
            "ercp_indication": self.ercp_indication,
            "ercp_papilla_status": self.ercp_papilla_status,
            "ercp_papilla_appearance": self.ercp_papilla_appearance,
            "ercp_therapeutic_intent": self.ercp_therapeutic_intent,
            "ercp_imaging_reviewed": self.ercp_imaging_reviewed,
            "ercp_antibiotic_prophylaxis": self.ercp_antibiotic_prophylaxis,
            "ercp_rectal_nsaid": self.ercp_rectal_nsaid,
            "ercp_hydration_plan": self.ercp_hydration_plan,
            "ercp_pancreatic_stent_plan": self.ercp_pancreatic_stent_plan,
            "ercp_rescue_plan": self.ercp_rescue_plan,
            "ercp_radiation_protection_verified": self.ercp_radiation_protection_verified,
            "ercp_pregnancy_precautions": self.ercp_pregnancy_precautions,
            "ercp_cannulation_success": self.ercp_cannulation_success,
            "ercp_cannulation_technique": self.ercp_cannulation_technique,
            "ercp_cannulation_contacts": self.ercp_cannulation_contacts,
            "ercp_cannulation_time_minutes": self.ercp_cannulation_time_minutes,
            "ercp_unintended_pd_access_count": self.ercp_unintended_pd_access_count,
            "ercp_pancreatic_duct_status": self.ercp_pancreatic_duct_status,
            "ercp_prophylactic_pd_stent": self.ercp_prophylactic_pd_stent,
            "ercp_prophylactic_pd_stent_details": self.ercp_prophylactic_pd_stent_details,
            "ercp_cholangiogram_cbd_mm": self.ercp_cholangiogram_cbd_mm,
            "ercp_intrahepatic_ducts": self.ercp_intrahepatic_ducts,
            "ercp_stone_count": self.ercp_stone_count,
            "ercp_largest_stone_mm": self.ercp_largest_stone_mm,
            "ercp_stricture_site": self.ercp_stricture_site,
            "ercp_leak_note": self.ercp_leak_note,
            "ercp_anatomy_other_findings": self.ercp_anatomy_other_findings,
            "ercp_drainage_achieved": self.ercp_drainage_achieved,
            "ercp_ducts_accessed": self.ercp_ducts_accessed,
            "ercp_sphincterotomy_performed": self.ercp_sphincterotomy_performed,
            "ercp_sphincterotomy_type": self.ercp_sphincterotomy_type,
            "ercp_sphincterotomy_details": self.ercp_sphincterotomy_details,
            "ercp_papillary_dilation_balloon_mm": self.ercp_papillary_dilation_balloon_mm,
            "ercp_stone_extraction_performed": self.ercp_stone_extraction_performed,
            "ercp_stone_therapy": self.ercp_stone_therapy,
            "ercp_stricture_therapy": self.ercp_stricture_therapy,
            "ercp_stent_placed": self.ercp_stent_placed,
            "ercp_biliary_stent_type": self.ercp_biliary_stent_type,
            "ercp_stent_details": self.ercp_stent_details,
            "ercp_other_intervention": self.ercp_other_intervention,
            "ercp_fluoroscopy_time_minutes": self.ercp_fluoroscopy_time_minutes,
            "ercp_dose_area_product": self.ercp_dose_area_product,
            "ercp_reference_air_kerma": self.ercp_reference_air_kerma,
            "ercp_images_acquired": self.ercp_images_acquired,
            "ercp_dose_reduction_measures": self.ercp_dose_reduction_measures,
            "ercp_dose_reduction_other": self.ercp_dose_reduction_other,
            "ercp_intended_therapy": self.ercp_intended_therapy,
            "ercp_technical_success": self.ercp_technical_success,
            "ercp_stone_clearance": self.ercp_stone_clearance,
            "ercp_biliary_drainage_outcome": self.ercp_biliary_drainage_outcome,
            "ercp_immediate_adverse_event": self.ercp_immediate_adverse_event,
            "ercp_temporary_stent": self.ercp_temporary_stent,
            "ercp_removal_exchange_due": _to_api_date(self.ercp_removal_exchange_due),
            "ercp_pd_stent": self.ercp_pd_stent,
            "ercp_migration_passage_check": self.ercp_migration_passage_check,
            "ercp_patient_contact_note": self.ercp_patient_contact_note,
            "ercp_tracking_register_entered": self.ercp_tracking_register_entered,
            "ercp_repeat_intervention": self.ercp_repeat_intervention,
            "ercp_repeat_intervention_timing": self.ercp_repeat_intervention_timing,
            "ercp_post_ercp_pancreatitis": self.ercp_post_ercp_pancreatitis,
            "ercp_significant_bleeding": self.ercp_significant_bleeding,
            "ercp_cholangitis_or_cholecystitis": self.ercp_cholangitis_or_cholecystitis,
            "ercp_unplanned_hospital_visit": self.ercp_unplanned_hospital_visit,
            "ercp_complication_note": self.ercp_complication_note,
            "ercp_impression": self.ercp_impression,
            "eus_route": self.eus_route,
            "eus_echoendoscope": self.eus_echoendoscope,
            "eus_intent": self.eus_intent,
            "eus_upper_esophagus": self.eus_upper_esophagus,
            "eus_upper_stomach": self.eus_upper_stomach,
            "eus_upper_duodenum": self.eus_upper_duodenum,
            "eus_pancreas_examined": self.eus_pancreas_examined,
            "eus_cbd_examined": self.eus_cbd_examined,
            "eus_gallbladder_examined": self.eus_gallbladder_examined,
            "eus_liver_examined": self.eus_liver_examined,
            "eus_adrenal_examined": self.eus_adrenal_examined,
            "eus_mediastinum_examined": self.eus_mediastinum_examined,
            "eus_nodes_examined": self.eus_nodes_examined,
            "eus_doppler_used": self.eus_doppler_used,
            "eus_relevant_anatomy_documented": self.eus_relevant_anatomy_documented,
            "eus_photo_anatomy": self.eus_photo_anatomy,
            "eus_technical_limitation": self.eus_technical_limitation,
            "eus_immediate_adverse_event_note": self.eus_immediate_adverse_event_note,
            "eus_regions_examined": self.eus_regions_examined,
            "eus_target_lesion_present": self.eus_target_lesion_present,
            "eus_target_location": self.eus_target_location,
            "eus_target_size_mm": self.eus_target_size_mm,
            "eus_echogenicity": self.eus_echogenicity,
            "eus_margins": self.eus_margins,
            "eus_vascular_relation": self.eus_vascular_relation,
            "eus_nodes_note": self.eus_nodes_note,
            "eus_image_reference": self.eus_image_reference,
            "eus_cancer_site": self.eus_cancer_site,
            "eus_staging_system": self.eus_staging_system,
            "eus_t_stage": self.eus_t_stage,
            "eus_n_stage": self.eus_n_stage,
            "eus_m_features": self.eus_m_features,
            "eus_vascular_invasion": self.eus_vascular_invasion,
            "eus_overall_stage": self.eus_overall_stage,
            "eus_management_implication": self.eus_management_implication,
            "eus_tissue_target": self.eus_tissue_target,
            "eus_approach": self.eus_approach,
            "eus_needle_type": self.eus_needle_type,
            "eus_needle_gauge": self.eus_needle_gauge,
            "eus_needle_design": self.eus_needle_design,
            "eus_fna_performed": self.eus_fna_performed,
            "eus_fnb_performed": self.eus_fnb_performed,
            "eus_passes_count": self.eus_passes_count,
            "eus_rose_status": self.eus_rose_status,
            "eus_mose_status": self.eus_mose_status,
            "eus_specimen_type": self.eus_specimen_type,
            "eus_container_labels": self.eus_container_labels,
            "eus_adequacy_status": self.eus_adequacy_status,
            "eus_adequacy_note": self.eus_adequacy_note,
            "eus_label_verified": self.eus_label_verified,
            "eus_complication_type": self.eus_complication_type,
            "eus_antibiotics_after_sampling": self.eus_antibiotics_after_sampling,
            "eus_intervention_procedure": self.eus_intervention_procedure,
            "eus_intervention_target_route": self.eus_intervention_target_route,
            "eus_device_stent": self.eus_device_stent,
            "eus_technical_success": self.eus_technical_success,
            "eus_clinical_plan": self.eus_clinical_plan,
            "eus_immediate_adverse_event": self.eus_immediate_adverse_event,
            "eus_impression": self.eus_impression,
            "eus_pathology_cytology_status": self.eus_pathology_cytology_status,
            "eus_followup_imaging_or_procedure": self.eus_followup_imaging_or_procedure,
            "eus_multidisciplinary_referral": self.eus_multidisciplinary_referral,
            "finalized_at": _to_api_datetime(self.finalized_at),
            "finalized_by_user_id": _user_identifier(self.finalized_by_user_id),
            "finalized_by_user_ref": self.finalized_by_user_ref,
            "template_version": self.template_version,
            "report_narrative_snapshot": self.report_narrative_snapshot,
            "pdf_asset_ref": self.pdf_asset_ref,
            "validation_summary": self.validation_summary,
            "payload_version": self.payload_version,
            "segment_exam": [
                {
                    "segment_name": segment.segment_name,
                    "normal": segment.normal,
                    "finding_note": segment.finding_note,
                    "photo_taken": segment.photo_taken,
                }
                for segment in self.segment_ids.sorted("sequence")
            ],
            "lesions": [
                {
                    "lesion_index": lesion.sequence,
                    "lesion_location": lesion.lesion_location,
                    "lesion_size_mm": lesion.lesion_size_mm,
                    "lesion_morphology": lesion.lesion_morphology,
                    "resection_method": lesion.resection_method,
                    "complete_resection": lesion.complete_resection,
                    "retrieved": lesion.retrieved,
                    "specimen_container_ref": lesion.specimen_container_ref,
                }
                for lesion in self.lesion_ids.sorted("sequence")
            ],
            "specimens": [
                {
                    "container_label": specimen.container_label,
                    "specimen_site": specimen.specimen_site,
                    "specimen_count": specimen.specimen_count,
                    "test_question": specimen.test_question,
                    "label_verified": specimen.label_verified,
                }
                for specimen in self.specimen_ids.sorted("sequence")
            ],
            "image_attachments": [
                image._serialize_for_clinical_api()
                for image in self.image_attachment_ids.sorted(lambda item: (item.uploaded_at or item.create_date or datetime.min, item.id))
            ],
            "followup_tasks": [
                {
                    "followup_task_id": task.external_task_id,
                    "task_type": task.task_type,
                    "task_owner_user_id": _user_identifier(task.task_owner_user_id),
                    "task_owner_user_ref": task.task_owner_user_ref,
                    "due_date": _to_api_date(task.due_date),
                    "task_status": task.task_status,
                    "resolution_note": task.resolution_note,
                    "closed_at": _to_api_datetime(task.closed_at),
                    "closed_by_user_id": _user_identifier(task.closed_by_user_id),
                    "closed_by_user_ref": task.closed_by_user_ref,
                }
                for task in self.task_ids.sorted("id")
            ],
        }

    def action_push_to_clinical_api(self):
        config = self._bridge_config()
        if not config["base_url"]:
            raise ValidationError("Clinical API Base URL is not configured in Odoo settings.")

        for record in self:
            payload = record._serialize_for_clinical_api()
            request_url = f"{config['base_url']}/api/odoo/cases/upsert-draft"
            request_headers = {"Content-Type": "application/json"}
            if config["api_key"]:
                request_headers["X-PhD-Ass-Api-Key"] = config["api_key"]

            body = json.dumps(payload).encode("utf-8")
            request_obj = urllib_request.Request(request_url, data=body, headers=request_headers, method="POST")

            try:
                with urllib_request.urlopen(request_obj, timeout=config["timeout"]) as response:
                    response_text = response.read().decode("utf-8")
                response_payload = json.loads(response_text) if response_text else {}
            except (urllib_error.URLError, urllib_error.HTTPError, json.JSONDecodeError) as exc:
                record.with_context(phd_ass_bridge_sync=True).write(
                    {
                        "sync_status": "sync_failed",
                        "last_sync_error": str(exc),
                    }
                )
                record._log_sync_event(
                    event_type="case_push",
                    status="error",
                    direction="odoo_to_api",
                    message=f"Failed to push draft case to the clinical API: {exc}",
                    payload_excerpt=_minimal_sync_excerpt(payload),
                )
                raise ValidationError(f"Clinical API push failed: {exc}")

            record.with_context(phd_ass_bridge_sync=True).write(
                {
                    "sync_status": "synced",
                    "last_sync_error": False,
                    "last_push_to_api_at": fields.Datetime.now(),
                    "last_synced_at": fields.Datetime.now(),
                    "clinical_payload_json": False,
                }
            )
            record._log_sync_event(
                event_type="case_push",
                status="success",
                direction="odoo_to_api",
                message="Draft case pushed from Odoo to the clinical API.",
                payload_version=response_payload.get("payloadVersion"),
                payload_excerpt=_minimal_sync_excerpt(payload),
            )
        return True

    def action_generate_report_preview(self):
        for record in self:
            if record.case_status == "finalized":
                raise ValidationError("Finalized cases must be reopened before a new preview can be generated.")
            errors = record._signoff_validation_errors()
            narrative = record._generate_narrative_snapshot()
            record.with_context(phd_ass_bridge_sync=True).write(
                {
                    "template_version": LOCAL_TEMPLATE_VERSION,
                    "report_narrative_snapshot": narrative,
                    "validation_summary": record._validation_summary_text(errors),
                    "sync_status": "draft_local",
                    "last_sync_error": False,
                }
            )
            record._log_audit_event(
                "report_preview_generated",
                payload={
                    "validation_errors": errors,
                    "template_version": LOCAL_TEMPLATE_VERSION,
                },
            )
        return True

    def action_mark_ready_for_signoff(self):
        for record in self:
            if record.case_status not in ("draft", "draft_reopened"):
                raise ValidationError("Only a draft or reopened case can be marked ready for sign-off.")
            errors = record._signoff_validation_errors()
            if errors:
                raise ValidationError(record._validation_summary_text(errors))
            record.with_context(phd_ass_bridge_sync=True).write(
                {
                    "case_status": "ready_for_signoff",
                    "template_version": LOCAL_TEMPLATE_VERSION,
                    "report_narrative_snapshot": record._generate_narrative_snapshot(),
                    "validation_summary": "Ready for sign-off.",
                    "sync_status": "draft_local",
                    "last_sync_error": False,
                }
            )
            record._log_audit_event(
                "ready_for_signoff_marked",
                payload={"template_version": LOCAL_TEMPLATE_VERSION},
            )
        return True

    def action_finalize_report(self):
        self._ensure_endoscopist_signoff_role()
        for record in self:
            if record.case_status != "ready_for_signoff":
                raise ValidationError("A case must be marked ready for sign-off before it can be finalized.")

            errors = record._signoff_validation_errors()
            if errors:
                raise ValidationError(record._validation_summary_text(errors))

            narrative = record._generate_narrative_snapshot()
            attachment = record._create_pdf_attachment(narrative)
            finalized_at = fields.Datetime.now()
            validation_summary = f"Finalized on {_to_api_datetime(finalized_at)} by {self.env.user.display_name}."
            record.with_context(phd_ass_bridge_sync=True).write(
                {
                    "case_status": "finalized",
                    "finalized_at": finalized_at,
                    "finalized_by_user_id": self.env.user.id,
                    "finalized_by_user_ref": self.env.user.display_name,
                    "template_version": LOCAL_TEMPLATE_VERSION,
                    "report_narrative_snapshot": narrative,
                    "pdf_attachment_id": attachment.id,
                    "pdf_asset_ref": f"/web/content/{attachment.id}?download=1",
                    "validation_summary": validation_summary,
                    "sync_status": "draft_local",
                    "last_sync_error": False,
                }
            )
            revision = record._create_final_revision()
            record._log_audit_event(
                "report_finalized",
                payload={
                    "revision_number": revision.revision_number,
                    "pdf_attachment_id": attachment.id,
                    "template_version": LOCAL_TEMPLATE_VERSION,
                    "followup_state": record.followup_state,
                },
            )
        return True

    def action_return_to_draft(self):
        self._ensure_return_to_draft_role()
        for record in self:
            if record.case_status == "finalized":
                raise ValidationError("Finalized cases must be reopened instead of returned to draft directly.")
            if record.case_status not in ("ready_for_signoff", "draft_reopened"):
                raise ValidationError("Only a ready or reopened case can be returned to draft.")
            record.sudo().with_context(phd_ass_bridge_sync=True).write(
                {
                    "case_status": "draft",
                    "validation_summary": False,
                    "sync_status": "draft_local",
                    "last_sync_error": False,
                }
            )
            record._log_audit_event("returned_to_draft")
        return True

    def action_open_reopen_wizard(self):
        self.ensure_one()
        self._ensure_reopen_role()
        if self.case_status != "finalized":
            raise ValidationError("Only finalized cases can be reopened.")
        return {
            "type": "ir.actions.act_window",
            "name": "Reopen Finalized Case",
            "res_model": "phd.ass.case.reopen.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("phd_ass_bridge.view_phd_ass_case_reopen_wizard_form").id,
            "target": "new",
            "context": {"default_case_id": self.id},
        }

    def _reopen_case(self, reason):
        self.ensure_one()
        self._ensure_reopen_role()
        if self.case_status != "finalized":
            raise ValidationError("Only finalized cases can be reopened.")
        if not reason:
            raise ValidationError("Enter a reopen reason before reopening a finalized case.")

        self.sudo().with_context(phd_ass_bridge_sync=True).write(
            {
                "case_status": "draft_reopened",
                "finalized_at": False,
                "finalized_by_user_id": False,
                "finalized_by_user_ref": False,
                "template_version": False,
                "report_narrative_snapshot": False,
                "pdf_attachment_id": False,
                "pdf_asset_ref": False,
                "validation_summary": "Case reopened for amendment.",
                "reopen_reason": reason,
                "reopened_at": fields.Datetime.now(),
                "reopened_by_user_id": self.env.user.id,
                "reopened_by_user_ref": self.env.user.display_name,
                "sync_status": "draft_local",
                "last_sync_error": False,
            }
        )
        self._log_audit_event(
            "report_reopened",
            reason=reason,
            payload={
                "revision_count": len(self.sudo().revision_ids),
                "reopened_by": self.env.user.display_name,
            },
        )

    def action_reopen_finalized_case(self):
        for record in self:
            record._reopen_case(record.reopen_reason)
        return True

    def _auto_push_if_enabled(self):
        if self.env.context.get("phd_ass_bridge_sync"):
            return
        config = self._bridge_config()
        if config["auto_push_on_save"]:
            self.action_push_to_clinical_api()

    def _mark_local_draft(self):
        self.sudo().with_context(phd_ass_bridge_sync=True).write(
            {
                "sync_status": "draft_local",
                "last_sync_error": False,
            }
        )

    def _log_sync_event(self, event_type, status, direction, message, payload_version=False, payload_excerpt=False):
        self.ensure_one()
        self.env["phd.ass.sync.event"].sudo().create(
            {
                "case_id": self.id,
                "event_type": event_type,
                "sync_direction": direction,
                "status": status,
                "payload_version": payload_version,
                "payload_excerpt": _to_text_json(_minimal_sync_excerpt(payload_excerpt)),
                "message": message,
            }
        )


class PhdAssCaseSegment(models.Model):
    _name = "phd.ass.case.segment"
    _description = "PhD-Ass Case Segment"
    _order = "sequence, id"

    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    segment_name = fields.Selection(SEGMENT_NAME_SELECTION, required=True)
    normal = fields.Boolean()
    finding_note = fields.Text()
    photo_taken = fields.Boolean()

    def write(self, vals):
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._ensure_case_editable()
        result = super().write(vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._mark_local_draft()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("phd_ass_bridge_sync"):
            records.mapped("case_id")._mark_local_draft()
        return records

    def unlink(self):
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases = self.mapped("case_id")
            cases._ensure_case_editable()
            result = super().unlink()
            cases._mark_local_draft()
            return result
        return super().unlink()


class PhdAssCaseLesion(models.Model):
    _name = "phd.ass.case.lesion"
    _description = "PhD-Ass Case Lesion"
    _order = "sequence, id"

    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    lesion_location = fields.Char()
    lesion_size_mm = fields.Integer()
    lesion_morphology = fields.Char()
    resection_method = fields.Char()
    complete_resection = fields.Boolean()
    retrieved = fields.Boolean()
    specimen_container_ref = fields.Char()

    def write(self, vals):
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._ensure_case_editable()
        result = super().write(vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._mark_local_draft()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("phd_ass_bridge_sync"):
            records.mapped("case_id")._mark_local_draft()
        return records

    def unlink(self):
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases = self.mapped("case_id")
            cases._ensure_case_editable()
            result = super().unlink()
            cases._mark_local_draft()
            return result
        return super().unlink()


class PhdAssCaseSpecimen(models.Model):
    _name = "phd.ass.case.specimen"
    _description = "PhD-Ass Case Specimen"
    _order = "sequence, id"

    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    container_label = fields.Char()
    specimen_site = fields.Char()
    specimen_count = fields.Integer()
    test_question = fields.Text()
    label_verified = fields.Boolean()

    def write(self, vals):
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._ensure_case_editable()
        result = super().write(vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._mark_local_draft()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("phd_ass_bridge_sync"):
            records.mapped("case_id")._mark_local_draft()
        return records

    def unlink(self):
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases = self.mapped("case_id")
            cases._ensure_case_editable()
            result = super().unlink()
            cases._mark_local_draft()
            return result
        return super().unlink()


class PhdAssCaseImage(models.Model):
    _name = "phd.ass.case.image"
    _description = "PhD-Ass Case Image"
    _order = "uploaded_at, id"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True)
    external_image_id = fields.Char(required=True, default=lambda self: f"img-{uuid.uuid4().hex[:12]}", index=True, copy=False)
    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade")
    file_name = fields.Char(required=True, default="case-image")
    image_file = fields.Binary(string="Image", attachment=True)
    content_type = fields.Char()
    caption = fields.Char()
    size_bytes = fields.Integer(readonly=True)
    uploaded_at = fields.Datetime(readonly=True)
    uploaded_by_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    uploaded_by_user_ref = fields.Char(readonly=True)

    _external_image_id_unique = models.Constraint(
        "unique(external_image_id)",
        "Case image ID must be unique.",
    )

    @api.depends("file_name", "caption", "external_image_id")
    def _compute_name(self):
        for record in self:
            record.name = record.caption or record.file_name or record.external_image_id

    def _prepare_image_vals(self, vals):
        prepared = dict(vals)
        existing_file_name = self.file_name if len(self) == 1 else False
        file_name = _safe_attachment_filename(prepared.get("file_name") or existing_file_name, fallback="case-image")
        prepared["file_name"] = file_name
        prepared["content_type"] = _guess_image_content_type(prepared.get("content_type") or (self.content_type if len(self) == 1 else False), file_name)

        if prepared.get("image_file"):
            prepared["size_bytes"] = _base64_payload_size(prepared.get("image_file"))
            prepared.setdefault("uploaded_at", fields.Datetime.now())
            prepared.setdefault("uploaded_by_user_id", self.env.user.id)
            prepared.setdefault("uploaded_by_user_ref", _user_reference(self.env.user))
        return prepared

    def _prepare_vals_from_payload(self, case_record, payload):
        file_name = _safe_attachment_filename(payload.get("file_name"), fallback="case-image")
        vals = {
            "external_image_id": payload.get("external_image_id") or payload.get("image_id"),
            "case_id": case_record.id,
            "file_name": file_name,
            "content_type": _guess_image_content_type(payload.get("content_type"), file_name),
            "caption": payload.get("caption"),
            "size_bytes": payload.get("size_bytes") or 0,
            "uploaded_at": _to_datetime_value(payload.get("uploaded_at")) or fields.Datetime.now(),
            "uploaded_by_user_id": _find_user_by_ref(
                self.env,
                payload.get("uploaded_by_user_id") or payload.get("uploaded_by_user_ref"),
            ).id
            or False,
            "uploaded_by_user_ref": payload.get("uploaded_by_user_ref") or payload.get("uploaded_by_user_id"),
        }
        if payload.get("content_base64"):
            vals["image_file"] = payload.get("content_base64")
            vals["size_bytes"] = vals["size_bytes"] or _base64_payload_size(payload.get("content_base64"))
        return vals

    def _asset_ref(self):
        self.ensure_one()
        if not self.image_file:
            return False
        return f"/web/content/phd.ass.case.image/{self.id}/image_file/{quote(self.file_name or self.name or 'case-image')}?download=false"

    def _serialize_for_clinical_api(self):
        self.ensure_one()
        return {
            "external_image_id": self.external_image_id,
            "file_name": self.file_name,
            "content_type": _guess_image_content_type(self.content_type, self.file_name),
            "caption": self.caption,
            "size_bytes": self.size_bytes,
            "uploaded_at": _to_api_datetime(self.uploaded_at),
            "uploaded_by_user_id": _user_identifier(self.uploaded_by_user_id),
            "uploaded_by_user_ref": self.uploaded_by_user_ref,
            "asset_ref": self._asset_ref(),
        }

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        for vals in vals_list:
            draft_vals = self.browse()._prepare_image_vals(vals)
            draft_vals.setdefault("external_image_id", f"img-{uuid.uuid4().hex[:12]}")
            draft_vals.setdefault("uploaded_at", fields.Datetime.now())
            draft_vals.setdefault("uploaded_by_user_id", self.env.user.id)
            draft_vals.setdefault("uploaded_by_user_ref", _user_reference(self.env.user))
            prepared_vals.append(draft_vals)

        records = super().create(prepared_vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            records.mapped("case_id")._ensure_case_editable()
            for record in records:
                record.case_id._log_audit_event(
                    "case_image_attached",
                    entity_type="case_image",
                    entity_ref=record.external_image_id,
                    payload={
                        "file_name": record.file_name,
                        "content_type": record.content_type,
                        "size_bytes": record.size_bytes,
                        "has_caption": bool(record.caption),
                    },
                )
            records.mapped("case_id")._mark_local_draft()
        return records

    def write(self, vals):
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._ensure_case_editable()
        result = super().write(self._prepare_image_vals(vals))
        if not self.env.context.get("phd_ass_bridge_sync"):
            self.mapped("case_id")._mark_local_draft()
        return result

    def unlink(self):
        cases = self.mapped("case_id")
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases._ensure_case_editable()
            for record in self:
                record.case_id._log_audit_event(
                    "case_image_removed",
                    entity_type="case_image",
                    entity_ref=record.external_image_id,
                    payload={
                        "file_name": record.file_name,
                        "content_type": record.content_type,
                        "size_bytes": record.size_bytes,
                    },
                )
        result = super().unlink()
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases._mark_local_draft()
        return result


class PhdAssFollowupTask(models.Model):
    _name = "phd.ass.followup.task"
    _description = "PhD-Ass Follow-Up Task"
    _order = "due_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(compute="_compute_name", store=True)
    external_task_id = fields.Char(required=True, default=lambda self: str(uuid.uuid4()), index=True, copy=False)
    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade")
    task_type = fields.Selection(TASK_TYPE_SELECTION)
    task_owner_user_id = fields.Many2one("res.users", string="Task Owner", domain=[("share", "=", False)])
    task_owner_user_ref = fields.Char()
    due_date = fields.Date(index=True)
    task_status = fields.Selection(TASK_STATUS_SELECTION, default="open", index=True)
    resolution_note = fields.Text()
    closed_at = fields.Datetime(readonly=True)
    closed_by_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    closed_by_user_ref = fields.Char(readonly=True)
    last_synced_at = fields.Datetime(readonly=True)

    _external_task_id_unique = models.Constraint(
        "unique(external_task_id)",
        "Follow-up task ID must be unique.",
    )

    @api.depends("task_type", "external_task_id")
    def _compute_name(self):
        labels = dict(TASK_TYPE_SELECTION)
        for record in self:
            record.name = labels.get(record.task_type, record.task_type) or record.external_task_id

    def _prepare_owner_vals(self, vals):
        prepared = dict(vals)
        user_model = self.env["res.users"].with_context(active_test=False)

        if "task_owner_user_id" in prepared:
            if prepared["task_owner_user_id"]:
                user = user_model.browse(prepared["task_owner_user_id"])
                prepared["task_owner_user_ref"] = _user_reference(user)
            else:
                prepared["task_owner_user_ref"] = prepared.get("task_owner_user_ref") or False
        elif "task_owner_user_ref" in prepared:
            user = _find_user_by_ref(self.env, prepared.get("task_owner_user_ref"))
            prepared["task_owner_user_id"] = user.id if user else False
            prepared["task_owner_user_ref"] = _user_reference(user) if user else prepared.get("task_owner_user_ref")

        return prepared

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals = []
        for vals in vals_list:
            draft_vals = self._prepare_owner_vals(vals)
            draft_vals.setdefault("external_task_id", str(uuid.uuid4()))
            draft_vals.setdefault("task_status", "open")
            prepared_vals.append(draft_vals)
        records = super().create(prepared_vals)
        if not self.env.context.get("phd_ass_bridge_sync"):
            for record in records:
                record.case_id._log_audit_event(
                    "followup_task_created",
                    entity_type="followup_task",
                    entity_ref=record.external_task_id,
                    payload={
                        "task_type": record.task_type,
                        "task_status": record.task_status,
                        "task_owner_assigned": bool(record.task_owner_user_id or record.task_owner_user_ref),
                    },
                )
            records.mapped("case_id")._mark_local_draft()
        return records

    def write(self, vals):
        prepared_vals = self._prepare_owner_vals(vals)
        if self.env.context.get("phd_ass_bridge_sync"):
            return super().write(prepared_vals)

        if "closed_by_user_id" in prepared_vals or "closed_by_user_ref" in prepared_vals or "last_synced_at" in prepared_vals:
            raise ValidationError("Task sync metadata is managed by the integration.")
        if prepared_vals.get("task_status") in {"closed", "cancelled"} and not prepared_vals.get("resolution_note") and any(not record.resolution_note for record in self):
            raise ValidationError("A resolution note is required when closing or cancelling a follow-up task.")

        previous_values = {
            record.id: {
                "task_owner_user_ref": record.task_owner_user_ref,
                "task_status": record.task_status,
                "resolution_note": record.resolution_note,
            }
            for record in self
        }
        result = super().write(prepared_vals)
        if any(record.task_status in {"closed", "cancelled"} and not record.closed_at for record in self):
            super(PhdAssFollowupTask, self.with_context(phd_ass_bridge_sync=True)).write(
                {
                    "closed_at": fields.Datetime.now(),
                    "closed_by_user_id": self.env.user.id,
                    "closed_by_user_ref": self.env.user.display_name,
                }
            )
        for record in self:
            previous = previous_values[record.id]
            if previous["task_owner_user_ref"] != record.task_owner_user_ref:
                record.case_id._log_audit_event(
                    "followup_task_reassigned",
                    entity_type="followup_task",
                    entity_ref=record.external_task_id,
                    payload={"task_owner_changed": True},
                )
            if previous["task_status"] != record.task_status and record.task_status in {"closed", "cancelled"}:
                record.case_id._log_audit_event(
                    "followup_task_closed",
                    entity_type="followup_task",
                    entity_ref=record.external_task_id,
                    payload={
                        "status": record.task_status,
                        "resolution_documented": bool(record.resolution_note),
                        "closed_by_user_id": _user_identifier(record.closed_by_user_id),
                    },
                )
        self.mapped("case_id")._mark_local_draft()
        return result

    def unlink(self):
        cases = self.mapped("case_id")
        if not self.env.context.get("phd_ass_bridge_sync"):
            for record in self:
                record.case_id._log_audit_event(
                    "followup_task_deleted",
                    entity_type="followup_task",
                    entity_ref=record.external_task_id,
                    payload={"task_type": record.task_type},
                )
        result = super().unlink()
        if not self.env.context.get("phd_ass_bridge_sync"):
            cases._mark_local_draft()
        return result

    @api.model
    def sync_from_payload(self, payload):
        payload = payload or {}
        external_task_id = payload.get("followup_task_id") or payload.get("task_id") or payload.get("external_task_id")
        if not external_task_id:
            raise ValidationError("The sync payload must include followup_task_id, task_id, or external_task_id.")

        external_case_id = payload.get("case_id") or payload.get("case_id_ref") or payload.get("external_case_id")
        case = self.env["phd.ass.case"].with_context(phd_ass_bridge_sync=True).search([("external_case_id", "=", external_case_id)], limit=1)
        if not case:
            raise ValidationError("The follow-up task payload references a case that does not exist in Odoo.")

        vals = {
            "external_task_id": external_task_id,
            "case_id": case.id,
            "task_type": payload.get("task_type"),
            "task_owner_user_ref": payload.get("task_owner_user_id") or payload.get("task_owner_user_ref"),
            "due_date": _to_date_value(payload.get("due_date")),
            "task_status": payload.get("task_status") or "open",
            "resolution_note": payload.get("resolution_note"),
            "closed_at": _to_datetime_value(payload.get("closed_at")),
            "closed_by_user_id": _find_user_by_ref(self.env, payload.get("closed_by_user_id") or payload.get("closed_by_user_ref")).id or False,
            "closed_by_user_ref": payload.get("closed_by_user_id") or payload.get("closed_by_user_ref"),
            "last_synced_at": fields.Datetime.now(),
        }
        vals = self._prepare_owner_vals(vals)

        sync_model = self.with_context(phd_ass_bridge_sync=True)
        record = sync_model.search([("external_task_id", "=", external_task_id)], limit=1)
        if record:
            record.write(vals)
        else:
            record = sync_model.create(vals)

        case._log_sync_event(
            event_type="task_sync",
            status="success",
            direction="api_to_odoo",
            message=f"Follow-up task {external_task_id} synchronized from the clinical API.",
            payload_excerpt=_minimal_sync_excerpt(payload),
        )
        return record


class PhdAssCaseReopenWizard(models.TransientModel):
    _name = "phd.ass.case.reopen.wizard"
    _description = "Reopen Finalized Case Wizard"

    case_id = fields.Many2one("phd.ass.case", required=True, readonly=True)
    reason = fields.Text(required=True)

    def action_confirm_reopen(self):
        self.ensure_one()
        self.case_id.with_user(self.env.user)._reopen_case(self.reason)
        return {"type": "ir.actions.act_window_close"}


class PhdAssCaseRevision(models.Model):
    _name = "phd.ass.case.revision"
    _description = "PhD-Ass Finalized Case Revision"
    _order = "revision_number desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name", store=True)
    case_id = fields.Many2one("phd.ass.case", required=True, ondelete="cascade", readonly=True)
    revision_number = fields.Integer(required=True, readonly=True)
    finalized_at = fields.Datetime(readonly=True)
    finalized_by_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    finalized_by_user_ref = fields.Char(readonly=True)
    template_version = fields.Char(readonly=True)
    report_narrative_snapshot = fields.Text(readonly=True)
    pdf_attachment_id = fields.Many2one("ir.attachment", readonly=True, ondelete="set null")
    pdf_asset_ref = fields.Char(readonly=True)
    snapshot_json = fields.Text(readonly=True)

    _case_revision_unique = models.Constraint(
        "unique(case_id, revision_number)",
        "Revision numbers must be unique per clinical case.",
    )

    @api.depends("case_id.name", "revision_number")
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.case_id.name or record.case_id.external_case_id} - Revision {record.revision_number}"


class PhdAssAuditEvent(models.Model):
    _name = "phd.ass.audit.event"
    _description = "PhD-Ass Audit Event"
    _order = "create_date desc, id desc"

    case_id = fields.Many2one("phd.ass.case", ondelete="cascade", readonly=True)
    actor_user_id = fields.Many2one("res.users", readonly=True, ondelete="set null")
    actor_role = fields.Char(readonly=True)
    event_type = fields.Char(required=True, readonly=True)
    entity_type = fields.Char(readonly=True)
    entity_ref = fields.Char(readonly=True)
    reason = fields.Text(readonly=True)
    payload_json = fields.Text(readonly=True)


class PhdAssSyncEvent(models.Model):
    _name = "phd.ass.sync.event"
    _description = "PhD-Ass Sync Event"
    _order = "create_date desc, id desc"

    case_id = fields.Many2one("phd.ass.case", ondelete="cascade", readonly=True)
    event_type = fields.Char(required=True, readonly=True)
    sync_direction = fields.Selection(
        [("api_to_odoo", "API to Odoo"), ("odoo_to_api", "Odoo to API")],
        default="api_to_odoo",
        required=True,
        readonly=True,
    )
    status = fields.Selection(
        [("success", "Success"), ("error", "Error")],
        default="success",
        required=True,
        readonly=True,
    )
    payload_version = fields.Char(readonly=True)
    message = fields.Text(readonly=True)
    payload_excerpt = fields.Text(readonly=True)
