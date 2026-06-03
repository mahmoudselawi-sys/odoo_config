from odoo import _, models, fields

EVENT_CODE = "delivery_done"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    webhook_sent = fields.Boolean(string="Webhook Sent", default=False, copy=False)

    def button_validate(self):
        res = super().button_validate()
        for record in self:
            if record.picking_type_id.code != "outgoing":
                continue
            if record.state != "done":
                continue
            if record.webhook_sent:
                continue
            record._send_delivery_webhook()
        return res

    def _send_delivery_webhook(self):
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
            "picking_id": self.id,
            "picking_number": self.name,
            "origin": self.origin or "",
            "state": self.state,
            "customer_name": partner.name,
            "customer_phone": partner.phone or "",
            "customer_email": partner.email or "",
        }
        self.env["webhook.mixin"]._wh_send(self, url, payload, success_label=_("Delivery feedback sent to BusinessChat"))
