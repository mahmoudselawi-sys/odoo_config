import json
import logging
import requests

import odoo
from odoo import api, models

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
        # Defer the HTTP POST until after the current transaction commits.
        # Rolled-back transactions therefore never produce a webhook, and the
        # user's Post / Confirm / Validate button returns immediately.
        record_model = record._name
        record_id = record.id
        dbname = self.env.cr.dbname
        uid = self.env.uid
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        def _do_send():
            try:
                response = requests.post(url, data=body, headers=headers, timeout=10)
                response.raise_for_status()
                ok = True
                msg = "%s | HTTP %s" % (success_label, response.status_code)
            except Exception as e:
                _logger.error("Webhook send failed: %s", e)
                ok = False
                msg = "Failed to send to BusinessChat: %s" % e
            # Fresh cursor: post-commit runs outside any transaction.
            with api.Environment.manage(), odoo.registry(dbname).cursor() as cr:
                env = api.Environment(cr, uid, {})
                rec = env[record_model].browse(record_id).exists()
                if rec:
                    rec.message_post(body=msg)
                    if ok:
                        rec.webhook_sent = True
                cr.commit()

        self.env.cr.postcommit.add(_do_send)
