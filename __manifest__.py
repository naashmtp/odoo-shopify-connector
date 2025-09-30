{
    'name': 'Shopify Integration',
    'version': '16.0.1.0.0',
    'category': 'Sales/E-commerce',
    'summary': 'Complete Shopify integration for Odoo',
    'description': """
        Complete Shopify Integration
        ===========================

        This module provides complete integration with Shopify e-commerce platform:

        * Multi-store management
        * Products sync (import/export with variants, images, prices)
        * Orders import and management
        * Customers synchronization
        * Stock synchronization
        * Payment and refunds management
        * Webhooks support
        * Automated workflows
        * Queue management
        * Reports and analytics

        Features:
        - OAuth authentication
        - Real-time webhooks
        - Bulk operations
        - Error handling and logging
        - Multi-warehouse support
        - Multi-currency support
    """,
    'author': 'Your Company',
    'website': 'https://github.com/naashmtp/odoo-shopify-connector',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'sale',
        'stock',
        'account',
        'payment',
        'website',
        'queue_job',
    ],
    'external_dependencies': {
        'python': ['requests', 'shopifyapi'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_cron.xml',
        'data/queue_job.xml',
        'views/shopify_instance_views.xml',
        'views/shopify_product_views.xml',
        'views/shopify_order_views.xml',
        'views/shopify_customer_views.xml',
        'views/shopify_log_views.xml',
        'views/shopify_queue_views.xml',
        'views/menu_views.xml',
        'wizards/onboarding_wizard_views.xml',
        'wizards/import_export_wizard_views.xml',
        'wizards/sync_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'shopify_integration/static/src/js/**/*',
            'shopify_integration/static/src/css/**/*',
        ],
    },
    'demo': [
        'data/demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 10,
    'images': ['static/description/banner.png'],
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}