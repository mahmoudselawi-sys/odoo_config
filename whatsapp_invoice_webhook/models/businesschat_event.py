from odoo import models, fields, api

DEFAULT_URL_KEY = "whatsapp_invoice_webhook.url"


class BusinessChatEvent(models.Model):
    _name = "businesschat.event"
    _description = "BusinessChat Event"
    _order = "name"

    name = fields.Char(string="Event", required=True, translate=True)
    code = fields.Char(string="Technical Code", required=True, index=True)
    # The URL carries customer data when triggered; restrict UI visibility
    # and ORM read/write to administrators only.
    url = fields.Char(string="Webhook URL", groups="base.group_system")
    enabled = fields.Boolean(string="Enabled", default=False)

    _sql_constraints = [
        ("code_unique", "unique(code)", "Each event code must be unique."),
    ]

    def resolve_url(self):
        self.ensure_one()
        # sudo() so the per-event URL is honoured when a non-admin user
        # (e.g. a salesperson confirming an order) triggers the webhook.
        # The field-level group hides the URL in the UI; it must not
        # disable per-event routing for non-admin triggers.
        url = self.sudo().url
        if url:
            return url
        return self.env["ir.config_parameter"].sudo().get_param(DEFAULT_URL_KEY)

    @api.model
    def get_active_event(self, code):
        event = self.search([("code", "=", code)], limit=1)
        if event and event.enabled:
            return event
        return self.browse()
