IMAGES REQUIRED FOR MODULE
==========================

This file lists the images needed for the Shopify Integration module.

1. icon.png
   Location: static/description/icon.png
   Size: 256x256 pixels (recommended)
   Format: PNG with transparency
   Description: Module icon displayed in Odoo Apps
   Suggestions:
   - Shopify logo combined with Odoo logo
   - Shopping bag icon with integration symbol
   - Green/white color scheme to match Shopify branding
   - Simple, recognizable design

   You can create this using:
   - Online tool: https://www.canva.com/ or https://www.figma.com/
   - Design software: GIMP, Photoshop, Illustrator
   - Icon libraries: FontAwesome, Material Icons

   Recommended design:
   - Background: White or transparent
   - Main icon: Shopping cart or bag in green (#5cb85c)
   - Add small link/sync symbol to indicate integration

2. banner.png
   Location: static/description/banner.png
   Size: 1200x630 pixels (recommended)
   Format: PNG or JPG
   Description: Banner image for module listing and description page
   Suggestions:
   - Professional banner showing "Shopify + Odoo Integration"
   - Include key features or benefits
   - Use green gradient background matching Shopify colors
   - Add screenshots or mockups if available

   Recommended design:
   - Left side: Module name and tagline
   - Right side: Illustration or screenshot
   - Bottom: Key features as badges/pills
   - Color scheme: #5cb85c (green), #2c3e50 (dark blue), white

3. screenshot_*.png (optional but recommended)
   Location: static/description/screenshot_1.png, screenshot_2.png, etc.
   Size: 1280x720 pixels or higher
   Format: PNG or JPG
   Description: Screenshots of the module in action
   Suggestions:
   - Dashboard with stats
   - Configuration wizard
   - Product sync interface
   - Order management view
   - Webhook configuration

   Capture screenshots from:
   - Odoo interface once module is installed
   - Use browser developer tools to ensure good resolution
   - Add annotations or highlights to important features

QUICK PLACEHOLDER CREATION
===========================

If you need quick placeholders for testing:

For icon.png (256x256):
$ convert -size 256x256 xc:#5cb85c -gravity center -pointsize 80 -fill white \
  -annotate +0+0 "S\nO" static/description/icon.png

For banner.png (1200x630):
$ convert -size 1200x630 gradient:#5cb85c-#4cae4c -gravity center -pointsize 60 \
  -fill white -annotate +0-50 "Shopify Integration" \
  -pointsize 30 -annotate +0+50 "Complete Connector for Odoo 16" \
  static/description/banner.png

Note: Requires ImageMagick to be installed
$ sudo apt-get install imagemagick

ALTERNATIVE: Use online placeholder generators
- https://placeholder.com/
- https://via.placeholder.com/
- https://dummyimage.com/

Example URLs:
- Icon: https://via.placeholder.com/256x256/5cb85c/FFFFFF?text=Shopify+Odoo
- Banner: https://via.placeholder.com/1200x630/5cb85c/FFFFFF?text=Shopify+Integration

BRANDING GUIDELINES
===================

Shopify Colors:
- Primary Green: #5cb85c, #95BF47
- Dark Green: #4cae4c
- Dark Blue: #2c3e50
- White: #FFFFFF

Odoo Colors:
- Purple: #714B67
- Dark: #2c3e50

Recommended fonts:
- Headings: Inter, Roboto, Open Sans
- Body: System fonts, Segoe UI

Icons to consider:
- 🛍️ Shopping bag
- 🔄 Sync/Integration symbol
- 📦 Package/Product
- 🛒 Shopping cart
- 💳 Payment/Transaction