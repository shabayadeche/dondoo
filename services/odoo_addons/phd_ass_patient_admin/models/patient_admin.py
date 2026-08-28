from odoo import api, fields, models
from odoo.exceptions import ValidationError


SEX_SELECTION = [
    ("female", "Female"),
    ("male", "Male"),
    ("intersex", "Intersex"),
    ("unknown", "Unknown"),
]

PATIENT_CASE_FIELDS = {"patient_id"}

RELATIONSHIP_TYPE_SELECTION = [
    ("primary_endoscopist", "Primary Endoscopist"),
    ("historical_endoscopist", "Historical Endoscopist"),
]


class PhdAssPatient(models.Model):
    _name = "phd.ass.patient"
    _description = "PhD-Ass Patient Registry"
    _rec_name = "name"
    _order = "patient_identifier, id desc"

    name = fields.Char(compute="_compute_name", store=True)
    patient_identifier = fields.Char(required=True, index=True)
    full_name = fields.Char()
    dob_or_age = fields.Char()
    sex = fields.Selection(SEX_SELECTION)
    medical_record_number = fields.Char(index=True)
    phone = fields.Char()
    email = fields.Char()
    notes = fields.Text()
    active = fields.Boolean(default=True)
    case_ids = fields.One2many("phd.ass.case", "patient_id", string="Clinical Cases")
    care_relationship_ids = fields.One2many(
        "phd.ass.patient.care.relationship", "patient_id", string="Endoscopist Assignments"
    )
    case_count = fields.Integer(compute="_compute_case_metrics")
    last_case_datetime = fields.Datetime(compute="_compute_case_metrics")

    _patient_identifier_unique = models.Constraint(
        "unique(patient_identifier)",
        "Patient identifier must be unique.",
    )

    @api.depends("full_name", "patient_identifier")
    def _compute_name(self):
        for record in self:
            record.name = record.full_name or record.patient_identifier

    @api.depends("case_ids", "case_ids.procedure_datetime")
    def _compute_case_metrics(self):
        for record in self:
            record.case_count = len(record.case_ids)
            record.last_case_datetime = max(record.case_ids.mapped("procedure_datetime")) if record.case_ids else False

    def action_open_cases(self):
        self.ensure_one()
        action = self.env.ref("phd_ass_bridge.action_phd_ass_cases").read()[0]
        action["domain"] = [("patient_id", "=", self.id)]
        action["context"] = {"default_patient_id": self.id}
        return action

    def action_assign_latest_endoscopist(self):
        if not (
            self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin")
            or self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")
        ):
            raise ValidationError("Only operations staff can migrate endoscopist assignments.")
        created = 0
        skipped = 0
        relationship_model = self.env["phd.ass.patient.care.relationship"]
        for patient in self:
            latest_case = patient.case_ids.filtered(lambda case: case.facility_id and case.endoscopist_user_id).sorted(
                key=lambda case: case.procedure_datetime or fields.Datetime.to_datetime("1970-01-01"), reverse=True
            )[:1]
            if not latest_case:
                skipped += 1
                continue
            current = relationship_model.search([
                ("patient_id", "=", patient.id),
                ("relationship_type", "=", "primary_endoscopist"),
                ("active", "=", True),
                ("is_primary", "=", True),
            ], limit=1)
            if current:
                skipped += 1
                continue
            relationship_model.create({
                "patient_id": patient.id,
                "facility_id": latest_case.facility_id.id,
                "facility_unit_id": latest_case.facility_unit_id.id or False,
                "endoscopist_user_id": latest_case.endoscopist_user_id.id,
                "relationship_type": "primary_endoscopist",
                "start_date": fields.Date.to_date(latest_case.procedure_datetime) or fields.Date.today(),
                "is_primary": True,
                "note": "Created from the most recent eligible clinical case; verify with the patient.",
            })
            created += 1
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Endoscopist assignments",
                "message": f"Created {created} assignment(s); skipped {skipped} patient(s).",
                "type": "success",
                "sticky": False,
            },
        }


class PhdAssPatientCareRelationship(models.Model):
    _name = "phd.ass.patient.care.relationship"
    _description = "Patient Facility Endoscopist Assignment"
    _order = "is_primary desc, start_date desc, id desc"
    _rec_name = "display_name"

    display_name = fields.Char(compute="_compute_display_name", store=True)
    patient_id = fields.Many2one("phd.ass.patient", required=True, ondelete="cascade", index=True)
    facility_id = fields.Many2one("phd.ass.facility", required=True, ondelete="restrict", index=True)
    facility_unit_id = fields.Many2one("phd.ass.facility.unit", ondelete="restrict")
    endoscopist_user_id = fields.Many2one(
        "res.users", required=True, ondelete="restrict", index=True,
        domain=[("share", "=", False)],
    )
    relationship_type = fields.Selection(RELATIONSHIP_TYPE_SELECTION, required=True, default="primary_endoscopist", index=True)
    start_date = fields.Date(required=True, default=fields.Date.today, index=True)
    end_date = fields.Date(index=True)
    is_primary = fields.Boolean(default=True, index=True)
    active = fields.Boolean(default=True, index=True)
    note = fields.Text()

    @api.depends("patient_id.name", "facility_id.name", "endoscopist_user_id.display_name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = " / ".join(
                part for part in (
                    record.patient_id.name,
                    record.facility_id.name,
                    record.endoscopist_user_id.display_name,
                ) if part
            ) or "Endoscopist assignment"

    @api.constrains("facility_id", "facility_unit_id", "endoscopist_user_id", "start_date", "end_date", "active", "is_primary", "relationship_type")
    def _check_assignment(self):
        endoscopist_group = self.env.ref("phd_ass_bridge.group_phd_ass_endoscopist", raise_if_not_found=False)
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError("End date cannot be earlier than start date.")
            if record.facility_unit_id and record.facility_unit_id.facility_id != record.facility_id:
                raise ValidationError("The selected unit must belong to the selected facility.")
            if endoscopist_group and endoscopist_group not in record.endoscopist_user_id.group_ids:
                raise ValidationError("The assigned user must have the Endoscopist workspace role.")
            if record.facility_id not in record.endoscopist_user_id.phd_ass_facility_ids:
                raise ValidationError("The endoscopist must have access to the selected facility.")
            if record.active and record.is_primary and record.relationship_type == "primary_endoscopist":
                duplicate = self.search([
                    ("id", "!=", record.id),
                    ("patient_id", "=", record.patient_id.id),
                    ("relationship_type", "=", record.relationship_type),
                    ("is_primary", "=", True),
                    ("active", "=", True),
                    "|", ("end_date", "=", False), ("end_date", ">=", fields.Date.today()),
                    ("start_date", "<=", fields.Date.today()),
                ], limit=1)
                if duplicate:
                    raise ValidationError("A patient can have only one current primary endoscopist assignment.")


class PhdAssCase(models.Model):
    _inherit = "phd.ass.case"

    patient_id = fields.Many2one("phd.ass.patient", string="Patient Registry Record", ondelete="restrict", index=True)
    patient_registry_name = fields.Char(related="patient_id.full_name", string="Patient Full Name", readonly=True)
    patient_registry_mrn = fields.Char(related="patient_id.medical_record_number", string="MRN", readonly=True)

    @api.onchange("patient_id")
    def _onchange_patient_id(self):
        for record in self.filtered("patient_id"):
            patient = record.patient_id
            record.patient_identifier = patient.patient_identifier
            record.sex = patient.sex or record.sex
            record.dob_or_age = patient.dob_or_age or record.dob_or_age

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("phd_ass_patient_registry_sync"):
            records._sync_patient_registry_from_case()
        return records

    def write(self, vals):
        target = self
        if not self.env.context.get("phd_ass_bridge_sync") and vals and set(vals).issubset(PATIENT_CASE_FIELDS):
            target = self.with_context(phd_ass_bridge_sync=True)
        result = super(PhdAssCase, target).write(vals)
        if not self.env.context.get("phd_ass_patient_registry_sync"):
            self._sync_patient_registry_from_case()
        return result

    def _sync_patient_registry_from_case(self):
        patient_model = self.env["phd.ass.patient"].sudo().with_context(active_test=False)
        for record in self:
            identifier = (record.patient_identifier or "").strip()
            if not identifier:
                continue

            patient = record.patient_id
            if not patient or patient.patient_identifier != identifier:
                patient = patient_model.search([("patient_identifier", "=", identifier)], limit=1)
            patient_vals = {
                "patient_identifier": identifier,
                "dob_or_age": record.dob_or_age or False,
                "sex": record.sex or False,
            }
            if not patient:
                patient = patient_model.create(patient_vals)
            else:
                updates = {}
                for field_name, value in patient_vals.items():
                    if value and patient[field_name] != value:
                        updates[field_name] = value
                if updates:
                    patient.write(updates)
            if record.patient_id != patient:
                record.with_context(phd_ass_bridge_sync=True, phd_ass_patient_registry_sync=True).write({"patient_id": patient.id})
