from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import json


class ShopifyProduct(models.Model):
    _name = 'shopify.product'
    _description = 'Shopify Product'
    _rec_name = 'name'

    name = fields.Char('Product Name', required=True)
    shopify_id = fields.Char('Shopify Product ID', required=True)
    shopify_handle = fields.Char('Shopify Handle')
    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    product_id = fields.Many2one('product.product', 'Odoo Product')
    template_id = fields.Many2one('product.template', 'Product Template')

    # Product Details
    description = fields.Html('Description')
    vendor = fields.Char('Vendor')
    product_type = fields.Char('Product Type')
    tags = fields.Char('Tags')
    status = fields.Selection([
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('draft', 'Draft')
    ], default='active')

    # Shopify specific
    shopify_created_at = fields.Datetime('Created at Shopify')
    shopify_updated_at = fields.Datetime('Updated at Shopify')
    published_at = fields.Datetime('Published At')
    published_scope = fields.Char('Published Scope')

    # Sync
    last_sync = fields.Datetime('Last Sync')
    sync_required = fields.Boolean('Sync Required', default=False)

    # Variants
    variant_ids = fields.One2many('shopify.product.variant', 'product_id', 'Variants')
    variant_count = fields.Integer('Variants Count', compute='_compute_variant_count')

    # Images
    image_ids = fields.One2many('shopify.product.image', 'product_id', 'Images')
    image_count = fields.Integer('Images Count', compute='_compute_image_count')

    @api.depends('variant_ids')
    def _compute_variant_count(self):
        for record in self:
            record.variant_count = len(record.variant_ids)

    @api.depends('image_ids')
    def _compute_image_count(self):
        for record in self:
            record.image_count = len(record.image_ids)

    @api.model
    def import_from_shopify(self, instance):
        """Import products from Shopify"""
        try:
            headers = {
                'X-Shopify-Access-Token': instance.access_token or instance.api_secret,
                'Content-Type': 'application/json'
            }

            url = f"https://{instance.shop_url}/admin/api/2023-10/products.json"
            params = {'limit': 250}

            while url:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    products = data.get('products', [])

                    for product_data in products:
                        self._create_or_update_product(instance, product_data)

                    # Handle pagination
                    url = self._get_next_page_url(response.headers)
                    params = None
                else:
                    raise UserError(_("Failed to fetch products: %s") % response.text)

            instance.last_sync = fields.Datetime.now()
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'product_import',
                'message': 'Products imported successfully',
                'status': 'success'
            })

        except Exception as e:
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'product_import',
                'message': f'Error importing products: {str(e)}',
                'status': 'error'
            })

    def _create_or_update_product(self, instance, product_data):
        """Create or update product from Shopify data"""
        shopify_id = str(product_data.get('id'))
        existing_product = self.search([
            ('shopify_id', '=', shopify_id),
            ('instance_id', '=', instance.id)
        ], limit=1)

        vals = self._prepare_product_vals(instance, product_data)

        if existing_product:
            existing_product.write(vals)
            product = existing_product
        else:
            product = self.create(vals)

        # Import variants
        self._import_product_variants(product, product_data.get('variants', []))

        # Import images
        self._import_product_images(product, product_data.get('images', []))

        return product

    def _prepare_product_vals(self, instance, product_data):
        """Prepare product values from Shopify data"""
        return {
            'name': product_data.get('title'),
            'shopify_id': str(product_data.get('id')),
            'shopify_handle': product_data.get('handle'),
            'instance_id': instance.id,
            'description': product_data.get('body_html'),
            'vendor': product_data.get('vendor'),
            'product_type': product_data.get('product_type'),
            'tags': product_data.get('tags'),
            'status': product_data.get('status'),
            'shopify_created_at': product_data.get('created_at'),
            'shopify_updated_at': product_data.get('updated_at'),
            'published_at': product_data.get('published_at'),
            'published_scope': product_data.get('published_scope'),
            'last_sync': fields.Datetime.now()
        }

    def _import_product_variants(self, product, variants_data):
        """Import product variants"""
        for variant_data in variants_data:
            self.env['shopify.product.variant']._create_or_update_variant(
                product, variant_data
            )

    def _import_product_images(self, product, images_data):
        """Import product images"""
        for image_data in images_data:
            self.env['shopify.product.image']._create_or_update_image(
                product, image_data
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

    def export_to_shopify(self):
        """Export product to Shopify"""
        if not self.product_id:
            raise UserError(_("Please link an Odoo product first"))

        headers = {
            'X-Shopify-Access-Token': self.instance_id.access_token or self.instance_id.api_secret,
            'Content-Type': 'application/json'
        }

        product_data = self._prepare_export_data()

        if self.shopify_id:
            # Update existing product
            url = f"https://{self.instance_id.shop_url}/admin/api/2023-10/products/{self.shopify_id}.json"
            response = requests.put(url, headers=headers, json=product_data, timeout=30)
        else:
            # Create new product
            url = f"https://{self.instance_id.shop_url}/admin/api/2023-10/products.json"
            response = requests.post(url, headers=headers, json=product_data, timeout=30)

        if response.status_code in [200, 201]:
            result = response.json()
            self.shopify_id = str(result['product']['id'])
            self.last_sync = fields.Datetime.now()
            self.sync_required = False
        else:
            raise UserError(_("Failed to export product: %s") % response.text)

    def _prepare_export_data(self):
        """Prepare product data for export to Shopify"""
        product = self.product_id
        template = product.product_tmpl_id

        variants = []
        for variant in template.product_variant_ids:
            variant_data = {
                'title': variant.name,
                'price': str(variant.list_price),
                'sku': variant.default_code or '',
                'inventory_quantity': int(variant.qty_available),
                'inventory_management': 'shopify'
            }
            variants.append(variant_data)

        return {
            'product': {
                'title': template.name,
                'body_html': template.description_sale or '',
                'vendor': self.vendor or '',
                'product_type': self.product_type or template.categ_id.name,
                'tags': self.tags or '',
                'variants': variants
            }
        }

    def sync_stock_levels(self):
        """Sync stock levels with Shopify"""
        for variant in self.variant_ids:
            variant.sync_stock_level()

    def action_sync_from_shopify(self):
        """Manual sync from Shopify"""
        self.import_from_shopify(self.instance_id)
        return True

    def action_export_to_shopify(self):
        """Manual export to Shopify"""
        self.export_to_shopify()
        return True


class ShopifyProductVariant(models.Model):
    _name = 'shopify.product.variant'
    _description = 'Shopify Product Variant'

    name = fields.Char('Variant Name', required=True)
    shopify_id = fields.Char('Shopify Variant ID', required=True)
    product_id = fields.Many2one('shopify.product', 'Shopify Product', required=True)
    odoo_variant_id = fields.Many2one('product.product', 'Odoo Product Variant')

    # Variant details
    title = fields.Char('Title')
    price = fields.Float('Price')
    compare_at_price = fields.Float('Compare At Price')
    sku = fields.Char('SKU')
    barcode = fields.Char('Barcode')
    grams = fields.Float('Weight (grams)')
    inventory_quantity = fields.Integer('Inventory Quantity')
    inventory_policy = fields.Char('Inventory Policy')
    fulfillment_service = fields.Char('Fulfillment Service')
    inventory_management = fields.Char('Inventory Management')
    requires_shipping = fields.Boolean('Requires Shipping')
    taxable = fields.Boolean('Taxable')

    # Options
    option1 = fields.Char('Option 1')
    option2 = fields.Char('Option 2')
    option3 = fields.Char('Option 3')

    # Sync
    last_sync = fields.Datetime('Last Sync')

    @api.model
    def _create_or_update_variant(self, product, variant_data):
        """Create or update variant from Shopify data"""
        shopify_id = str(variant_data.get('id'))
        existing_variant = self.search([
            ('shopify_id', '=', shopify_id),
            ('product_id', '=', product.id)
        ], limit=1)

        vals = {
            'name': variant_data.get('title'),
            'shopify_id': shopify_id,
            'product_id': product.id,
            'title': variant_data.get('title'),
            'price': float(variant_data.get('price', 0)),
            'compare_at_price': float(variant_data.get('compare_at_price', 0)) if variant_data.get('compare_at_price') else 0,
            'sku': variant_data.get('sku'),
            'barcode': variant_data.get('barcode'),
            'grams': float(variant_data.get('grams', 0)),
            'inventory_quantity': int(variant_data.get('inventory_quantity', 0)),
            'inventory_policy': variant_data.get('inventory_policy'),
            'fulfillment_service': variant_data.get('fulfillment_service'),
            'inventory_management': variant_data.get('inventory_management'),
            'requires_shipping': variant_data.get('requires_shipping'),
            'taxable': variant_data.get('taxable'),
            'option1': variant_data.get('option1'),
            'option2': variant_data.get('option2'),
            'option3': variant_data.get('option3'),
            'last_sync': fields.Datetime.now()
        }

        if existing_variant:
            existing_variant.write(vals)
            return existing_variant
        else:
            return self.create(vals)

    def sync_stock_level(self):
        """Sync stock level with Shopify"""
        if not self.odoo_variant_id:
            return

        headers = {
            'X-Shopify-Access-Token': self.product_id.instance_id.access_token or self.product_id.instance_id.api_secret,
            'Content-Type': 'application/json'
        }

        # Get inventory item ID first
        url = f"https://{self.product_id.instance_id.shop_url}/admin/api/2023-10/variants/{self.shopify_id}.json"
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            variant_data = response.json()['variant']
            inventory_item_id = variant_data.get('inventory_item_id')

            if inventory_item_id:
                # Update inventory level
                inventory_data = {
                    'location_id': self._get_default_location_id(),
                    'inventory_item_id': inventory_item_id,
                    'available': int(self.odoo_variant_id.qty_available)
                }

                url = f"https://{self.product_id.instance_id.shop_url}/admin/api/2023-10/inventory_levels/set.json"
                requests.post(url, headers=headers, json=inventory_data, timeout=30)

    def _get_default_location_id(self):
        """Get default Shopify location ID"""
        # This should be stored in instance configuration
        return 1  # Placeholder


class ShopifyProductImage(models.Model):
    _name = 'shopify.product.image'
    _description = 'Shopify Product Image'

    name = fields.Char('Image Name')
    shopify_id = fields.Char('Shopify Image ID', required=True)
    product_id = fields.Many2one('shopify.product', 'Shopify Product', required=True)

    # Image details
    position = fields.Integer('Position')
    alt_text = fields.Char('Alt Text')
    width = fields.Integer('Width')
    height = fields.Integer('Height')
    src = fields.Char('Source URL')

    # Variant associations
    variant_ids = fields.Many2many('shopify.product.variant', 'Image Variants')

    @api.model
    def _create_or_update_image(self, product, image_data):
        """Create or update image from Shopify data"""
        shopify_id = str(image_data.get('id'))
        existing_image = self.search([
            ('shopify_id', '=', shopify_id),
            ('product_id', '=', product.id)
        ], limit=1)

        vals = {
            'name': image_data.get('alt') or f"Image {image_data.get('position', 1)}",
            'shopify_id': shopify_id,
            'product_id': product.id,
            'position': image_data.get('position'),
            'alt_text': image_data.get('alt'),
            'width': image_data.get('width'),
            'height': image_data.get('height'),
            'src': image_data.get('src')
        }

        if existing_image:
            existing_image.write(vals)
            return existing_image
        else:
            return self.create(vals)