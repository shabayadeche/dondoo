from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    phd_ass_clinical_api_base_url = fields.Char(
        string="Clinical API Base URL",
        config_parameter="phd_ass_bridge.clinical_api_base_url",
    )
    phd_ass_clinical_api_key = fields.Char(
        string="Clinical API Service Key",
        config_parameter="phd_ass_bridge.clinical_api_key",
    )
    phd_ass_request_timeout_seconds = fields.Integer(
        string="Clinical API Timeout Seconds",
        default=10,
        config_parameter="phd_ass_bridge.request_timeout_seconds",
    )
    phd_ass_auto_push_on_save = fields.Boolean(
        string="Auto Push Drafts On Save",
        config_parameter="phd_ass_bridge.auto_push_on_save",
    )
