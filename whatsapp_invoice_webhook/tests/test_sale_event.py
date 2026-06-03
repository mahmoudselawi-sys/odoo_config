from unittest.mock import patch

from odoo.tests.common import SavepointCase

from odoo.addons.whatsapp_invoice_webhook.models.webhook_mixin import (
    WebhookMixin,
)


class TestSaleOrderEvent(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Acme Customer",
            "phone": "+966500000000",
            "email": "acme@example.com",
        })
        cls.product = cls.env["product.product"].create({
            "name": "Service Widget",
            "list_price": 100.0,
            "type": "service",
        })
        cls.event = cls.env.ref(
            "whatsapp_invoice_webhook.event_sale_order"
        )

    def _make_draft_order(self):
        return self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "price_unit": 75.0,
                "tax_id": [(6, 0, [])],
            })],
        })

    def test_sale_order_confirmed_uses_per_event_url(self):
        self.event.enabled = True
        self.event.url = "http://event.example/order"
        order = self._make_draft_order()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            order.action_confirm()
        send.assert_called_once()
        _, record, url, payload = send.call_args[0]
        self.assertEqual(record, order)
        self.assertEqual(url, "http://event.example/order")
        self.assertEqual(payload["event_type"], "sale_order_confirmed")
        self.assertEqual(payload["order_id"], order.id)
        self.assertEqual(payload["order_number"], order.name)
        self.assertEqual(payload["amount_total"], order.amount_total)
        self.assertEqual(payload["customer_name"], "Acme Customer")
        self.assertEqual(payload["customer_phone"], "+966500000000")
        self.assertEqual(payload["customer_email"], "acme@example.com")
        self.assertEqual(payload["state"], "sale")
        # success_label kwarg should be the order-specific one
        self.assertEqual(
            send.call_args[1].get("success_label"),
            "Order sent to BusinessChat",
        )

    def test_sale_order_confirmed_falls_back_to_default_url(self):
        self.event.enabled = True
        self.event.url = False
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp_invoice_webhook.url", "http://default.example/hook"
        )
        order = self._make_draft_order()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            order.action_confirm()
        _, _, url, _ = send.call_args[0]
        self.assertEqual(url, "http://default.example/hook")

    def test_sale_order_confirmed_silent_when_event_disabled(self):
        self.event.enabled = False
        order = self._make_draft_order()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            order.action_confirm()
        send.assert_not_called()

    def test_sale_order_skipped_when_webhook_sent_already_true(self):
        self.event.enabled = True
        self.event.url = "http://event.example/order"
        order = self._make_draft_order()
        order.webhook_sent = True
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            order.action_confirm()
        send.assert_not_called()
