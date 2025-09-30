from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShopifyImportExportWizard(models.TransientModel):
    _name = 'shopify.import.export.wizard'
    _description = 'Shopify Import/Export Wizard'

    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    operation = fields.Selection([
        ('import_products', 'Import Products'),
        ('export_products', 'Export Products'),
        ('import_orders', 'Import Orders'),
        ('import_customers', 'Import Customers'),
        ('sync_stock', 'Sync Stock'),
        ('sync_prices', 'Sync Prices'),
    ], required=True, string='Operation')

    # Product selection for export
    product_ids = fields.Many2many('product.product', string='Products to Export')
    export_all_products = fields.Boolean('Export All Products')

    # Order filters
    order_status = fields.Selection([
        ('any', 'Any'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ], default='any', string='Order Status')

    fulfillment_status = fields.Selection([
        ('any', 'Any'),
        ('fulfilled', 'Fulfilled'),
        ('partial', 'Partial'),
        ('unfulfilled', 'Unfulfilled')
    ], default='any', string='Fulfillment Status')

    # Date range
    from_date = fields.Datetime('From Date')
    to_date = fields.Datetime('To Date')

    # Options
    create_queue_job = fields.Boolean('Create Queue Job', default=True,
                                      help="Process in background using queue")

    @api.onchange('instance_id')
    def _onchange_instance_id(self):
        """Set default values when instance changes"""
        if not self.instance_id:
            return

        # Set defaults based on instance configuration
        if self.operation == 'import_orders' and not self.from_date:
            # Import orders from last sync
            if self.instance_id.last_sync:
                self.from_date = self.instance_id.last_sync

    def action_execute(self):
        """Execute the selected operation"""
        if not self.instance_id:
            raise UserError(_("Please select a Shopify instance"))

        if self.create_queue_job:
            return self._create_queue_job()
        else:
            return self._execute_immediate()

    def _create_queue_job(self):
        """Create a queue job for the operation"""
        job_data = self._prepare_job_data()

        queue_job = self.env['shopify.queue'].create({
            'name': f"{self.operation.replace('_', ' ').title()} - {fields.Datetime.now()}",
            'instance_id': self.instance_id.id,
            'operation': self.operation,
            'data': str(job_data),
            'state': 'queued',
            'priority': '2'
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operation Queued'),
                'message': _('Operation has been queued and will be processed shortly'),
                'type': 'success',
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'shopify.queue',
                    'res_id': queue_job.id,
                    'view_mode': 'form',
                },
            }
        }

    def _execute_immediate(self):
        """Execute operation immediately"""
        try:
            if self.operation == 'import_products':
                self.env['shopify.product'].import_from_shopify(self.instance_id)
            elif self.operation == 'export_products':
                self._export_products()
            elif self.operation == 'import_orders':
                self.env['shopify.order'].import_from_shopify(self.instance_id)
            elif self.operation == 'import_customers':
                self.env['shopify.customer'].import_from_shopify(self.instance_id)
            elif self.operation == 'sync_stock':
                self._sync_stock()
            elif self.operation == 'sync_prices':
                self._sync_prices()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Operation completed successfully'),
                    'type': 'success',
                }
            }

        except Exception as e:
            raise UserError(_("Operation failed: %s") % str(e))

    def _export_products(self):
        """Export products to Shopify"""
        if self.export_all_products:
            products = self.env['shopify.product'].search([
                ('instance_id', '=', self.instance_id.id)
            ])
        else:
            if not self.product_ids:
                raise UserError(_("Please select products to export"))

            # Find or create shopify product records
            products = self.env['shopify.product']
            for product in self.product_ids:
                shopify_product = self.env['shopify.product'].search([
                    ('product_id', '=', product.id),
                    ('instance_id', '=', self.instance_id.id)
                ], limit=1)

                if shopify_product:
                    products |= shopify_product
                else:
                    # Create new shopify product record
                    shopify_product = self.env['shopify.product'].create({
                        'name': product.name,
                        'shopify_id': '',
                        'instance_id': self.instance_id.id,
                        'product_id': product.id,
                        'template_id': product.product_tmpl_id.id
                    })
                    products |= shopify_product

        for product in products:
            product.export_to_shopify()

    def _sync_stock(self):
        """Sync stock levels"""
        products = self.env['shopify.product'].search([
            ('instance_id', '=', self.instance_id.id)
        ])

        for product in products:
            product.sync_stock_levels()

    def _sync_prices(self):
        """Sync prices"""
        products = self.env['shopify.product'].search([
            ('instance_id', '=', self.instance_id.id),
            ('sync_required', '=', True)
        ])

        for product in products:
            product.export_to_shopify()

    def _prepare_job_data(self):
        """Prepare data for queue job"""
        data = {}

        if self.operation == 'export_products':
            if self.export_all_products:
                data['export_all'] = True
            else:
                data['product_ids'] = self.product_ids.ids

        if self.operation == 'import_orders':
            if self.order_status != 'any':
                data['order_status'] = self.order_status
            if self.fulfillment_status != 'any':
                data['fulfillment_status'] = self.fulfillment_status
            if self.from_date:
                data['from_date'] = str(self.from_date)
            if self.to_date:
                data['to_date'] = str(self.to_date)

        return data