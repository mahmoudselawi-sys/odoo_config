from odoo import _, models, fields

EVENT_CODE = "invoice_posted"


class AccountMove(models.Model):
    _inherit = "account.move"

    webhook_sent = fields.Boolean(string="Webhook Sent", default=False, copy=False)

    def action_post(self):
        res = super().action_post()
        for record in self:
            if record.move_type != "out_invoice":
                continue
            if record.webhook_sent:
                continue
            record._send_invoice_webhook()
        return res

    def _send_invoice_webhook(self):
        self.ensure_one()
        event = self.env["businesschat.event"].get_active_event(EVENT_CODE)
        if not event:
            return
        url = event.resolve_url()
        if not url:
            return
        partner = self.partner_id
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        full_invoice_url = base_url + self.get_portal_url()
        payload = {
            "event_type": EVENT_CODE,
            "invoice_id": self.id,
            "invoice_number": self.name,
            "amount_total": self.amount_total,
            "currency": self.currency_id.name,
            "state": self.state,
            "customer_name": partner.name,
            "customer_phone": partner.phone or "",
            "customer_email": partner.email or "",
            "invoice_url": full_invoice_url,
        }
        self.env["webhook.mixin"]._wh_send(self, url, payload, success_label=_("Sent to BusinessChat"))
