from unittest.mock import patch

from odoo.tests.common import SavepointCase

from odoo.addons.whatsapp_invoice_webhook.models.webhook_mixin import (
    WebhookMixin,
)


class TestInvoiceEvent(SavepointCase):

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
        cls.event = cls.env.ref("whatsapp_invoice_webhook.event_invoice")

    def _make_draft_invoice(self):
        return self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "invoice_line_ids": [(0, 0, {
                "product_id": self.product.id,
                "quantity": 2,
                "price_unit": 50.0,
                "tax_ids": [(6, 0, [])],
            })],
        })

    def test_invoice_posted_uses_per_event_url(self):
        self.event.enabled = True
        self.event.url = "http://event.example/invoice"
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp_invoice_webhook.url", "http://default.example/hook"
        )
        invoice = self._make_draft_invoice()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            invoice.action_post()
        send.assert_called_once()
        # Positional args: (self_mixin, record, url, payload)
        _, record, url, payload = send.call_args[0]
        self.assertEqual(record, invoice)
        self.assertEqual(url, "http://event.example/invoice")
        self.assertEqual(payload["event_type"], "invoice_posted")
        self.assertEqual(payload["invoice_id"], invoice.id)
        self.assertEqual(payload["invoice_number"], invoice.name)
        self.assertEqual(payload["amount_total"], invoice.amount_total)
        self.assertEqual(payload["customer_name"], "Acme Customer")
        self.assertEqual(payload["customer_phone"], "+966500000000")
        self.assertEqual(payload["customer_email"], "acme@example.com")
        self.assertIn("invoice_url", payload)
        self.assertEqual(payload["state"], "posted")

    def test_invoice_posted_falls_back_to_default_url(self):
        self.event.enabled = True
        self.event.url = False
        self.env["ir.config_parameter"].sudo().set_param(
            "whatsapp_invoice_webhook.url", "http://default.example/hook"
        )
        invoice = self._make_draft_invoice()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            invoice.action_post()
        _, _, url, _ = send.call_args[0]
        self.assertEqual(url, "http://default.example/hook")

    def test_invoice_posted_silent_when_event_disabled(self):
        self.event.enabled = False
        self.event.url = "http://event.example/invoice"
        invoice = self._make_draft_invoice()
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            invoice.action_post()
        send.assert_not_called()

    def test_invoice_posted_skipped_when_webhook_sent_already_true(self):
        self.event.enabled = True
        self.event.url = "http://event.example/invoice"
        invoice = self._make_draft_invoice()
        # Mark as already sent before posting → action_post must skip our hook.
        invoice.webhook_sent = True
        with patch.object(WebhookMixin, "_wh_send", autospec=True) as send:
            invoice.action_post()
        send.assert_not_called()

    def test_invoice_posted_uses_invoice_posted_code(self):
        # Sanity-check that the constant moved into constants.py matches
        # the seed data file used by Odoo at install time.
        from odoo.addons.whatsapp_invoice_webhook.models import constants
        self.assertEqual(self.event.code, constants.EVENT_INVOICE_POSTED)
