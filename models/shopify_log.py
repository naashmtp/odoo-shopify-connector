from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ShopifyLog(models.Model):
    _name = 'shopify.log'
    _description = 'Shopify Integration Log'
    _rec_name = 'operation'
    _order = 'create_date desc'

    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    operation = fields.Selection([
        ('connection_test', 'Connection Test'),
        ('webhook_create', 'Webhook Creation'),
        ('webhook_process', 'Webhook Processing'),
        ('product_import', 'Product Import'),
        ('product_export', 'Product Export'),
        ('order_import', 'Order Import'),
        ('order_export', 'Order Export'),
        ('customer_import', 'Customer Import'),
        ('customer_export', 'Customer Export'),
        ('stock_sync', 'Stock Sync'),
        ('price_sync', 'Price Sync'),
        ('refund_import', 'Refund Import'),
        ('refund_export', 'Refund Export'),
        ('queue_processing', 'Queue Processing'),
        ('api_request', 'API Request'),
        ('data_validation', 'Data Validation'),
        ('error_handling', 'Error Handling'),
        ('system', 'System Operation')
    ], required=True, string='Operation')

    status = fields.Selection([
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('debug', 'Debug')
    ], required=True, string='Status')

    message = fields.Text('Message', required=True)
    details = fields.Text('Details')

    # Request/Response data
    request_data = fields.Text('Request Data')
    response_data = fields.Text('Response Data')

    # Error details
    error_code = fields.Char('Error Code')
    error_trace = fields.Text('Error Traceback')

    # Performance metrics
    execution_time = fields.Float('Execution Time (ms)')
    memory_usage = fields.Float('Memory Usage (MB)')

    # Related records
    related_model = fields.Char('Related Model')
    related_record_id = fields.Integer('Related Record ID')

    # API details
    api_endpoint = fields.Char('API Endpoint')
    http_method = fields.Char('HTTP Method')
    http_status = fields.Integer('HTTP Status Code')

    # User context
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)

    @api.model
    def log_api_requests(self, instance_id, endpoint, method, request_data=None,
                        response_data=None, status_code=None, execution_time=None):
        """Log API requests"""
        status = 'success' if status_code and 200 <= status_code < 300 else 'error'

        self.create({
            'instance_id': instance_id,
            'operation': 'api_request',
            'status': status,
            'message': f'{method} {endpoint}',
            'api_endpoint': endpoint,
            'http_method': method,
            'http_status': status_code or 0,
            'request_data': json.dumps(request_data) if request_data else None,
            'response_data': json.dumps(response_data) if response_data else None,
            'execution_time': execution_time or 0
        })

    @api.model
    def log_operation(self, instance_id, operation, status, message, **kwargs):
        """Generic method to log operations"""
        vals = {
            'instance_id': instance_id,
            'operation': operation,
            'status': status,
            'message': message
        }

        # Add optional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                vals[key] = value

        return self.create(vals)

    @api.model
    def handle_api_errors(self, instance_id, operation, error, request_data=None):
        """Handle and log API errors"""
        error_message = str(error)

        # Extract error details if it's a requests exception
        status_code = getattr(error, 'response', {}).get('status_code', 0) if hasattr(error, 'response') else 0
        response_text = getattr(error, 'response', {}).get('text', '') if hasattr(error, 'response') else ''

        self.create({
            'instance_id': instance_id,
            'operation': operation,
            'status': 'error',
            'message': f'API Error: {error_message}',
            'error_code': str(status_code) if status_code else 'UNKNOWN',
            'details': response_text,
            'request_data': json.dumps(request_data) if request_data else None,
            'http_status': status_code
        })

    @api.model
    def create_mismatch_logs(self, instance_id, operation, mismatches):
        """Create logs for data mismatches"""
        for mismatch in mismatches:
            self.create({
                'instance_id': instance_id,
                'operation': operation,
                'status': 'warning',
                'message': f"Data mismatch: {mismatch.get('field')}",
                'details': f"Expected: {mismatch.get('expected')}, Got: {mismatch.get('actual')}",
                'related_model': mismatch.get('model'),
                'related_record_id': mismatch.get('record_id')
            })

    @api.model
    def log_webhook_processing(self, webhook_id, topic, status, message, data=None):
        """Log webhook processing"""
        webhook = self.env['shopify.webhook'].browse(webhook_id)

        self.create({
            'instance_id': webhook.instance_id.id,
            'operation': 'webhook_process',
            'status': status,
            'message': f'Webhook {topic}: {message}',
            'details': json.dumps(data) if data else None,
            'related_model': 'shopify.webhook',
            'related_record_id': webhook_id
        })

    @api.model
    def log_queue_processing(self, queue_id, status, message, execution_time=None):
        """Log queue job processing"""
        queue_job = self.env['shopify.queue'].browse(queue_id)

        self.create({
            'instance_id': queue_job.instance_id.id,
            'operation': 'queue_processing',
            'status': status,
            'message': f'Queue {queue_job.operation}: {message}',
            'execution_time': execution_time,
            'related_model': 'shopify.queue',
            'related_record_id': queue_id
        })

    @api.model
    def send_error_notifications(self, threshold=10, hours=1):
        """Send notifications for error threshold breaches"""
        cutoff_time = fields.Datetime.now() - timedelta(hours=hours)

        for instance in self.env['shopify.instance'].search([('is_active', '=', True)]):
            error_count = self.search_count([
                ('instance_id', '=', instance.id),
                ('status', '=', 'error'),
                ('create_date', '>=', cutoff_time)
            ])

            if error_count >= threshold:
                # Send notification to administrators
                self._send_error_notification(instance, error_count, hours)

    def _send_error_notification(self, instance, error_count, hours):
        """Send error notification"""
        # Create activity or send email
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
            'res_model': 'shopify.instance',
            'res_id': instance.id,
            'summary': f'High Error Rate Alert: {instance.name}',
            'note': f'{error_count} errors in the last {hours} hour(s) for instance {instance.name}. Please investigate.',
            'user_id': self.env.ref('base.user_admin').id
        })

    @api.model
    def trigger_scheduled_activities(self):
        """Trigger scheduled activities based on logs"""
        # Check for repeated failures
        instances = self.env['shopify.instance'].search([('is_active', '=', True)])

        for instance in instances:
            # Check for connection issues
            recent_connection_errors = self.search_count([
                ('instance_id', '=', instance.id),
                ('operation', '=', 'connection_test'),
                ('status', '=', 'error'),
                ('create_date', '>=', fields.Datetime.now() - timedelta(hours=24))
            ])

            if recent_connection_errors >= 5:
                # Create maintenance activity
                self.env['mail.activity'].create({
                    'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                    'res_model': 'shopify.instance',
                    'res_id': instance.id,
                    'summary': 'Connection Issues Detected',
                    'note': f'Multiple connection failures detected for {instance.name}. Please check API credentials and connection.',
                    'user_id': self.env.ref('base.user_admin').id
                })

    @api.model
    def generate_debug_logs(self, instance_id, operation, debug_data):
        """Generate debug logs with detailed information"""
        self.create({
            'instance_id': instance_id,
            'operation': operation,
            'status': 'debug',
            'message': f'Debug info for {operation}',
            'details': json.dumps(debug_data, indent=2) if isinstance(debug_data, dict) else str(debug_data)
        })

    @api.model
    def validate_data_integrity(self, instance_id):
        """Validate data integrity and log issues"""
        issues = []

        # Check for orphaned records
        orphaned_products = self.env['shopify.product'].search([
            ('instance_id', '=', instance_id),
            ('product_id', '=', False)
        ])

        if orphaned_products:
            issues.append(f"{len(orphaned_products)} products without linked Odoo products")

        orphaned_orders = self.env['shopify.order'].search([
            ('instance_id', '=', instance_id),
            ('sale_order_id', '=', False),
            ('imported', '=', True)
        ])

        if orphaned_orders:
            issues.append(f"{len(orphaned_orders)} imported orders without sale orders")

        # Log integrity issues
        for issue in issues:
            self.create({
                'instance_id': instance_id,
                'operation': 'data_validation',
                'status': 'warning',
                'message': f'Data integrity issue: {issue}'
            })

        return issues

    def action_view_related_record(self):
        """Open the related record"""
        if not self.related_model or not self.related_record_id:
            raise UserError(_("No related record available"))

        return {
            'type': 'ir.actions.act_window',
            'res_model': self.related_model,
            'res_id': self.related_record_id,
            'view_mode': 'form',
            'target': 'current'
        }

    @api.model
    def cleanup_old_logs(self, days=90):
        """Clean up old logs"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)

        # Keep error logs longer
        old_logs = self.search([
            ('create_date', '<', cutoff_date),
            ('status', '!=', 'error')
        ])

        old_error_logs = self.search([
            ('create_date', '<', cutoff_date - timedelta(days=30)),  # Keep errors for 120 days
            ('status', '=', 'error')
        ])

        total_deleted = len(old_logs) + len(old_error_logs)
        old_logs.unlink()
        old_error_logs.unlink()

        return total_deleted

    @api.model
    def get_statistics(self, instance_id, days=30):
        """Get log statistics for an instance"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)

        domain = [
            ('instance_id', '=', instance_id),
            ('create_date', '>=', cutoff_date)
        ]

        stats = {
            'total_logs': self.search_count(domain),
            'success_count': self.search_count(domain + [('status', '=', 'success')]),
            'error_count': self.search_count(domain + [('status', '=', 'error')]),
            'warning_count': self.search_count(domain + [('status', '=', 'warning')]),
            'avg_execution_time': 0
        }

        # Calculate average execution time
        logs_with_time = self.search(domain + [('execution_time', '>', 0)])
        if logs_with_time:
            stats['avg_execution_time'] = sum(logs_with_time.mapped('execution_time')) / len(logs_with_time)

        return stats

    def action_retry_operation(self):
        """Retry the failed operation"""
        if self.status != 'error':
            raise UserError(_("Only error logs can be retried"))

        if not self.related_model or not self.related_record_id:
            raise UserError(_("No related record to retry"))

        # Create a new queue job to retry the operation
        self.env['shopify.queue'].create({
            'name': f"Retry {self.operation} - {fields.Datetime.now()}",
            'operation': self.operation,
            'instance_id': self.instance_id.id,
            'state': 'queued',
            'priority': '3'  # High priority for retries
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Operation Queued'),
                'message': _('The operation has been queued for retry'),
                'type': 'success',
            }
        }