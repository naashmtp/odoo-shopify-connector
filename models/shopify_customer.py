from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import requests
import json


class ShopifyCustomer(models.Model):
    _name = 'shopify.customer'
    _description = 'Shopify Customer'
    _rec_name = 'name'

    name = fields.Char('Customer Name', required=True)
    shopify_id = fields.Char('Shopify Customer ID', required=True)
    instance_id = fields.Many2one('shopify.instance', 'Shopify Instance', required=True)
    partner_id = fields.Many2one('res.partner', 'Odoo Partner')

    # Customer Details
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    note = fields.Text('Notes')
    tags = fields.Char('Tags')

    # Status
    state = fields.Selection([
        ('disabled', 'Disabled'),
        ('invited', 'Invited'),
        ('enabled', 'Enabled'),
        ('declined', 'Declined')
    ], string='Status')

    accepts_marketing = fields.Boolean('Accepts Marketing')
    verified_email = fields.Boolean('Verified Email')
    tax_exempt = fields.Boolean('Tax Exempt')

    # Dates
    shopify_created_at = fields.Datetime('Created at Shopify')
    shopify_updated_at = fields.Datetime('Updated at Shopify')
    last_order_date = fields.Datetime('Last Order Date')

    # Statistics
    orders_count = fields.Integer('Orders Count')
    total_spent = fields.Float('Total Spent')
    currency = fields.Char('Currency')

    # Addresses
    address_ids = fields.One2many('shopify.customer.address', 'customer_id', 'Addresses')
    default_address = fields.Text('Default Address')

    # Sync
    last_sync = fields.Datetime('Last Sync')
    imported = fields.Boolean('Imported to Odoo', default=False)

    @api.model
    def import_from_shopify(self, instance):
        """Import customers from Shopify"""
        try:
            headers = {
                'X-Shopify-Access-Token': instance.access_token or instance.api_secret,
                'Content-Type': 'application/json'
            }

            url = f"https://{instance.shop_url}/admin/api/2023-10/customers.json"
            params = {'limit': 250}

            while url:
                response = requests.get(url, headers=headers, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    customers = data.get('customers', [])

                    for customer_data in customers:
                        self._create_or_update_customer(instance, customer_data)

                    # Handle pagination
                    url = self._get_next_page_url(response.headers)
                    params = None
                else:
                    raise UserError(_("Failed to fetch customers: %s") % response.text)

            instance.last_sync = fields.Datetime.now()
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'customer_import',
                'message': 'Customers imported successfully',
                'status': 'success'
            })

        except Exception as e:
            self.env['shopify.log'].create({
                'instance_id': instance.id,
                'operation': 'customer_import',
                'message': f'Error importing customers: {str(e)}',
                'status': 'error'
            })

    def _create_or_update_customer(self, instance, customer_data):
        """Create or update customer from Shopify data"""
        shopify_id = str(customer_data.get('id'))
        existing_customer = self.search([
            ('shopify_id', '=', shopify_id),
            ('instance_id', '=', instance.id)
        ], limit=1)

        vals = self._prepare_customer_vals(instance, customer_data)

        if existing_customer:
            existing_customer.write(vals)
            customer = existing_customer
        else:
            customer = self.create(vals)

        # Import addresses
        self._import_customer_addresses(customer, customer_data.get('addresses', []))

        # Auto-create partner if configured
        if instance.auto_import_customers and not customer.imported:
            customer.create_partner()

        return customer

    def _prepare_customer_vals(self, instance, customer_data):
        """Prepare customer values from Shopify data"""
        first_name = customer_data.get('first_name', '')
        last_name = customer_data.get('last_name', '')
        name = f"{first_name} {last_name}".strip() or customer_data.get('email', 'Unknown Customer')

        default_address = customer_data.get('default_address')
        default_address_text = self._format_address(default_address) if default_address else ''

        return {
            'name': name,
            'shopify_id': str(customer_data.get('id')),
            'instance_id': instance.id,
            'first_name': first_name,
            'last_name': last_name,
            'email': customer_data.get('email'),
            'phone': customer_data.get('phone'),
            'note': customer_data.get('note'),
            'tags': customer_data.get('tags'),
            'state': customer_data.get('state'),
            'accepts_marketing': customer_data.get('accepts_marketing'),
            'verified_email': customer_data.get('verified_email'),
            'tax_exempt': customer_data.get('tax_exempt'),
            'shopify_created_at': customer_data.get('created_at'),
            'shopify_updated_at': customer_data.get('updated_at'),
            'last_order_date': customer_data.get('last_order_date'),
            'orders_count': customer_data.get('orders_count', 0),
            'total_spent': float(customer_data.get('total_spent', 0)),
            'currency': customer_data.get('currency'),
            'default_address': default_address_text,
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

    def _import_customer_addresses(self, customer, addresses_data):
        """Import customer addresses"""
        for address_data in addresses_data:
            self.env['shopify.customer.address']._create_or_update_address(
                customer, address_data
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

    def create_partner(self):
        """Create Odoo partner from Shopify customer"""
        if self.partner_id:
            return self.partner_id

        # Check if partner already exists by email
        if self.email:
            existing_partner = self.env['res.partner'].search([('email', '=', self.email)], limit=1)
            if existing_partner:
                self.partner_id = existing_partner.id
                self.imported = True
                return existing_partner

        # Create new partner
        vals = {
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'comment': self.note,
            'is_company': False,
            'customer_rank': 1,
            'supplier_rank': 0
        }

        # Add default address if available
        if self.default_address:
            address_data = self._parse_default_address()
            vals.update(address_data)

        partner = self.env['res.partner'].create(vals)
        self.partner_id = partner.id
        self.imported = True

        # Create additional addresses as child contacts
        self._create_child_addresses(partner)

        return partner

    def _parse_default_address(self):
        """Parse default address text to dictionary"""
        if not self.default_address:
            return {}

        lines = [line.strip() for line in self.default_address.split('\n') if line.strip()]

        # Basic parsing - this could be improved
        vals = {}
        if len(lines) >= 4:
            vals['street'] = lines[3]
        if len(lines) >= 6:
            vals['city'] = lines[5]
        if len(lines) >= 8:
            vals['zip'] = lines[7]
        if len(lines) >= 9:
            country = self.env['res.country'].search([('name', 'ilike', lines[8])], limit=1)
            if country:
                vals['country_id'] = country.id

        return vals

    def _create_child_addresses(self, parent_partner):
        """Create child contacts for additional addresses"""
        for address in self.address_ids:
            if address.is_default:
                continue  # Skip default address as it's already on parent

            vals = {
                'name': f"{self.name} - {address.name or 'Address'}",
                'parent_id': parent_partner.id,
                'type': 'delivery',
                'street': address.address1,
                'street2': address.address2,
                'city': address.city,
                'zip': address.zip,
                'phone': address.phone
            }

            # Find country and state
            if address.country:
                country = self.env['res.country'].search([('name', 'ilike', address.country)], limit=1)
                if country:
                    vals['country_id'] = country.id

                    if address.province:
                        state = self.env['res.country.state'].search([
                            ('name', 'ilike', address.province),
                            ('country_id', '=', country.id)
                        ], limit=1)
                        if state:
                            vals['state_id'] = state.id

            self.env['res.partner'].create(vals)

    def update_customer_info(self):
        """Update customer info in Shopify"""
        if not self.partner_id:
            raise UserError(_("No Odoo partner linked to this customer"))

        headers = {
            'X-Shopify-Access-Token': self.instance_id.access_token or self.instance_id.api_secret,
            'Content-Type': 'application/json'
        }

        customer_data = {
            'customer': {
                'id': int(self.shopify_id),
                'first_name': self.partner_id.name.split()[0] if self.partner_id.name else '',
                'last_name': ' '.join(self.partner_id.name.split()[1:]) if len(self.partner_id.name.split()) > 1 else '',
                'email': self.partner_id.email,
                'phone': self.partner_id.phone,
                'note': self.partner_id.comment or ''
            }
        }

        url = f"https://{self.instance_id.shop_url}/admin/api/2023-10/customers/{self.shopify_id}.json"
        response = requests.put(url, headers=headers, json=customer_data, timeout=30)

        if response.status_code == 200:
            self.last_sync = fields.Datetime.now()
        else:
            raise UserError(_("Failed to update customer: %s") % response.text)

    def action_create_partner(self):
        """Manual action to create partner"""
        self.create_partner()
        return True

    def action_sync_from_shopify(self):
        """Manual sync from Shopify"""
        self.import_from_shopify(self.instance_id)
        return True


class ShopifyCustomerAddress(models.Model):
    _name = 'shopify.customer.address'
    _description = 'Shopify Customer Address'

    name = fields.Char('Address Name')
    shopify_id = fields.Char('Shopify Address ID', required=True)
    customer_id = fields.Many2one('shopify.customer', 'Shopify Customer', required=True)

    # Address Details
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    company = fields.Char('Company')
    address1 = fields.Char('Address Line 1')
    address2 = fields.Char('Address Line 2')
    city = fields.Char('City')
    province = fields.Char('Province/State')
    country = fields.Char('Country')
    zip = fields.Char('ZIP/Postal Code')
    phone = fields.Char('Phone')

    # Flags
    is_default = fields.Boolean('Default Address')

    @api.model
    def _create_or_update_address(self, customer, address_data):
        """Create or update address from Shopify data"""
        shopify_id = str(address_data.get('id'))
        existing_address = self.search([
            ('shopify_id', '=', shopify_id),
            ('customer_id', '=', customer.id)
        ], limit=1)

        first_name = address_data.get('first_name', '')
        last_name = address_data.get('last_name', '')
        name = f"{first_name} {last_name}".strip() or 'Address'

        vals = {
            'name': name,
            'shopify_id': shopify_id,
            'customer_id': customer.id,
            'first_name': first_name,
            'last_name': last_name,
            'company': address_data.get('company'),
            'address1': address_data.get('address1'),
            'address2': address_data.get('address2'),
            'city': address_data.get('city'),
            'province': address_data.get('province'),
            'country': address_data.get('country'),
            'zip': address_data.get('zip'),
            'phone': address_data.get('phone'),
            'is_default': address_data.get('default', False)
        }

        if existing_address:
            existing_address.write(vals)
            return existing_address
        else:
            return self.create(vals)