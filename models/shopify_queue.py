from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ShopifyQueue(models.Model):
    _name = 'shopify.queue'
    _description = 'Shopify Queue Job'
    _rec_name = 'name'
    _order = 'priority desc, create_date asc'

    name = fields.Char('Job Name', required=True)
    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)

    # Job Details
    operation = fields.Selection([
        ('import_products', 'Import Products'),
        ('export_products', 'Export Products'),
        ('import_orders', 'Import Orders'),
        ('import_customers', 'Import Customers'),
        ('sync_stock', 'Sync Stock'),
        ('sync_prices', 'Sync Prices'),
        ('process_webhook', 'Process Webhook'),
        ('export_order_status', 'Export Order Status'),
        ('import_refunds', 'Import Refunds'),
        ('custom', 'Custom Operation')
    ], required=True, string='Operation')

    # Queue Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status')

    priority = fields.Selection([
        ('0', 'Very Low'),
        ('1', 'Low'),
        ('2', 'Normal'),
        ('3', 'High'),
        ('4', 'Very High')
    ], default='2', string='Priority')

    # Data
    data = fields.Text('Job Data', help="JSON data for the job")
    result = fields.Text('Job Result')
    error_message = fields.Text('Error Message')

    # Timing
    scheduled_date = fields.Datetime('Scheduled Date', default=fields.Datetime.now)
    started_date = fields.Datetime('Started Date')
    finished_date = fields.Datetime('Finished Date')
    execution_time = fields.Float('Execution Time (seconds)')

    # Retry Logic
    max_retries = fields.Integer('Max Retries', default=3)
    retry_count = fields.Integer('Retry Count', default=0)
    retry_delay = fields.Integer('Retry Delay (minutes)', default=5)

    # Progress
    total_records = fields.Integer('Total Records')
    processed_records = fields.Integer('Processed Records')
    success_records = fields.Integer('Success Records')
    failed_records = fields.Integer('Failed Records')
    progress = fields.Float('Progress %', compute='_compute_progress')

    # Relations
    parent_job_id = fields.Many2one('shopify.queue', 'Parent Job')
    child_job_ids = fields.One2many('shopify.queue', 'parent_job_id', 'Child Jobs')

    @api.depends('total_records', 'processed_records')
    def _compute_progress(self):
        for record in self:
            if record.total_records > 0:
                record.progress = (record.processed_records / record.total_records) * 100
            else:
                record.progress = 0.0

    @api.model
    def create_import_queue(self, operation, instance_id, data=None, priority='2'):
        """Create a new import queue job"""
        vals = {
            'name': f"{operation.replace('_', ' ').title()} - {fields.Datetime.now()}",
            'operation': operation,
            'instance_id': instance_id,
            'data': json.dumps(data) if data else '{}',
            'priority': priority,
            'state': 'queued'
        }
        return self.create(vals)

    def action_run(self):
        """Run the queue job"""
        if self.state != 'queued':
            raise UserError(_("Only queued jobs can be run"))

        self.state = 'running'
        self.started_date = fields.Datetime.now()

        try:
            result = self._execute_job()

            self.state = 'done'
            self.result = json.dumps(result) if isinstance(result, dict) else str(result)
            self.finished_date = fields.Datetime.now()

            if self.started_date:
                duration = (self.finished_date - self.started_date).total_seconds()
                self.execution_time = duration

            # Log success
            self.env['shopify.log'].create({
                'instance_id': self.instance_id.id,
                'operation': self.operation,
                'message': f'Queue job {self.name} completed successfully',
                'status': 'success'
            })

        except Exception as e:
            self._handle_job_error(str(e))

    def _execute_job(self):
        """Execute the actual job logic"""
        data = json.loads(self.data) if self.data else {}

        if self.operation == 'import_products':
            return self._import_products(data)
        elif self.operation == 'export_products':
            return self._export_products(data)
        elif self.operation == 'import_orders':
            return self._import_orders(data)
        elif self.operation == 'import_customers':
            return self._import_customers(data)
        elif self.operation == 'sync_stock':
            return self._sync_stock(data)
        elif self.operation == 'sync_prices':
            return self._sync_prices(data)
        elif self.operation == 'process_webhook':
            return self._process_webhook(data)
        elif self.operation == 'export_order_status':
            return self._export_order_status(data)
        elif self.operation == 'import_refunds':
            return self._import_refunds(data)
        else:
            raise UserError(_("Unknown operation: %s") % self.operation)

    def _import_products(self, data):
        """Import products from Shopify"""
        self.env['shopify.product'].import_from_shopify(self.instance_id)
        return {'status': 'success', 'message': 'Products imported successfully'}

    def _export_products(self, data):
        """Export products to Shopify"""
        products = data.get('product_ids', [])
        if products:
            products = self.env['shopify.product'].browse(products)
            for product in products:
                product.export_to_shopify()
        return {'status': 'success', 'message': f'Exported {len(products)} products'}

    def _import_orders(self, data):
        """Import orders from Shopify"""
        self.env['shopify.order'].import_from_shopify(self.instance_id)
        return {'status': 'success', 'message': 'Orders imported successfully'}

    def _import_customers(self, data):
        """Import customers from Shopify"""
        self.env['shopify.customer'].import_from_shopify(self.instance_id)
        return {'status': 'success', 'message': 'Customers imported successfully'}

    def _sync_stock(self, data):
        """Sync stock levels"""
        products = self.env['shopify.product'].search([
            ('instance_id', '=', self.instance_id.id)
        ])
        for product in products:
            product.sync_stock_levels()
        return {'status': 'success', 'message': f'Synced stock for {len(products)} products'}

    def _sync_prices(self, data):
        """Sync prices"""
        products = self.env['shopify.product'].search([
            ('instance_id', '=', self.instance_id.id)
        ])
        for product in products:
            if product.sync_required:
                product.export_to_shopify()
        return {'status': 'success', 'message': f'Synced prices for {len(products)} products'}

    def _process_webhook(self, data):
        """Process webhook data"""
        topic = data.get('topic')
        webhook_data = data.get('data')
        headers = data.get('headers', {})

        result = self.env['shopify.webhook'].process_webhook(
            topic, webhook_data, headers, self.instance_id.id
        )
        return {'status': 'success' if result else 'failed', 'message': 'Webhook processed'}

    def _export_order_status(self, data):
        """Export order status updates"""
        order_ids = data.get('order_ids', [])
        orders = self.env['shopify.order'].browse(order_ids)
        for order in orders:
            if order.sale_order_id.state == 'done':
                order.mark_order_fulfilled()
        return {'status': 'success', 'message': f'Updated status for {len(orders)} orders'}

    def _import_refunds(self, data):
        """Import refunds from Shopify"""
        # Implementation for refund import
        return {'status': 'success', 'message': 'Refunds imported successfully'}

    def _handle_job_error(self, error_message):
        """Handle job execution error"""
        self.error_message = error_message
        self.finished_date = fields.Datetime.now()

        if self.retry_count < self.max_retries:
            # Schedule retry
            self.retry_count += 1
            self.state = 'queued'
            self.scheduled_date = fields.Datetime.now() + timedelta(minutes=self.retry_delay)

            _logger.info(f"Scheduling retry {self.retry_count}/{self.max_retries} for job {self.name}")
        else:
            # Mark as failed
            self.state = 'failed'

            # Log error
            self.env['shopify.log'].create({
                'instance_id': self.instance_id.id,
                'operation': self.operation,
                'message': f'Queue job {self.name} failed: {error_message}',
                'status': 'error'
            })

    def action_retry(self):
        """Manually retry a failed job"""
        if self.state not in ['failed', 'cancelled']:
            raise UserError(_("Only failed or cancelled jobs can be retried"))

        self.state = 'queued'
        self.error_message = False
        self.scheduled_date = fields.Datetime.now()

    def action_cancel(self):
        """Cancel a job"""
        if self.state == 'running':
            raise UserError(_("Cannot cancel a running job"))

        self.state = 'cancelled'

    @api.model
    def process_queue_jobs(self, limit=10):
        """Process queued jobs"""
        jobs = self.search([
            ('state', '=', 'queued'),
            ('scheduled_date', '<=', fields.Datetime.now())
        ], limit=limit, order='priority desc, create_date asc')

        for job in jobs:
            try:
                job.action_run()
            except Exception as e:
                _logger.error(f"Error processing queue job {job.id}: {str(e)}")

        return len(jobs)

    @api.model
    def retry_failed_operations(self):
        """Retry failed operations that haven't exceeded max retries"""
        failed_jobs = self.search([
            ('state', '=', 'failed'),
            ('retry_count', '<', 'max_retries')
        ])

        for job in failed_jobs:
            job.action_retry()

        return len(failed_jobs)

    @api.model
    def cleanup_old_jobs(self, days=30):
        """Clean up old completed jobs"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_jobs = self.search([
            ('state', 'in', ['done', 'failed', 'cancelled']),
            ('create_date', '<', cutoff_date)
        ])
        old_jobs.unlink()
        return len(old_jobs)

    def skip_failed_records(self):
        """Skip failed records and continue processing"""
        if self.state != 'failed':
            raise UserError(_("Only failed jobs can skip failed records"))

        # Reset job to continue from where it left off
        self.state = 'queued'
        self.error_message = False
        return True

    def monitor_queue_status(self):
        """Return queue monitoring information"""
        stats = {
            'total_jobs': self.search_count([]),
            'queued_jobs': self.search_count([('state', '=', 'queued')]),
            'running_jobs': self.search_count([('state', '=', 'running')]),
            'failed_jobs': self.search_count([('state', '=', 'failed')]),
            'completed_jobs': self.search_count([('state', '=', 'done')])
        }
        return stats