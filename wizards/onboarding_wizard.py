from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShopifyOnboardingWizard(models.TransientModel):
    _name = 'shopify.onboarding.wizard'
    _description = 'Shopify Onboarding Wizard'

    # Step management
    step = fields.Selection([
        ('credentials', 'API Credentials'),
        ('configuration', 'Configuration'),
        ('mapping', 'Mapping'),
        ('webhooks', 'Webhooks Setup')
    ], default='credentials', required=True)

    # Step 1: Credentials
    name = fields.Char('Instance Name', required=True)
    shop_url = fields.Char('Shop URL', required=True, help="e.g., myshop.myshopify.com")
    api_key = fields.Char('API Key')
    api_secret = fields.Char('API Secret', required=True)
    access_token = fields.Char('Access Token')

    # Step 2: Configuration
    auto_import_orders = fields.Boolean('Auto Import Orders', default=True)
    auto_import_products = fields.Boolean('Auto Import Products', default=False)
    auto_import_customers = fields.Boolean('Auto Import Customers', default=True)
    auto_sync_stock = fields.Boolean('Auto Sync Stock', default=True)
    auto_create_invoices = fields.Boolean('Auto Create Invoices', default=True)

    # Step 3: Mapping
    warehouse_id = fields.Many2one('stock.warehouse', 'Default Warehouse')
    pricelist_id = fields.Many2one('product.pricelist', 'Default Pricelist')
    payment_term_id = fields.Many2one('account.payment.term', 'Default Payment Term')
    team_id = fields.Many2one('crm.team', 'Sales Team')

    # Step 4: Webhooks
    setup_webhooks = fields.Boolean('Setup Webhooks', default=True)

    # Instance reference
    instance_id = fields.Many2one('shopify.instance', 'Instance')

    @api.constrains('shop_url')
    def _check_shop_url(self):
        for record in self:
            if record.shop_url and not record.shop_url.endswith('.myshopify.com'):
                raise ValidationError(_("Shop URL must end with '.myshopify.com'"))

    def action_next(self):
        """Move to next step"""
        if self.step == 'credentials':
            # Test connection before moving forward
            self._test_connection()
            self.step = 'configuration'
        elif self.step == 'configuration':
            self.step = 'mapping'
        elif self.step == 'mapping':
            self.step = 'webhooks'
        elif self.step == 'webhooks':
            return self.action_finish()

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_previous(self):
        """Move to previous step"""
        if self.step == 'webhooks':
            self.step = 'mapping'
        elif self.step == 'mapping':
            self.step = 'configuration'
        elif self.step == 'configuration':
            self.step = 'credentials'

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_finish(self):
        """Complete onboarding"""
        # Create or update instance
        if self.instance_id:
            self.instance_id.write(self._prepare_instance_vals())
        else:
            self.instance_id = self.env['shopify.instance'].create(self._prepare_instance_vals())

        # Setup webhooks if requested
        if self.setup_webhooks:
            self.instance_id.setup_webhooks()

        # Mark instance as connected
        self.instance_id.state = 'connected'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Setup Complete'),
                'message': _('Shopify instance configured successfully!'),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'shopify.instance',
                    'res_id': self.instance_id.id,
                    'view_mode': 'form',
                },
            }
        }

    def _test_connection(self):
        """Test API connection"""
        import requests

        try:
            headers = {
                'X-Shopify-Access-Token': self.access_token or self.api_secret,
                'Content-Type': 'application/json'
            }

            url = f"https://{self.shop_url}/admin/api/2023-10/shop.json"
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                raise ValidationError(
                    _("Connection failed. Status: %s\nResponse: %s") %
                    (response.status_code, response.text)
                )

        except Exception as e:
            raise ValidationError(_("Connection failed: %s") % str(e))

    def _prepare_instance_vals(self):
        """Prepare values for instance creation/update"""
        return {
            'name': self.name,
            'shop_url': self.shop_url,
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'access_token': self.access_token,
            'auto_import_orders': self.auto_import_orders,
            'auto_import_products': self.auto_import_products,
            'auto_import_customers': self.auto_import_customers,
            'auto_sync_stock': self.auto_sync_stock,
            'auto_create_invoices': self.auto_create_invoices,
            'warehouse_id': self.warehouse_id.id if self.warehouse_id else False,
            'pricelist_id': self.pricelist_id.id if self.pricelist_id else False,
            'payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'team_id': self.team_id.id if self.team_id else False,
            'is_active': True,
        }

    def action_test_connection(self):
        """Test connection action"""
        try:
            self._test_connection()
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