#!/usr/bin/env python3
"""
Generate placeholder images for Shopify Integration module.
This script creates simple placeholder images when proper graphics are not available.

Usage:
    python3 generate_placeholder_images.py
"""

import os

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("PIL/Pillow not available. Install with: pip3 install Pillow")


def create_icon(output_path, size=256):
    """Create a simple icon placeholder."""
    if not PIL_AVAILABLE:
        print(f"Skipping {output_path} - PIL not available")
        return

    # Create image with green background
    img = Image.new('RGB', (size, size), color='#5cb85c')
    draw = ImageDraw.Draw(img)

    # Draw white circle border
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        outline='white',
        width=size // 20
    )

    # Try to add text
    try:
        # Use a default font, try to make it large
        font_size = size // 3
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Draw "S" in the center
    text = "S"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    position = ((size - text_width) // 2, (size - text_height) // 2 - size // 20)
    draw.text(position, text, fill='white', font=font)

    # Save
    img.save(output_path)
    print(f"Created: {output_path}")


def create_banner(output_path, width=1200, height=630):
    """Create a simple banner placeholder."""
    if not PIL_AVAILABLE:
        print(f"Skipping {output_path} - PIL not available")
        return

    # Create image with gradient-like background
    img = Image.new('RGB', (width, height), color='#5cb85c')
    draw = ImageDraw.Draw(img)

    # Add darker gradient effect
    for y in range(height):
        alpha = int(255 * (1 - y / height * 0.3))
        color = (92, 184, 92)  # #5cb85c in RGB
        draw.rectangle([0, y, width, y + 1], fill=color)

    # Try to add text
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

    # Draw title
    title = "Shopify Integration"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    title_height = bbox[3] - bbox[1]
    title_x = (width - title_width) // 2
    title_y = height // 3

    # Add shadow
    draw.text((title_x + 3, title_y + 3), title, fill='#2c3e50', font=font_title)
    draw.text((title_x, title_y), title, fill='white', font=font_title)

    # Draw subtitle
    subtitle = "Complete Connector for Odoo 16"
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + title_height + 30

    draw.text((subtitle_x + 2, subtitle_y + 2), subtitle, fill='#2c3e50', font=font_subtitle)
    draw.text((subtitle_x, subtitle_y), subtitle, fill='white', font=font_subtitle)

    # Save
    img.save(output_path)
    print(f"Created: {output_path}")


def main():
    """Generate all placeholder images."""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_desc = os.path.join(script_dir, 'static', 'description')

    # Ensure directory exists
    os.makedirs(static_desc, exist_ok=True)

    # Generate images
    icon_path = os.path.join(static_desc, 'icon.png')
    banner_path = os.path.join(static_desc, 'banner.png')

    print("Generating placeholder images...")
    print("-" * 50)

    create_icon(icon_path)
    create_banner(banner_path)

    print("-" * 50)
    print("Done!")
    print()
    print("Note: These are placeholder images.")
    print("For production, create professional graphics using:")
    print("  - Figma, Canva, or Adobe tools")
    print("  - See static/description/README_IMAGES.txt for guidelines")


if __name__ == '__main__':
    main()