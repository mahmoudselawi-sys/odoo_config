{
    'name': 'BusinessChat Connector',
    'version': '16.0.7.0.0',
    'summary': 'Send Odoo events (invoices, orders, deliveries) to BusinessChat via webhook',
    'description': 'Sends invoice, sale order and delivery events to configured webhook URLs (BusinessChat) for WhatsApp messaging, with a settings page and a dynamic events table.',
    'category': 'Tools',
    'author': 'BusinessChat',
    'website': 'https://businesschat.io',
    'license': 'LGPL-3',
    'depends': ['account', 'sale', 'account_payment', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/businesschat_event_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'whatsapp_invoice_webhook/static/src/css/settings.css',
        ],
    },
    'installable': True,
    'application': False,
}
