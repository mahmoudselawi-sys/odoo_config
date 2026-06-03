import logging
import requests

from odoo import models

_logger = logging.getLogger(__name__)

DEFAULT_URL_KEY = "whatsapp_invoice_webhook.url"


class WebhookMixin(models.AbstractModel):
    _name = "webhook.mixin"
    _description = "Reusable webhook sender for BusinessChat"

    def _wh_is_enabled(self, enable_key):
        # Enabled ONLY if the value is explicitly "1" or "True".
        # Missing/deleted/empty/"0"/"False" -> disabled (safe default).
        value = self.env["ir.config_parameter"].sudo().get_param(enable_key)
        if not value:
            return False
        return str(value).strip().lower() in ("1", "true")

    def _wh_get_url(self, specific_key):
        ICP = self.env["ir.config_parameter"].sudo()
        specific_url = ICP.get_param(specific_key)
        if specific_url:
            return specific_url
        return ICP.get_param(DEFAULT_URL_KEY)

    def _wh_send(self, record, url, payload, success_label="Sent to BusinessChat"):
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            record.message_post(
                body="%s | HTTP %s" % (success_label, response.status_code)
            )
            return True
        except Exception as e:
            _logger.error("Webhook send failed: %s", e)
            record.message_post(body="Failed to send to BusinessChat: %s" % e)
            return False
