# odoo_config

BusinessChat Odoo 16 add-ons.

This repository is an Odoo addons folder. Each top-level subdirectory is a
standalone Odoo module that can be installed independently.

## Modules

| Module                      | Summary                                                                    |
| --------------------------- | -------------------------------------------------------------------------- |
| [`whatsapp_invoice_webhook`](whatsapp_invoice_webhook/README.md) | BusinessChat Connector — send Odoo invoice / sale / delivery events to a webhook for WhatsApp messaging. |

## Using this repo as an Odoo addons path

### Odoo.sh
Point the project at this repository — Odoo.sh detects modules in the repo
root automatically.

### Self-hosted
Clone the repo and add it to your Odoo addons path:

```bash
git clone https://github.com/mahmoudselawi-sys/odoo_config.git
# then, in your odoo.conf:
# addons_path = /path/to/odoo/addons,/path/to/odoo_config
```

Or, with `docker-compose`, mount the repo as an addons folder:

```yaml
volumes:
  - ./odoo_config:/mnt/extra-addons
```

## License

Each module declares its own license in its `__manifest__.py`. The
`whatsapp_invoice_webhook` module is released under **LGPL-3**.

## Author

**BusinessChat** — https://businesschat.io
