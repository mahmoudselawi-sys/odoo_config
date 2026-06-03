# BusinessChat Connector

Send Odoo events (customer invoices, sale orders, deliveries) to a
[BusinessChat](https://businesschat.io) webhook so your customers receive
automated WhatsApp messages when something important happens in Odoo.

> Module technical name: `whatsapp_invoice_webhook`
> Odoo version: **16.0**
> License: **LGPL-3**
> Author: **BusinessChat**

---

## What it does

When a configured event happens inside Odoo, the module POSTs a small JSON
payload to a webhook URL you control (typically a BusinessChat endpoint).
BusinessChat then turns that payload into a WhatsApp message to the customer.

Three events are supported out of the box:

| Event code               | Fires when                                         | Source model      |
| ------------------------ | -------------------------------------------------- | ----------------- |
| `invoice_posted`         | A customer invoice is posted (`action_post`)       | `account.move`    |
| `sale_order_confirmed`   | A sale order is confirmed (`action_confirm`)       | `sale.order`      |
| `delivery_done`          | An outgoing delivery is validated (`button_validate`) | `stock.picking` |

---

## Features

- **Three ready-to-use events** — invoice posted, sale order confirmed,
  delivery done.
- **Dynamic event table** — events are stored in a small `businesschat.event`
  model, so they can be enabled / disabled and re-configured at runtime.
- **Per-event URL override** — each event can target its own webhook URL.
- **Default URL fallback** — events with no URL fall back to a global
  default URL set in Settings.
- **Per-event enable / disable toggles** — turn an event off without
  uninstalling the module.
- **Safe duplicate protection** — each source record carries a
  `webhook_sent` flag so the same record never fires the same event twice.
- **Resilient sending** — webhook failures (timeout, 4xx/5xx, network
  errors) are caught, logged to the record's chatter, and never roll back
  the underlying business action.
- **Arabic translation** — Arabic localization is included
  (`i18n/ar.po`, `i18n/ar_001.po`).
- **Custom settings styling** — a small CSS bundle gives the BusinessChat
  settings page a clean, branded look.

---

## How it works

```
┌───────────────────────┐    action_post / action_confirm / button_validate
│  account.move         │ ─┐
│  sale.order           │ ─┼──► businesschat.event.get_active_event(code)
│  stock.picking        │ ─┘                 │
└───────────────────────┘                    │ enabled?
                                             ▼
                            ┌────────────────────────────────┐
                            │  businesschat.event            │
                            │  - name, code, url, enabled    │
                            │  - resolve_url() falls back to │
                            │    ir.config_parameter         │
                            └────────────────────────────────┘
                                             │
                                             ▼
                            ┌────────────────────────────────┐
                            │  webhook.mixin._wh_send(...)   │
                            │  POST JSON, 10s timeout        │
                            │  log result to record chatter  │
                            └────────────────────────────────┘
                                             │
                                             ▼
                                  Your BusinessChat webhook
```

Key components:

- **`businesschat.event`** — a tiny model that acts as a registry of
  events. Each row has a translatable `name`, a unique technical `code`,
  an optional per-event `url`, and an `enabled` flag.
- **`webhook.mixin`** — an `AbstractModel` that owns the `_wh_send`
  helper. All three event hooks call into it so HTTP transport,
  timeouts, and error logging live in one place.
- **`res.config.settings`** — extends the Odoo settings form with a
  *BusinessChat* page: a default URL field and an inline editable table
  of all `businesschat.event` rows.

---

## Requirements

- Odoo **16.0** (Community or Enterprise)
- Python `requests` (ships with Odoo)
- The following Odoo modules are required and will be installed
  automatically as dependencies:
  - `account` — invoicing
  - `sale` — sale orders
  - `account_payment` — payment register / portal URL helpers
  - `stock` — deliveries

---

## Installation

### Option A — Odoo.sh (Git-based)

1. Push this folder (the `whatsapp_invoice_webhook` directory) to your
   Odoo.sh repository under the repo's addons path (usually the repo
   root).
2. Trigger a build on Odoo.sh (push to a tracked branch).
3. When the build is green, go to **Apps** in your Odoo.sh database,
   click **Update Apps List**, search for **BusinessChat Connector**,
   and click **Activate**.

### Option B — Self-hosted Odoo

1. Copy the `whatsapp_invoice_webhook` folder into your Odoo addons
   path, for example:
   ```bash
   cp -r whatsapp_invoice_webhook /path/to/odoo/addons/
   ```
   Or mount it via `docker-compose` (`./addons:/mnt/extra-addons`).
2. Restart Odoo so it picks up the new module.
3. In the Odoo web UI, go to **Apps → Update Apps List**.
4. Search for **BusinessChat Connector** and click **Install**.

---

## Configuration

After installation:

1. Go to **Settings → BusinessChat**.
2. Set the **Default Webhook URL** — this is used by any event that
   does not have its own URL.
3. In the **Events** table, you'll see three rows pre-installed
   (Invoice, Sale Order, Delivery Feedback), each disabled by default:
   - Toggle **Enabled** to start sending that event.
   - Optionally fill the **Webhook URL** column to override the default
     URL for that specific event.
4. Save.

That's it — the next time the matching business action fires, the
configured webhook will receive the payload.

---

## Webhook payload reference

All payloads are sent as `POST` requests with `Content-Type: application/json`.

### `invoice_posted`

```json
{
  "event_type":     "invoice_posted",
  "invoice_id":     42,
  "invoice_number": "INV/2026/00042",
  "amount_total":   1250.0,
  "currency":       "SAR",
  "state":          "posted",
  "customer_name":  "Acme Trading",
  "customer_phone": "+9665XXXXXXXX",
  "customer_email": "billing@acme.example",
  "invoice_url":    "https://your-odoo.example/my/invoices/42?access_token=…"
}
```

### `sale_order_confirmed`

```json
{
  "event_type":     "sale_order_confirmed",
  "order_id":       17,
  "order_number":   "S00017",
  "amount_total":   860.0,
  "currency":       "SAR",
  "state":          "sale",
  "customer_name":  "Acme Trading",
  "customer_phone": "+9665XXXXXXXX",
  "customer_email": "billing@acme.example"
}
```

### `delivery_done`

```json
{
  "event_type":     "delivery_done",
  "picking_id":     9,
  "picking_number": "WH/OUT/00009",
  "origin":         "S00017",
  "state":          "done",
  "customer_name":  "Acme Trading",
  "customer_phone": "+9665XXXXXXXX",
  "customer_email": "billing@acme.example"
}
```

The HTTP client has a **10-second timeout**. Non-2xx responses,
timeouts and network errors are logged to the source record's chatter
and never roll back the business transaction.

---

## Notes & limitations

- **Delivery event needs the Inventory module** (`stock`) and a real
  storable product on the sale order — service-only orders never
  generate an outgoing picking, so no `delivery_done` event fires.
- **Only customer invoices** (`out_invoice`) fire `invoice_posted`.
  Credit notes (`out_refund`), vendor bills and journal entries are
  ignored.
- **Dedup is per record, per direction.** The `webhook_sent` flag on
  each record prevents the same record from sending the same event
  twice. It does **not** protect against duplicate sends caused by
  third-party automations triggering the same action method.
- **Translations.** The module ships both `i18n/ar.po` and
  `i18n/ar_001.po`. The two files are identical; `ar_001` is included
  because some Odoo deployments resolve the Arabic language to the
  `ar_001` locale code. If your installation only uses `ar`, you can
  safely ignore `ar_001.po`.
- **Webhook payloads are not signed.** If your receiver is exposed on
  the public internet, restrict access by IP or rotate the URL secret
  regularly — or extend `webhook.mixin._wh_send` to add an HMAC header.
- **Settings styling is Odoo 16-specific.** The CSS in
  `static/src/css/settings.css` targets internal Odoo class names and
  may need adjustment on future Odoo versions.

---

## License

This module is released under the **LGPL-3** license. See the
`__manifest__.py` for details.

## Author

**BusinessChat** — https://businesschat.io
