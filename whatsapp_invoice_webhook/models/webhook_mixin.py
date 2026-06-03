import json
import logging
import os
import requests
import threading

import odoo
from odoo import _, api, models

_logger = logging.getLogger(__name__)

DEFAULT_URL_KEY = "whatsapp_invoice_webhook.url"

# ----------------------------------------------------------------------
# Tiny dependency-free .po reader used to resolve chatter strings.
#
# Odoo 14 reads code translations from the ir_translation table.
# Odoo 15/16 read them from an in-memory dict (odoo.tools.translate.
# code_translations) populated at module install/upgrade time. Both
# internal APIs are out of reach across the post-commit boundary — and
# differ across versions. To keep this module working identically on
# Odoo 14, 15 and 16 we parse the module's i18n/<lang>.po files
# ourselves once per process and look the chatter strings up in that
# dict before scheduling the post-commit callback.
# ----------------------------------------------------------------------
_PO_CACHE = {}                 # {lang: {msgid: msgstr}}
_PO_CACHE_LOCK = threading.Lock()


def _i18n_dir():
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "i18n",
    )


def _po_unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    # Unescape in two passes so '\\' doesn't grab the leading slash of
    # other escape sequences.
    return (s.replace(r"\\", "\x00")
             .replace(r'\"', '"')
             .replace(r"\n", "\n")
             .replace(r"\t", "\t")
             .replace("\x00", "\\"))


def _parse_po(path):
    out = {}
    cur_id, cur_str, mode = [], [], None

    def flush():
        if mode and cur_id:
            mid = "".join(cur_id)
            mstr = "".join(cur_str)
            if mid and mstr:
                out[mid] = mstr

    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    flush()
                    cur_id, cur_str, mode = [], [], None
                elif stripped.startswith("msgid "):
                    flush()
                    cur_id, cur_str, mode = [_po_unquote(stripped[6:])], [], "id"
                elif stripped.startswith("msgstr "):
                    cur_str, mode = [_po_unquote(stripped[7:])], "str"
                elif stripped.startswith('"'):
                    (cur_id if mode == "id" else cur_str).append(_po_unquote(stripped))
            flush()
    except OSError:
        pass
    return out


def _translations_for(lang):
    if lang in _PO_CACHE:
        return _PO_CACHE[lang]
    with _PO_CACHE_LOCK:
        if lang in _PO_CACHE:
            return _PO_CACHE[lang]
        merged = {}
        i18n = _i18n_dir()
        # Match Odoo 16's order: load the base lang first, then the
        # full lang (so e.g. ar_001 overrides ar where they differ).
        seen = set()
        for candidate in (lang.split("_")[0], lang):
            if candidate in seen:
                continue
            seen.add(candidate)
            merged.update(_parse_po(os.path.join(i18n, "%s.po" % candidate)))
        _PO_CACHE[lang] = merged
        return merged


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
        #
        # Resolve user-facing strings via our own .po cache (works
        # identically on Odoo 14/15/16). Doing the lookup here, before
        # scheduling, captures the right text on the closure and dodges
        # the post-commit language-loss problem.
        lang = self.env.context.get("lang") or self.env.user.lang or "en_US"
        T = _translations_for(lang)
        success_source = str(success_label)
        success_label = T.get(success_source, success_source)
        failure_template = T.get(
            "Failed to send to BusinessChat: %s",
            "Failed to send to BusinessChat: %s",
        )

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
                msg = failure_template % e
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
