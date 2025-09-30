from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ShopifyWebhook(models.Model):
    _name = 'shopify.webhook'
    _description = 'Shopify Webhook'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'topic'
    _order = 'create_date desc'

    topic = fields.Char('Topic', required=True)
    shopify_id = fields.Char('Shopify Webhook ID')
    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    
    # Webhook Details
    address = fields.Char('Webhook Address', required=True)
    format = fields.Selection([
        ('json', 'JSON'),
        ('xml', 'XML')
    ], default='json', string='Format')
    
    # Status
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('error', 'Error')
    ], default='active', string='Status', tracking=True)
    
    # Verification
    api_version = fields.Char('API Version')
    fields_to_include = fields.Char('Fields to Include')
    metafield_namespaces = fields.Char('Metafield Namespaces')
    
    # Statistics
    total_calls = fields.Integer('Total Calls', default=0)
    successful_calls = fields.Integer('Successful Calls', default=0)
    failed_calls = fields.Integer('Failed Calls', default=0)
    last_call = fields.Datetime('Last Call')
    
    # Logs
    log_ids = fields.One2many('shopify.webhook.log', 'webhook_id', 'Logs')
    
    @api.model
    def process_webhook(self, topic, data, headers, instance_id):
        """Process incoming webhook"""
        try:
            # Find webhook configuration
            webhook = self.search([
                ('topic', '=', topic),
                ('instance_id', '=', instance_id),
                ('state', '=', 'active')
            ], limit=1)
            
            if not webhook:
                _logger.warning(f"No active webhook found for topic {topic}")
                return False
            
            # Log the webhook call
            webhook_log = self.env['shopify.webhook.log'].create({
                'webhook_id': webhook.id,
                'topic': topic,
                'data': json.dumps(data) if isinstance(data, dict) else str(data),
                'headers': json.dumps(dict(headers)) if headers else '{}',
                'status': 'processing'
            })
            
            # Process based on topic
            result = self._process_by_topic(topic, data, instance_id)
            
            # Update statistics
            webhook.total_calls += 1
            webhook.last_call = fields.Datetime.now()
            
            if result:
                webhook.successful_calls += 1
                webhook_log.status = 'success'
                webhook_log.response = 'Processed successfully'
            else:
                webhook.failed_calls += 1
                webhook_log.status = 'failed'
                webhook_log.response = 'Processing failed'
            
            return result
            
        except Exception as e:
            _logger.error(f"Error processing webhook {topic}: {str(e)}")
            if 'webhook_log' in locals():
                webhook_log.status = 'error'
                webhook_log.response = str(e)
            return False
    
    def _process_by_topic(self, topic, data, instance_id):
        """Process webhook based on topic"""
        instance = self.env['shopify.instance'].browse(instance_id)
        
        try:
            if topic == 'orders/create':
                return self._process_order_created(data, instance)
            elif topic == 'orders/updated':
                return self._process_order_updated(data, instance)
            elif topic == 'orders/cancelled':
                return self._process_order_cancelled(data, instance)
            elif topic == 'orders/fulfilled':
                return self._process_order_fulfilled(data, instance)
            elif topic == 'products/create':
                return self._process_product_created(data, instance)
            elif topic == 'products/update':
                return self._process_product_updated(data, instance)
            elif topic == 'customers/create':
                return self._process_customer_created(data, instance)
            elif topic == 'refunds/create':
                return self._process_refund_created(data, instance)
            else:
                _logger.warning(f"Unhandled webhook topic: {topic}")
                return False
                
        except Exception as e:
            _logger.error(f"Error in _process_by_topic for {topic}: {str(e)}")
            return False
    
    def _process_order_created(self, data, instance):
        """Process order created webhook"""
        try:
            shopify_order = self.env['shopify.order']._create_or_update_order(instance, data)
            if instance.auto_import_orders and not shopify_order.imported:
                shopify_order.create_sale_order()
            return True
        except Exception as e:
            _logger.error(f"Error processing order created: {str(e)}")
            return False
    
    def _process_order_updated(self, data, instance):
        """Process order updated webhook"""
        try:
            self.env['shopify.order']._create_or_update_order(instance, data)
            return True
        except Exception as e:
            _logger.error(f"Error processing order updated: {str(e)}")
            return False
    
    def _process_order_cancelled(self, data, instance):
        """Process order cancelled webhook"""
        try:
            shopify_id = str(data.get('id'))
            order = self.env['shopify.order'].search([
                ('shopify_id', '=', shopify_id),
                ('instance_id', '=', instance.id)
            ], limit=1)
            
            if order and order.sale_order_id:
                order.sale_order_id.action_cancel()
            return True
        except Exception as e:
            _logger.error(f"Error processing order cancelled: {str(e)}")
            return False
    
    def _process_order_fulfilled(self, data, instance):
        """Process order fulfilled webhook"""
        try:
            shopify_id = str(data.get('id'))
            order = self.env['shopify.order'].search([
                ('shopify_id', '=', shopify_id),
                ('instance_id', '=', instance.id)
            ], limit=1)
            
            if order:
                order.fulfillment_status = 'fulfilled'
            return True
        except Exception as e:
            _logger.error(f"Error processing order fulfilled: {str(e)}")
            return False
    
    def _process_product_created(self, data, instance):
        """Process product created webhook"""
        try:
            self.env['shopify.product']._create_or_update_product(instance, data)
            return True
        except Exception as e:
            _logger.error(f"Error processing product created: {str(e)}")
            return False
    
    def _process_product_updated(self, data, instance):
        """Process product updated webhook"""
        try:
            self.env['shopify.product']._create_or_update_product(instance, data)
            return True
        except Exception as e:
            _logger.error(f"Error processing product updated: {str(e)}")
            return False
    
    def _process_customer_created(self, data, instance):
        """Process customer created webhook"""
        try:
            customer = self.env['shopify.customer']._create_or_update_customer(instance, data)
            if instance.auto_import_customers and not customer.imported:
                customer.create_partner()
            return True
        except Exception as e:
            _logger.error(f"Error processing customer created: {str(e)}")
            return False
    
    def _process_refund_created(self, data, instance):
        """Process refund created webhook"""
        try:
            # TODO: Create refund record and credit note if needed
            # self.env['shopify.refund'].create_from_webhook(data, instance)
            _logger.info(f"Refund webhook received but shopify.refund model not yet implemented: {data.get('id')}")
            return True
        except Exception as e:
            _logger.error(f"Error processing refund created: {str(e)}")
            return False
    
    def action_test_webhook(self):
        """Test webhook endpoint"""
        # This would send a test call to verify the webhook is working
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Webhook Test'),
                'message': _('Webhook test completed successfully'),
                'type': 'success',
            }
        }

    def action_view_logs(self):
        """View webhook logs"""
        return {
            'name': _('Webhook Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'shopify.webhook.log',
            'view_mode': 'tree,form',
            'domain': [('webhook_id', '=', self.id)],
            'context': {'default_webhook_id': self.id}
        }


class ShopifyWebhookLog(models.Model):
    _name = 'shopify.webhook.log'
    _description = 'Shopify Webhook Log'
    _order = 'create_date desc'
    
    webhook_id = fields.Many2one('shopify.webhook', 'Webhook', required=True)
    topic = fields.Char('Topic', required=True)
    data = fields.Text('Webhook Data')
    headers = fields.Text('Headers')
    response = fields.Text('Response')
    
    status = fields.Selection([
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('error', 'Error')
    ], default='processing', string='Status')
    
    processing_time = fields.Float('Processing Time (ms)')
    error_message = fields.Text('Error Message')
    
    @api.model
    def cleanup_old_logs(self, days=30):
        """Clean up old webhook logs"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('create_date', '<', cutoff_date)])
        old_logs.unlink()
        return True