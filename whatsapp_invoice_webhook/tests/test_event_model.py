from odoo.tests.common import SavepointCase


class TestBusinessChatEvent(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Event = cls.env["businesschat.event"]
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.invoice_event = cls.env.ref(
            "whatsapp_invoice_webhook.event_invoice"
        )

    def test_resolve_url_uses_event_specific_url(self):
        self.invoice_event.url = "http://event-specific.example/hook"
        self.assertEqual(
            self.invoice_event.resolve_url(),
            "http://event-specific.example/hook",
        )

    def test_resolve_url_falls_back_to_default(self):
        self.invoice_event.url = False
        self.ICP.set_param(
            "whatsapp_invoice_webhook.url", "http://default.example/hook"
        )
        self.assertEqual(
            self.invoice_event.resolve_url(),
            "http://default.example/hook",
        )

    def test_resolve_url_returns_falsy_when_nothing_set(self):
        self.invoice_event.url = False
        self.ICP.set_param("whatsapp_invoice_webhook.url", "")
        self.assertFalse(self.invoice_event.resolve_url())

    def test_get_active_event_returns_event_when_enabled(self):
        self.invoice_event.enabled = True
        got = self.Event.get_active_event("invoice_posted")
        self.assertEqual(got, self.invoice_event)

    def test_get_active_event_returns_empty_when_disabled(self):
        self.invoice_event.enabled = False
        got = self.Event.get_active_event("invoice_posted")
        self.assertFalse(got)

    def test_get_active_event_returns_empty_when_code_missing(self):
        got = self.Event.get_active_event("no_such_event_code")
        self.assertFalse(got)

    def test_three_default_events_exist(self):
        codes = set(self.Event.search([]).mapped("code"))
        self.assertIn("invoice_posted", codes)
        self.assertIn("sale_order_confirmed", codes)
        self.assertIn("delivery_done", codes)
