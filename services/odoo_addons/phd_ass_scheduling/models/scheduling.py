from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


SCHEDULE_STATE_SELECTION = [
    ("unscheduled", "Unscheduled"),
    ("scheduled", "Scheduled"),
    ("arrived", "Arrived"),
    ("in_room", "In Room"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("no_show", "No Show"),
]
PREP_STATE_SELECTION = [
    ("not_started", "Not Started"),
    ("in_progress", "In Progress"),
    ("ready", "Ready"),
    ("issue", "Issue"),
    ("completed", "Completed"),
]
SCHEDULING_CASE_FIELDS = {
    "schedule_state",
    "scheduled_start",
    "scheduled_end",
    "room_id",
    "prep_state",
    "check_in_at",
    "schedule_note",
    "arrival_note",
}


class PhdAssProcedureRoom(models.Model):
    _name = "phd.ass.procedure.room"
    _description = "PhD-Ass Procedure Room"
    _order = "facility_id, facility_unit_id, name"

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    facility_id = fields.Many2one("phd.ass.facility", string="Facility", required=True, ondelete="cascade")
    facility_unit_id = fields.Many2one("phd.ass.facility.unit", string="Unit", ondelete="set null")
    active = fields.Boolean(default=True)
    note = fields.Text()

    _room_code_unique = models.Constraint(
        "unique(code)",
        "Procedure room code must be unique.",
    )

    @api.constrains("facility_id", "facility_unit_id")
    def _check_facility_unit_alignment(self):
        for record in self:
            if record.facility_id and record.facility_unit_id and record.facility_unit_id.facility_id != record.facility_id:
                raise ValidationError("The selected procedure room unit must belong to the selected facility.")


class PhdAssCase(models.Model):
    _inherit = "phd.ass.case"

    schedule_state = fields.Selection(SCHEDULE_STATE_SELECTION, default="unscheduled", index=True)
    scheduled_start = fields.Datetime(index=True)
    scheduled_end = fields.Datetime()
    room_id = fields.Many2one("phd.ass.procedure.room", string="Procedure Room", ondelete="set null")
    prep_state = fields.Selection(PREP_STATE_SELECTION, default="not_started", index=True)
    check_in_at = fields.Datetime()
    schedule_note = fields.Text()
    arrival_note = fields.Text()

    @api.constrains("scheduled_start", "scheduled_end")
    def _check_schedule_window(self):
        for record in self:
            if record.scheduled_start and record.scheduled_end and record.scheduled_end < record.scheduled_start:
                raise ValidationError("Scheduled end time cannot be earlier than scheduled start time.")

    def write(self, vals):
        if not self.env.context.get("phd_ass_bridge_sync") and set(vals).intersection(SCHEDULING_CASE_FIELDS):
            if not (
                self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin")
                or self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")
            ):
                raise AccessError("Only operations staff can change procedure scheduling.")
        target = self
        if not self.env.context.get("phd_ass_bridge_sync") and vals and set(vals).issubset(SCHEDULING_CASE_FIELDS):
            target = self.with_context(phd_ass_bridge_sync=True)
        return super(PhdAssCase, target).write(vals)

    def _write_schedule_state(self, values):
        if not (
            self.env.user.has_group("phd_ass_bridge.group_phd_ass_operations_admin")
            or self.env.user.has_group("phd_ass_bridge.group_phd_ass_admin")
        ) and not self.env.context.get("phd_ass_bridge_sync"):
            raise AccessError("Only operations staff can change procedure scheduling.")
        previous_states = {record.id: record.schedule_state for record in self}
        self.with_context(phd_ass_bridge_sync=True).write(values)
        for record in self:
            if previous_states.get(record.id) != record.schedule_state:
                record._log_audit_event(
                    "schedule_state_changed",
                    entity_type="case_schedule",
                    payload={"from": previous_states.get(record.id), "to": record.schedule_state},
                )
        return True

    def action_mark_scheduled(self):
        return self._write_schedule_state({"schedule_state": "scheduled"})

    def action_mark_arrived(self):
        return self._write_schedule_state({"schedule_state": "arrived", "check_in_at": fields.Datetime.now()})

    def action_mark_in_room(self):
        return self._write_schedule_state({"schedule_state": "in_room"})

    def action_mark_schedule_complete(self):
        return self._write_schedule_state({"schedule_state": "completed"})

    def action_mark_no_show(self):
        return self._write_schedule_state({"schedule_state": "no_show"})

    def action_mark_schedule_cancelled(self):
        return self._write_schedule_state({"schedule_state": "cancelled"})

    def action_reset_schedule_state(self):
        return self._write_schedule_state({"schedule_state": "unscheduled", "check_in_at": False})
