from odoo import _, models, fields

from .constants import EVENT_DELIVERY_DONE as EVENT_CODE


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
        # Suppress partials: this picking generated a backorder, so only
        # part of the order shipped. The completing backorder picking
        # itself has no further backorders and will fire normally.
        if self.backorder_ids:
            return
        # Suppress returns / re-shipments: any move tied back to an
        # earlier outgoing move via origin_returned_move_id means this
        # is not a fresh delivery to the customer. The move-list field
        # is named move_ids on Odoo 16 and move_lines on Odoo 14/15.
        moves_field = "move_ids" if "move_ids" in self._fields else "move_lines"
        if any(self[moves_field].mapped("origin_returned_move_id")):
            return
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
