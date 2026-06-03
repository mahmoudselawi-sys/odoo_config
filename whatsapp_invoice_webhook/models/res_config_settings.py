from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    wh_default_url = fields.Char(
        string="Default Webhook URL",
        config_parameter="whatsapp_invoice_webhook.url",
    )

    wh_event_ids = fields.One2many(
        "businesschat.event",
        compute="_compute_wh_event_ids",
        inverse="_inverse_wh_event_ids",
        string="BusinessChat Events",
    )

    @api.depends("company_id")
    def _compute_wh_event_ids(self):
        events = self.env["businesschat.event"].search([])
        for record in self:
            record.wh_event_ids = events

    def _inverse_wh_event_ids(self):
        return
