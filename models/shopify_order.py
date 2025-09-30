from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import json
from datetime import datetime


class ShopifyOrder(models.Model):
    _name = 'shopify.order'
    _description = 'Shopify Order'
    _rec_name = 'name'

    name = fields.Char('Order Number', required=True)
    shopify_id = fields.Char('Shopify Order ID', required=True)
    shopify_order_number = fields.Char('Shopify Order Number')
    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    sale_order_id = fields.Many2one('sale.order', 'Sale Order')

    # Order Details
    email = fields.Char('Customer Email')
    phone = fields.Char('Customer Phone')
    note = fields.Text('Order Notes')
    tags = fields.Char('Tags')

    # Financial
    total_price = fields.Float('Total Price')
    subtotal_price = fields.Float('Subtotal Price')
    total_tax = fields.Float('Total Tax')
    total_discounts = fields.Float('Total Discounts')
    shipping_price = fields.Float('Shipping Price')
    currency = fields.Char('Currency')

    # Status
    financial_status = fields.Selection([
        ('pending', 'Pending'),
        ('authorized', 'Authorized'),
        ('partially_paid', 'Partially Paid'),
        ('paid', 'Paid'),
        ('partially_refunded', 'Partially Refunded'),
        ('refunded', 'Refunded'),
        ('voided', 'Voided')
    ], string='Financial Status')

    fulfillment_status = fields.Selection([
        ('fulfilled', 'Fulfilled'),
        ('partial', 'Partial'),
        ('restocked', 'Restocked'),
        ('unfulfilled', 'Unfulfilled')
    ], string='Fulfillment Status')

    # Dates
    shopify_created_at = fields.Datetime('Created at Shopify')
    shopify_updated_at = fields.Datetime('Updated at Shopify')
    processed_at = fields.Datetime('Processed At')
    cancelled_at = fields.Datetime('Cancelled At')
    closed_at = fields.Datetime('Closed At')

    # Customer
    customer_id = fields.Many2one('shopify.customer', 'Shopify Customer')

    # Address
    billing_address = fields.Text('Billing Address')
    shipping_address = fields.Text('Shipping Address')

    # Order Lines
    line_ids = fields.One2many('shopify.order.line', 'order_id', 'Order Lines')
    line_count = fields.Integer('Lines Count', compute='_compute_line_count')

    # Sync
    last_sync = fields.Datetime('Last Sync')
    imported = fields.Boolean('Imported to Odoo', default=False)

    @api.depends('line_ids')
    def _compute_line_count(self):
        for record in self:
            record.line_count = len(record.line_ids)

    @api.model
    def import_from_shopify(self, instance):
        """Import orders from Shopify"""
        try:
            headers = {
                'X-Shopify-Access-Token': instance.access_token or instance.api_secret,
                'Content-Type': 'application/json'
            }

            # Import unfulfilled orders
            self._import_orders_by_status(instance, headers, 'unfulfilled')

            # Import partially fulfilled orders
            self._import_orders_by_status(instance, headers, 'partial')

            instance.last_sync = fields.Datetime.now()
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'order_import',
                'message': 'Orders imported successfully',
                'status': 'success'
            })

        except Exception as e:
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'order_import',
                'message': f'Error importing orders: {str(e)}',
                'status': 'error'
            })

    def _import_orders_by_status(self, instance, headers, status):
        """Import orders by fulfillment status"""
        url = f"https://{instance.shop_url}/admin/api/2023-10/orders.json"
        params = {
            'limit': 250,
            'fulfillment_status': status,
            'status': 'any'
        }

        while url:
            response = requests.get(url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                orders = data.get('orders', [])

                for order_data in orders:
                    self._create_or_update_order(instance, order_data)

                # Handle pagination
                url = self._get_next_page_url(response.headers)
                params = None
            else:
                raise UserError(_("Failed to fetch orders: %s") % response.text)

    def _create_or_update_order(self, instance, order_data):
        """Create or update order from Shopify data"""
        shopify_id = str(order_data.get('id'))
        existing_order = self.search([
            ('shopify_id', '=', shopify_id),
            ('instance_id', '=', instance.id)
        ], limit=1)

        vals = self._prepare_order_vals(instance, order_data)

        if existing_order:
            existing_order.write(vals)
            order = existing_order
        else:
            order = self.create(vals)

        # Import order lines
        self._import_order_lines(order, order_data.get('line_items', []))

        # Auto-process if configured
        if instance.auto_import_orders and not order.imported:
            order.create_sale_order()

        return order

    def _prepare_order_vals(self, instance, order_data):
        """Prepare order values from Shopify data"""
        billing_address = order_data.get('billing_address', {})
        shipping_address = order_data.get('shipping_address', {})

        return {
            'name': order_data.get('name', order_data.get('order_number')),
            'shopify_id': str(order_data.get('id')),
            'shopify_order_number': str(order_data.get('order_number')),
            'instance_id': instance.id,
            'email': order_data.get('email'),
            'phone': order_data.get('phone'),
            'note': order_data.get('note'),
            'tags': order_data.get('tags'),
            'total_price': float(order_data.get('total_price', 0)),
            'subtotal_price': float(order_data.get('subtotal_price', 0)),
            'total_tax': float(order_data.get('total_tax', 0)),
            'total_discounts': float(order_data.get('total_discounts', 0)),
            'currency': order_data.get('currency'),
            'financial_status': order_data.get('financial_status'),
            'fulfillment_status': order_data.get('fulfillment_status'),
            'shopify_created_at': order_data.get('created_at'),
            'shopify_updated_at': order_data.get('updated_at'),
            'processed_at': order_data.get('processed_at'),
            'cancelled_at': order_data.get('cancelled_at'),
            'closed_at': order_data.get('closed_at'),
            'billing_address': self._format_address(billing_address),
            'shipping_address': self._format_address(shipping_address),
            'last_sync': fields.Datetime.now()
        }

    def _format_address(self, address_data):
        """Format address data to text"""
        if not address_data:
            return ''

        address_parts = [
            address_data.get('first_name', ''),
            address_data.get('last_name', ''),
            address_data.get('company', ''),
            address_data.get('address1', ''),
            address_data.get('address2', ''),
            address_data.get('city', ''),
            address_data.get('province', ''),
            address_data.get('zip', ''),
            address_data.get('country', '')
        ]

        return '\n'.join([part for part in address_parts if part])

    def _import_order_lines(self, order, line_items):
        """Import order line items"""
        for line_data in line_items:
            self.env['shopify.order.line']._create_or_update_line(
                order, line_data
            )

    def _get_next_page_url(self, headers):
        """Extract next page URL from response headers"""
        link_header = headers.get('Link', '')
        if 'rel="next"' in link_header:
            links = link_header.split(',')
            for link in links:
                if 'rel="next"' in link:
                    return link.split('<')[1].split('>')[0]
        return None

    def create_sale_order(self):
        """Create Odoo sale order from Shopify order"""
        if self.sale_order_id:
            return self.sale_order_id

        # Find or create customer
        partner = self._find_or_create_customer()

        # Create sale order
        vals = {
            'partner_id': partner.id,
            'origin': f"Shopify-{self.name}",
            'note': self.note,
            'team_id': self.instance_id.team_id.id if self.instance_id.team_id else False,
            'payment_term_id': self.instance_id.payment_term_id.id if self.instance_id.payment_term_id else False,
            'pricelist_id': self.instance_id.pricelist_id.id if self.instance_id.pricelist_id else partner.property_product_pricelist.id,
        }

        sale_order = self.env['sale.order'].create(vals)

        # Create order lines
        for line in self.line_ids:
            line.create_sale_order_line(sale_order)

        self.sale_order_id = sale_order.id
        self.imported = True

        # Auto-confirm if configured
        if self.instance_id.auto_create_invoices:
            sale_order.action_confirm()

        return sale_order

    def _find_or_create_customer(self):
        """Find or create customer partner"""
        if self.customer_id and self.customer_id.partner_id:
            return self.customer_id.partner_id

        if self.email:
            partner = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if partner:
                return partner

        # Create new partner
        billing_data = self._parse_address(self.billing_address)
        vals = {
            'name': billing_data.get('name', self.email or 'Unknown Customer'),
            'email': self.email,
            'phone': self.phone,
            'is_company': False,
            'customer_rank': 1
        }

        return self.env['res.partner'].create(vals)

    def _parse_address(self, address_text):
        """Parse address text to dictionary"""
        if not address_text:
            return {}

        lines = address_text.split('\n')
        return {
            'name': lines[0] if lines else '',
            'street': lines[3] if len(lines) > 3 else '',
            'city': lines[5] if len(lines) > 5 else '',
            'zip': lines[7] if len(lines) > 7 else '',
        }

    def update_order_status(self, status):
        """Update order status in Shopify"""
        headers = {
            'X-Shopify-Access-Token': self.instance_id.access_token or self.instance_id.api_secret,
            'Content-Type': 'application/json'
        }

        order_data = {
            'order': {
                'id': int(self.shopify_id),
                'fulfillment_status': status
            }
        }

        url = f"https://{self.instance_id.shop_url}/admin/api/2023-10/orders/{self.shopify_id}.json"
        response = requests.put(url, headers=headers, json=order_data, timeout=30)

        if response.status_code == 200:
            self.fulfillment_status = status
        else:
            raise UserError(_("Failed to update order status: %s") % response.text)

    def mark_order_fulfilled(self):
        """Mark order as fulfilled in Shopify"""
        self.update_order_status('fulfilled')

    def cancel_shopify_order(self):
        """Cancel order in Shopify"""
        headers = {
            'X-Shopify-Access-Token': self.instance_id.access_token or self.instance_id.api_secret,
            'Content-Type': 'application/json'
        }

        url = f"https://{self.instance_id.shop_url}/admin/api/2023-10/orders/{self.shopify_id}/cancel.json"
        response = requests.post(url, headers=headers, timeout=30)

        if response.status_code == 200:
            self.cancelled_at = fields.Datetime.now()
        else:
            raise UserError(_("Failed to cancel order: %s") % response.text)


class ShopifyOrderLine(models.Model):
    _name = 'shopify.order.line'
    _description = 'Shopify Order Line'

    name = fields.Char('Product Name', required=True)
    shopify_id = fields.Char('Shopify Line ID', required=True)
    order_id = fields.Many2one('shopify.order', 'Shopify Order', required=True)
    variant_id = fields.Many2one('shopify.product.variant', 'Product Variant')
    sale_line_id = fields.Many2one('sale.order.line', 'Sale Order Line')

    # Product details
    variant_title = fields.Char('Variant Title')
    sku = fields.Char('SKU')
    vendor = fields.Char('Vendor')

    # Quantities and prices
    quantity = fields.Float('Quantity')
    price = fields.Float('Unit Price')
    total_discount = fields.Float('Total Discount')
    total_price = fields.Float('Total Price')

    # Product properties
    requires_shipping = fields.Boolean('Requires Shipping')
    taxable = fields.Boolean('Taxable')
    fulfillment_status = fields.Char('Fulfillment Status')

    @api.model
    def _create_or_update_line(self, order, line_data):
        """Create or update line from Shopify data"""
        shopify_id = str(line_data.get('id'))
        existing_line = self.search([
            ('shopify_id', '=', shopify_id),
            ('order_id', '=', order.id)
        ], limit=1)

        vals = {
            'name': line_data.get('title'),
            'shopify_id': shopify_id,
            'order_id': order.id,
            'variant_title': line_data.get('variant_title'),
            'sku': line_data.get('sku'),
            'vendor': line_data.get('vendor'),
            'quantity': float(line_data.get('quantity', 1)),
            'price': float(line_data.get('price', 0)),
            'total_discount': float(line_data.get('total_discount', 0)),
            'requires_shipping': line_data.get('requires_shipping'),
            'taxable': line_data.get('taxable'),
            'fulfillment_status': line_data.get('fulfillment_status')
        }

        vals['total_price'] = vals['quantity'] * vals['price'] - vals['total_discount']

        if existing_line:
            existing_line.write(vals)
            return existing_line
        else:
            return self.create(vals)

    def create_sale_order_line(self, sale_order):
        """Create sale order line in Odoo"""
        if self.sale_line_id:
            return self.sale_line_id

        # Find product
        product = self._find_product()
        if not product:
            # Create a generic product or raise error
            product = self._create_generic_product()

        vals = {
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': self.name,
            'product_uom_qty': self.quantity,
            'price_unit': self.price,
        }

        sale_line = self.env['sale.order.line'].create(vals)
        self.sale_line_id = sale_line.id

        return sale_line

    def _find_product(self):
        """Find corresponding Odoo product"""
        if self.variant_id and self.variant_id.odoo_variant_id:
            return self.variant_id.odoo_variant_id

        if self.sku:
            product = self.env['product.product'].search([('default_code', '=', self.sku)], limit=1)
            if product:
                return product

        # Try by name
        product = self.env['product.product'].search([('name', 'ilike', self.name)], limit=1)
        return product

    def _create_generic_product(self):
        """Create a generic product for unmapped items"""
        vals = {
            'name': self.name,
            'default_code': self.sku,
            'type': 'product',
            'list_price': self.price,
            'categ_id': self.env.ref('product.product_category_all').id
        }

        return self.env['product.product'].create(vals)