from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import json
import base64
import hashlib
import hmac


class ShopifyInstance(models.Model):
    _name = 'shopify.instance'
    _description = 'Shopify Instance Configuration'
    _rec_name = 'name'

    name = fields.Char('Instance Name', required=True)
    shop_url = fields.Char('Shop URL', required=True, help="e.g., myshop.myshopify.com")
    api_key = fields.Char('API Key', required=True)
    api_secret = fields.Char('API Secret', required=True)
    access_token = fields.Char('Access Token')
    webhook_secret = fields.Char('Webhook Secret')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('connected', 'Connected'),
        ('error', 'Error')
    ], default='draft', string='Status')

    last_sync = fields.Datetime('Last Sync')
    is_active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    # Configuration
    auto_import_orders = fields.Boolean('Auto Import Orders', default=True)
    auto_import_products = fields.Boolean('Auto Import Products', default=False)
    auto_import_customers = fields.Boolean('Auto Import Customers', default=True)
    auto_sync_stock = fields.Boolean('Auto Sync Stock', default=True)
    auto_create_invoices = fields.Boolean('Auto Create Invoices', default=True)

    # Mapping
    warehouse_id = fields.Many2one('stock.warehouse', 'Default Warehouse')
    pricelist_id = fields.Many2one('product.pricelist', 'Default Pricelist')
    payment_term_id = fields.Many2one('account.payment.term', 'Default Payment Term')
    team_id = fields.Many2one('crm.team', 'Sales Team')

    # Counts
    product_count = fields.Integer('Products', compute='_compute_counts')
    order_count = fields.Integer('Orders', compute='_compute_counts')
    customer_count = fields.Integer('Customers', compute='_compute_counts')

    @api.depends('name')
    def _compute_counts(self):
        for record in self:
            record.product_count = self.env['shopify.product'].search_count([('instance_id', '=', record.id)])
            record.order_count = self.env['shopify.order'].search_count([('instance_id', '=', record.id)])
            record.customer_count = self.env['shopify.customer'].search_count([('instance_id', '=', record.id)])

    @api.constrains('shop_url')
    def _check_shop_url(self):
        for record in self:
            if record.shop_url and not record.shop_url.endswith('.myshopify.com'):
                raise ValidationError(_("Shop URL must end with '.myshopify.com'"))

    def create_shopify_instance(self):
        """Create a new Shopify instance"""
        if not self.shop_url or not self.api_key or not self.api_secret:
            raise UserError(_("Please provide Shop URL, API Key and API Secret"))

        self.validate_shopify_credentials()
        return True

    def validate_shopify_credentials(self):
        """Validate Shopify API credentials"""
        try:
            headers = {
                'X-Shopify-Access-Token': self.access_token or self.api_secret,
                'Content-Type': 'application/json'
            }

            url = f"https://{self.shop_url}/admin/api/2023-10/shop.json"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                shop_data = response.json()
                self.state = 'connected'
                return True
            else:
                self.state = 'error'
                raise ValidationError(_("Invalid credentials. Status: %s") % response.status_code)

        except Exception as e:
            self.state = 'error'
            raise ValidationError(_("Connection failed: %s") % str(e))

    def get_shopify_access_token(self):
        """Get OAuth access token"""
        # OAuth implementation would go here
        pass

    def test_shopify_connection(self):
        """Test connection to Shopify API"""
        try:
            self.validate_shopify_credentials()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Connection to Shopify successful!'),
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def setup_onboarding_panel(self):
        """Setup onboarding wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shopify Setup Wizard'),
            'res_model': 'shopify.onboarding.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_instance_id': self.id}
        }

    def configure_api_settings(self):
        """Configure API settings"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('API Settings'),
            'res_model': 'shopify.instance',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current'
        }

    def setup_webhooks(self):
        """Setup Shopify webhooks"""
        webhooks = [
            {'topic': 'orders/create', 'address': f'/shopify/webhook/order/create'},
            {'topic': 'orders/updated', 'address': f'/shopify/webhook/order/update'},
            {'topic': 'orders/cancelled', 'address': f'/shopify/webhook/order/cancel'},
            {'topic': 'orders/fulfilled', 'address': f'/shopify/webhook/order/fulfill'},
            {'topic': 'products/create', 'address': f'/shopify/webhook/product/create'},
            {'topic': 'products/update', 'address': f'/shopify/webhook/product/update'},
            {'topic': 'customers/create', 'address': f'/shopify/webhook/customer/create'},
            {'topic': 'refunds/create', 'address': f'/shopify/webhook/refund/create'},
        ]

        for webhook in webhooks:
            self._create_webhook(webhook['topic'], webhook['address'])

    def _create_webhook(self, topic, address):
        """Create individual webhook"""
        try:
            headers = {
                'X-Shopify-Access-Token': self.access_token or self.api_secret,
                'Content-Type': 'application/json'
            }

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            webhook_data = {
                'webhook': {
                    'topic': topic,
                    'address': f"{base_url}{address}",
                    'format': 'json'
                }
            }

            url = f"https://{self.shop_url}/admin/api/2023-10/webhooks.json"
            response = requests.post(url, headers=headers, json=webhook_data, timeout=30)

            if response.status_code == 201:
                self.env['shopify.log'].create({
                    'instance_id': self.id,
                    'operation': 'webhook_create',
                    'message': f"Webhook created for {topic}",
                    'status': 'success'
                })
            else:
                self.env['shopify.log'].create({
                    'instance_id': self.id,
                    'operation': 'webhook_create',
                    'message': f"Failed to create webhook for {topic}: {response.text}",
                    'status': 'error'
                })

        except Exception as e:
            self.env['shopify.log'].create({
                'instance_id': self.id,
                'operation': 'webhook_create',
                'message': f"Error creating webhook for {topic}: {str(e)}",
                'status': 'error'
            })

    def validate_webhook_signature(self, data, hmac_header):
        """Validate webhook signature"""
        if not self.webhook_secret:
            return False

        calculated_hmac = base64.b64encode(
            hmac.new(
                self.webhook_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(calculated_hmac, hmac_header)

    def action_sync_all(self):
        """Sync all data from Shopify"""
        # Create queue jobs for async processing
        queue_obj = self.env['shopify.queue']

        queue_obj.create({
            'name': f'Import Products - {fields.Datetime.now()}',
            'instance_id': self.id,
            'operation': 'import_products',
            'state': 'queued',
            'data': json.dumps({'instance_id': self.id}),
        })

        queue_obj.create({
            'name': f'Import Orders - {fields.Datetime.now()}',
            'instance_id': self.id,
            'operation': 'import_orders',
            'state': 'queued',
            'data': json.dumps({'instance_id': self.id}),
        })

        queue_obj.create({
            'name': f'Import Customers - {fields.Datetime.now()}',
            'instance_id': self.id,
            'operation': 'import_customers',
            'state': 'queued',
            'data': json.dumps({'instance_id': self.id}),
        })

        return True

    def import_shopify_products(self):
        """Import products from Shopify"""
        # Implementation will be in shopify_product model
        self.env['shopify.product'].import_from_shopify(self)

    def import_shopify_orders(self):
        """Import orders from Shopify"""
        # Implementation will be in shopify_order model
        self.env['shopify.order'].import_from_shopify(self)

    def import_shopify_customers(self):
        """Import customers from Shopify"""
        # Implementation will be in shopify_customer model
        self.env['shopify.customer'].import_from_shopify(self)

    @api.model
    def get_dashboard_stats(self):
        """Get dashboard statistics for all active instances"""
        active_instances = self.search([('is_active', '=', True)])

        ShopifyProduct = self.env['shopify.product']
        ShopifyOrder = self.env['shopify.order']
        ShopifyCustomer = self.env['shopify.customer']
        ShopifyQueue = self.env['shopify.queue']
        ShopifyLog = self.env['shopify.log']

        # Get counts
        total_products = ShopifyProduct.search_count([('instance_id', 'in', active_instances.ids)])
        total_orders = ShopifyOrder.search_count([('instance_id', 'in', active_instances.ids)])
        total_customers = ShopifyCustomer.search_count([('instance_id', 'in', active_instances.ids)])

        # Pending orders (not imported in Odoo)
        pending_orders = ShopifyOrder.search_count([
            ('instance_id', 'in', active_instances.ids),
            ('sale_order_id', '=', False)
        ])

        # Total revenue from paid orders
        paid_orders = ShopifyOrder.search([
            ('instance_id', 'in', active_instances.ids),
            ('financial_status', '=', 'paid')
        ])
        total_revenue = sum(paid_orders.mapped('total_price'))

        # Queue statistics
        queued_jobs = ShopifyQueue.search_count([('state', '=', 'queued')])
        failed_jobs = ShopifyQueue.search_count([('state', '=', 'failed')])

        # Recent errors (last 24h)
        from datetime import datetime, timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent_errors = ShopifyLog.search_count([
            ('status', '=', 'error'),
            ('create_date', '>=', yesterday)
        ])

        return {
            'total_products': total_products,
            'total_orders': total_orders,
            'total_customers': total_customers,
            'pending_orders': pending_orders,
            'total_revenue': total_revenue,
            'queued_jobs': queued_jobs,
            'failed_jobs': failed_jobs,
            'recent_errors': recent_errors,
        }

    @api.model
    def get_recent_orders(self, limit=5):
        """Get recent orders"""
        ShopifyOrder = self.env['shopify.order']

        orders = ShopifyOrder.search([
            ('instance_id.is_active', '=', True)
        ], order='shopify_created_at desc', limit=limit)

        result = []
        for order in orders:
            result.append({
                'name': order.name,
                'total_price': order.total_price,
                'financial_status': order.financial_status,
                'shopify_created_at': order.shopify_created_at.isoformat() if order.shopify_created_at else None,
            })

        return result

    @api.model
    def get_recent_logs(self, limit=10):
        """Get recent logs"""
        ShopifyLog = self.env['shopify.log']

        logs = ShopifyLog.search([], order='create_date desc', limit=limit)

        result = []
        for log in logs:
            result.append({
                'operation': log.operation,
                'status': log.status,
                'message': log.message,
                'create_date': log.create_date.isoformat() if log.create_date else None,
            })

        return result