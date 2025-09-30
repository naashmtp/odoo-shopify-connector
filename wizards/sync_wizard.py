from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShopifySyncWizard(models.TransientModel):
    _name = 'shopify.sync.wizard'
    _description = 'Shopify Sync Wizard'

    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)

    # Sync options
    sync_products = fields.Boolean('Sync Products', default=True)
    sync_orders = fields.Boolean('Sync Orders', default=True)
    sync_customers = fields.Boolean('Sync Customers', default=True)
    sync_stock = fields.Boolean('Sync Stock Levels', default=False)

    # Advanced options
    force_update = fields.Boolean('Force Update All',
                                   help="Update all records even if not modified")
    use_queue = fields.Boolean('Use Queue', default=True,
                               help="Process sync operations in background queue")

    # Statistics (readonly)
    product_count = fields.Integer('Products to Sync', compute='_compute_counts')
    order_count = fields.Integer('Orders to Sync', compute='_compute_counts')
    customer_count = fields.Integer('Customers to Sync', compute='_compute_counts')

    @api.depends('instance_id', 'sync_products', 'sync_orders', 'sync_customers')
    def _compute_counts(self):
        """Compute estimated counts for sync"""
        for wizard in self:
            wizard.product_count = 0
            wizard.order_count = 0
            wizard.customer_count = 0

            if not wizard.instance_id:
                continue

            if wizard.sync_products:
                wizard.product_count = self.env['shopify.product'].search_count([
                    ('instance_id', '=', wizard.instance_id.id)
                ])

            if wizard.sync_orders:
                wizard.order_count = self.env['shopify.order'].search_count([
                    ('instance_id', '=', wizard.instance_id.id),
                    ('imported', '=', False)
                ])

            if wizard.sync_customers:
                wizard.customer_count = self.env['shopify.customer'].search_count([
                    ('instance_id', '=', wizard.instance_id.id),
                    ('imported', '=', False)
                ])

    def action_sync_all(self):
        """Sync all selected data"""
        if not any([self.sync_products, self.sync_orders, self.sync_customers, self.sync_stock]):
            raise UserError(_("Please select at least one sync option"))

        if self.use_queue:
            return self._sync_with_queue()
        else:
            return self._sync_immediate()

    def _sync_with_queue(self):
        """Create queue jobs for sync operations"""
        jobs = []

        if self.sync_products:
            job = self.env['shopify.queue'].create({
                'name': f"Sync Products - {fields.Datetime.now()}",
                'instance_id': self.instance_id.id,
                'operation': 'import_products',
                'state': 'queued',
                'priority': '2'
            })
            jobs.append(job.id)

        if self.sync_orders:
            job = self.env['shopify.queue'].create({
                'name': f"Sync Orders - {fields.Datetime.now()}",
                'instance_id': self.instance_id.id,
                'operation': 'import_orders',
                'state': 'queued',
                'priority': '2'
            })
            jobs.append(job.id)

        if self.sync_customers:
            job = self.env['shopify.queue'].create({
                'name': f"Sync Customers - {fields.Datetime.now()}",
                'instance_id': self.instance_id.id,
                'operation': 'import_customers',
                'state': 'queued',
                'priority': '2'
            })
            jobs.append(job.id)

        if self.sync_stock:
            job = self.env['shopify.queue'].create({
                'name': f"Sync Stock - {fields.Datetime.now()}",
                'instance_id': self.instance_id.id,
                'operation': 'sync_stock',
                'state': 'queued',
                'priority': '2'
            })
            jobs.append(job.id)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Queued'),
                'message': _('%d sync job(s) have been queued') % len(jobs),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': _('Queue Jobs'),
                    'res_model': 'shopify.queue',
                    'domain': [('id', 'in', jobs)],
                    'view_mode': 'tree,form',
                },
            }
        }

    def _sync_immediate(self):
        """Execute sync immediately"""
        try:
            results = []

            if self.sync_products:
                self.env['shopify.product'].import_from_shopify(self.instance_id)
                results.append('Products synced')

            if self.sync_orders:
                self.env['shopify.order'].import_from_shopify(self.instance_id)
                results.append('Orders synced')

            if self.sync_customers:
                self.env['shopify.customer'].import_from_shopify(self.instance_id)
                results.append('Customers synced')

            if self.sync_stock:
                products = self.env['shopify.product'].search([
                    ('instance_id', '=', self.instance_id.id)
                ])
                for product in products:
                    product.sync_stock_levels()
                results.append('Stock levels synced')

            message = '\n'.join(results)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Complete'),
                    'message': message,
                    'type': 'success',
                }
            }

        except Exception as e:
            raise UserError(_("Sync failed: %s") % str(e))

    def action_sync_products_only(self):
        """Quick action to sync products only"""
        self.sync_products = True
        self.sync_orders = False
        self.sync_customers = False
        self.sync_stock = False
        return self.action_sync_all()

    def action_sync_orders_only(self):
        """Quick action to sync orders only"""
        self.sync_products = False
        self.sync_orders = True
        self.sync_customers = False
        self.sync_stock = False
        return self.action_sync_all()

    def action_sync_customers_only(self):
        """Quick action to sync customers only"""
        self.sync_products = False
        self.sync_orders = False
        self.sync_customers = True
        self.sync_stock = False
        return self.action_sync_all()