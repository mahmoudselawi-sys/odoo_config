from odoo.tests.common import TransactionCase

from odoo.addons.whatsapp_invoice_webhook.models import webhook_mixin


class TestTranslationReader(TransactionCase):

    def setUp(self):
        super().setUp()
        webhook_mixin._PO_CACHE.clear()

    def test_po_unquote_strips_quotes(self):
        self.assertEqual(webhook_mixin._po_unquote('"hello"'), "hello")

    def test_po_unquote_handles_escapes(self):
        self.assertEqual(webhook_mixin._po_unquote(r'"a\nb"'), "a\nb")
        self.assertEqual(webhook_mixin._po_unquote(r'"a\"b"'), 'a"b')
        self.assertEqual(webhook_mixin._po_unquote(r'"a\\b"'), "a\\b")

    def test_translations_for_ar_has_chatter_strings(self):
        T = webhook_mixin._translations_for("ar")
        self.assertIn("Sent to BusinessChat", T)
        self.assertEqual(
            T["Sent to BusinessChat"], "تم الإرسال إلى BusinessChat"
        )
        self.assertEqual(
            T["Order sent to BusinessChat"],
            "تم إرسال الطلب إلى BusinessChat",
        )
        self.assertEqual(
            T["Delivery feedback sent to BusinessChat"],
            "تم إرسال إشعار التسليم إلى BusinessChat",
        )
        self.assertEqual(
            T["Failed to send to BusinessChat: %s"],
            "فشل الإرسال إلى BusinessChat: %s",
        )

    def test_translations_for_ar_001_inherits_from_ar_base(self):
        T = webhook_mixin._translations_for("ar_001")
        # ar_001.po is byte-identical to ar.po — both load, both contribute.
        self.assertIn("Sent to BusinessChat", T)
        self.assertIn("Delivery Feedback", T)

    def test_translations_for_unknown_lang_returns_empty(self):
        T = webhook_mixin._translations_for("xx_YY")
        self.assertEqual(T, {})

    def test_translations_for_caches_result(self):
        T1 = webhook_mixin._translations_for("ar")
        T2 = webhook_mixin._translations_for("ar")
        self.assertIs(T1, T2)
