# Single source of truth for module-wide string constants.
#
# - Event codes are also referenced from data/businesschat_event_data.xml
#   as <field> values. XML cannot import Python, so the literals must
#   stay byte-identical there; the senders use these constants so a
#   typo in one Python file can no longer silently break one event.
# - DEFAULT_URL_KEY is the ir.config_parameter key for the fallback
#   webhook URL. It was duplicated in two model files; both now import
#   it from here.

EVENT_INVOICE_POSTED = "invoice_posted"
EVENT_SALE_ORDER_CONFIRMED = "sale_order_confirmed"
EVENT_DELIVERY_DONE = "delivery_done"

DEFAULT_URL_KEY = "whatsapp_invoice_webhook.url"
