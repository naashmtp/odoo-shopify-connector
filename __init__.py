from . import models
from . import controllers
from . import wizards

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Pre-installation hook"""
    _logger.info("Shopify Integration: Running pre-installation checks...")
    # Check if required dependencies are installed
    try:
        import requests
        _logger.info("✓ requests library found")
    except ImportError:
        _logger.warning("⚠ requests library not found. Install with: pip install requests")

    # Note: shopifyapi is optional, we use direct API calls with requests
    _logger.info("Shopify Integration: Pre-installation checks complete")


def post_init_hook(cr, registry):
    """Post-installation hook"""
    _logger.info("Shopify Integration: Running post-installation setup...")

    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Create default data if needed
    _logger.info("Shopify Integration: Module installed successfully!")
    _logger.info("Navigate to Shopify > Configuration > Instances to get started")


def uninstall_hook(cr, registry):
    """Uninstallation hook"""
    _logger.info("Shopify Integration: Running cleanup...")

    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})

    # Clean up any external webhooks if instances exist
    instances = env['shopify.instance'].search([])
    for instance in instances:
        _logger.info(f"Remember to manually delete webhooks in Shopify admin for: {instance.name}")

    _logger.info("Shopify Integration: Module uninstalled")