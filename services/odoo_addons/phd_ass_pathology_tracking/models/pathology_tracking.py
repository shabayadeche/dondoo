from odoo import api, fields, models
from odoo.exceptions import ValidationError


PATHOLOGY_TRACKING_STATE_SELECTION = [
    ("collected", "Collected"),
    ("sent_to_lab", "Sent To Lab"),
    ("result_pending", "Result Pending"),
    ("result_received", "Result Received"),
    ("reviewed", "Reviewed"),
    ("closed", "Closed"),
]
PATHOLOGY_SPECIMEN_FIELDS = {
    "pathology_tracking_state",
    "sent_to_lab_at",
    "lab_accession_number",
    "result_received_at",
    "reviewed_at",
    "reviewed_by_user_id",
    "result_summary",
    "result_attachment_id",
    "pathology_note",
}
PATHOLOGY_TASK_FIELDS = {"specimen_id", "pathology_note"}


class PhdAssCase(models.Model):
    _inherit = "phd.ass.case"

    open_pathology_specimen_count = fields.Integer(compute="_compute_open_pathology_specimen_count")

    @api.depends("specimen_ids.pathology_tracking_state")
    def _compute_open_pathology_specimen_count(self):
        open_states = {"collected", "sent_to_lab", "result_pending", "result_received"}
        for record in self:
            record.open_pathology_specimen_count = len(record.specimen_ids.filtered(lambda specimen: specimen.pathology_tracking_state in open_states))

    def action_open_pathology_queue(self):
        self.ensure_one()
        action = self.env.ref("phd_ass_pathology_tracking.action_phd_ass_pathology_specimens").read()[0]
        action["domain"] = [("case_id", "=", self.id)]
        action["context"] = {"default_case_id": self.id}
        return action


class PhdAssCaseSpecimen(models.Model):
    _inherit = "phd.ass.case.specimen"

    pathology_tracking_state = fields.Selection(PATHOLOGY_TRACKING_STATE_SELECTION, default="collected", index=True)
    sent_to_lab_at = fields.Datetime()
    lab_accession_number = fields.Char(index=True)
    result_received_at = fields.Datetime()
    reviewed_at = fields.Datetime(readonly=True)
    reviewed_by_user_id = fields.Many2one("res.users", string="Reviewed By", readonly=True, ondelete="set null")
    result_summary = fields.Text()
    result_attachment_id = fields.Many2one("ir.attachment", string="Result Attachment", ondelete="set null")
    pathology_note = fields.Text()
    linked_task_ids = fields.One2many("phd.ass.followup.task", "specimen_id", string="Linked Tasks", readonly=True)

    def write(self, vals):
        target = self
        if not self.env.context.get("phd_ass_bridge_sync") and vals and set(vals).issubset(PATHOLOGY_SPECIMEN_FIELDS):
            target = self.with_context(phd_ass_bridge_sync=True)
        return super(PhdAssCaseSpecimen, target).write(vals)

    def action_mark_sent_to_lab(self):
        self.with_context(phd_ass_bridge_sync=True).write(
            {
                "pathology_tracking_state": "sent_to_lab",
                "sent_to_lab_at": fields.Datetime.now(),
            }
        )
        return True

    def action_mark_result_pending(self):
        self.with_context(phd_ass_bridge_sync=True).write({"pathology_tracking_state": "result_pending"})
        return True

    def action_mark_result_received(self):
        self.with_context(phd_ass_bridge_sync=True).write(
            {
                "pathology_tracking_state": "result_received",
                "result_received_at": fields.Datetime.now(),
            }
        )
        return True

    def action_mark_reviewed(self):
        self.with_context(phd_ass_bridge_sync=True).write(
            {
                "pathology_tracking_state": "reviewed",
                "reviewed_at": fields.Datetime.now(),
                "reviewed_by_user_id": self.env.user.id,
            }
        )
        return True

    def action_mark_pathology_closed(self):
        self.with_context(phd_ass_bridge_sync=True).write({"pathology_tracking_state": "closed"})
        return True


class PhdAssFollowupTask(models.Model):
    _inherit = "phd.ass.followup.task"

    specimen_id = fields.Many2one("phd.ass.case.specimen", string="Specimen", ondelete="set null")
    pathology_note = fields.Text()

    @api.constrains("case_id", "specimen_id")
    def _check_task_specimen_case_alignment(self):
        for record in self:
            if record.specimen_id and record.specimen_id.case_id != record.case_id:
                raise ValidationError("The selected specimen must belong to the same case as the follow-up task.")

    def write(self, vals):
        target = self
        if not self.env.context.get("phd_ass_bridge_sync") and vals and set(vals).issubset(PATHOLOGY_TASK_FIELDS):
            target = self.with_context(phd_ass_bridge_sync=True)
        return super(PhdAssFollowupTask, target).write(vals)
