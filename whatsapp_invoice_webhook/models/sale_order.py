from odoo import _, models, fields

EVENT_CODE = "sale_order_confirmed"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    webhook_sent = fields.Boolean(string="Webhook Sent", default=False, copy=False)

    def action_confirm(self):
        res = super().action_confirm()
        for record in self:
            if record.webhook_sent:
                continue
            record._send_order_webhook()
        return res

    def _send_order_webhook(self):
        self.ensure_one()
        event = self.env["businesschat.event"].get_active_event(EVENT_CODE)
        if not event:
            return
        url = event.resolve_url()
        if not url:
            return
        partner = self.partner_id
        payload = {
            "event_type": EVENT_CODE,
            "order_id": self.id,
            "order_number": self.name,
            "amount_total": self.amount_total,
            "currency": self.currency_id.name,
            "state": self.state,
            "customer_name": partner.name,
            "customer_phone": partner.phone or "",
            "customer_email": partner.email or "",
        }
        self.env["webhook.mixin"]._wh_send(self, url, payload, success_label=_("Order sent to BusinessChat"))
