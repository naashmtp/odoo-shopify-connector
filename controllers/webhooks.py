from odoo import http
from odoo.http import request, Response
import json
import logging
import hmac
import hashlib
import base64

_logger = logging.getLogger(__name__)


class ShopifyWebhookController(http.Controller):
    """Controller for handling Shopify webhooks"""

    def _verify_webhook_signature(self, data, hmac_header, webhook_secret):
        """Verify webhook signature"""
        if not webhook_secret:
            return False

        calculated_hmac = base64.b64encode(
            hmac.new(
                webhook_secret.encode('utf-8'),
                data,
                hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(calculated_hmac, hmac_header)

    def _get_instance_from_domain(self, shop_domain):
        """Get Shopify instance from shop domain"""
        instance = request.env['shopify.instance'].sudo().search([
            ('shop_url', '=', shop_domain),
            ('is_active', '=', True)
        ], limit=1)
        return instance

    @http.route('/shopify/webhook/<string:topic>', type='json', auth='public', methods=['POST'], csrf=False)
    def shopify_webhook(self, topic, **kwargs):
        """Generic webhook handler"""
        try:
            # Get request data
            data = request.httprequest.get_data()
            headers = request.httprequest.headers

            # Get shop domain from headers
            shop_domain = headers.get('X-Shopify-Shop-Domain')
            hmac_header = headers.get('X-Shopify-Hmac-Sha256')

            if not shop_domain:
                _logger.error("Missing X-Shopify-Shop-Domain header")
                return {'status': 'error', 'message': 'Missing shop domain'}

            # Find instance
            instance = self._get_instance_from_domain(shop_domain)
            if not instance:
                _logger.error(f"No active instance found for domain: {shop_domain}")
                return {'status': 'error', 'message': 'Unknown shop domain'}

            # Verify signature
            if instance.webhook_secret and not self._verify_webhook_signature(data, hmac_header, instance.webhook_secret):
                _logger.error(f"Invalid webhook signature for {shop_domain}")
                return {'status': 'error', 'message': 'Invalid signature'}

            # Parse JSON data
            webhook_data = json.loads(data.decode('utf-8'))

            # Process webhook
            result = request.env['shopify.webhook'].sudo().process_webhook(
                topic.replace('/', '/'),  # Ensure proper topic format
                webhook_data,
                dict(headers),
                instance.id
            )

            if result:
                return {'status': 'success', 'message': 'Webhook processed'}
            else:
                return {'status': 'error', 'message': 'Webhook processing failed'}

        except Exception as e:
            _logger.error(f"Error processing webhook {topic}: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    @http.route('/shopify/webhook/order/create', type='json', auth='public', methods=['POST'], csrf=False)
    def order_create(self, **kwargs):
        """Handle order creation webhook"""
        return self.shopify_webhook('orders/create', **kwargs)

    @http.route('/shopify/webhook/order/update', type='json', auth='public', methods=['POST'], csrf=False)
    def order_update(self, **kwargs):
        """Handle order update webhook"""
        return self.shopify_webhook('orders/updated', **kwargs)

    @http.route('/shopify/webhook/order/cancel', type='json', auth='public', methods=['POST'], csrf=False)
    def order_cancel(self, **kwargs):
        """Handle order cancellation webhook"""
        return self.shopify_webhook('orders/cancelled', **kwargs)

    @http.route('/shopify/webhook/order/fulfill', type='json', auth='public', methods=['POST'], csrf=False)
    def order_fulfill(self, **kwargs):
        """Handle order fulfillment webhook"""
        return self.shopify_webhook('orders/fulfilled', **kwargs)

    @http.route('/shopify/webhook/product/create', type='json', auth='public', methods=['POST'], csrf=False)
    def product_create(self, **kwargs):
        """Handle product creation webhook"""
        return self.shopify_webhook('products/create', **kwargs)

    @http.route('/shopify/webhook/product/update', type='json', auth='public', methods=['POST'], csrf=False)
    def product_update(self, **kwargs):
        """Handle product update webhook"""
        return self.shopify_webhook('products/update', **kwargs)

    @http.route('/shopify/webhook/customer/create', type='json', auth='public', methods=['POST'], csrf=False)
    def customer_create(self, **kwargs):
        """Handle customer creation webhook"""
        return self.shopify_webhook('customers/create', **kwargs)

    @http.route('/shopify/webhook/refund/create', type='json', auth='public', methods=['POST'], csrf=False)
    def refund_create(self, **kwargs):
        """Handle refund creation webhook"""
        return self.shopify_webhook('refunds/create', **kwargs)

    @http.route('/shopify/webhook/test', type='http', auth='public', methods=['GET'], csrf=False)
    def webhook_test(self, **kwargs):
        """Test endpoint to verify webhook configuration"""
        return Response(
            json.dumps({'status': 'ok', 'message': 'Webhook endpoint is accessible'}),
            content_type='application/json'
        )