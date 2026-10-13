#!/usr/bin/env python3
"""
Create demo images for testing SocialPulse
"""

import os
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_demo_images():
    """Create sample images for testing"""
    
    # Create demo directory
    demo_dir = Path("demo_images")
    demo_dir.mkdir(exist_ok=True)
    
    # Sample 1: iPhone pricing offer
    create_iphone_offer_image(demo_dir / "iphone_offer.png")
    
    # Sample 2: General product ad
    create_product_ad_image(demo_dir / "product_ad.png")
    
    # Sample 3: News post
    create_news_post_image(demo_dir / "news_post.png")
    
    print(f"Demo images created in {demo_dir}:")
    for img_file in demo_dir.glob("*.png"):
        print(f"  - {img_file.name}")

def create_iphone_offer_image(output_path):
    """Create iPhone offer demo image"""
    
    # Create image
    img = Image.new('RGB', (400, 600), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to use a better font
        title_font = ImageFont.truetype("arial.ttf", 32)
        text_font = ImageFont.truetype("arial.ttf", 20)
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Fallback to default font
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Instagram-style header
    draw.rectangle([0, 0, 400, 60], fill='#262626')
    draw.text((20, 20), "amazing_deals_official", fill='white', font=text_font)
    draw.text((350, 20), "•••", fill='white', font=text_font)
    
    # Main product area
    draw.rectangle([50, 100, 350, 300], fill='#333333', outline='#666666')
    draw.text((200, 200), "📱", font=title_font, anchor="mm")
    
    # Main claim
    draw.text((200, 340), "iPhone 17 Pro", fill='white', font=title_font, anchor="mm")
    draw.text((200, 380), "available for", fill='#cccccc', font=text_font, anchor="mm")
    
    # Price highlight
    draw.rectangle([100, 400, 300, 450], fill='#ff4444')
    draw.text((200, 425), "₹19,999", fill='white', font=title_font, anchor="mm")
    
    # Call to action
    draw.text((200, 480), "Limited time offer!", fill='#ffcc00', font=text_font, anchor="mm")
    draw.text((200, 510), "Contact us now for", fill='white', font=small_font, anchor="mm")
    draw.text((200, 530), "exclusive deals", fill='white', font=small_font, anchor="mm")
    
    # Hashtags
    draw.text((20, 570), "#iPhone #Apple #Deal #Discount", fill='#4da6ff', font=small_font)
    
    img.save(output_path)

def create_product_ad_image(output_path):
    """Create generic product ad"""
    
    img = Image.new('RGB', (500, 400), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        text_font = ImageFont.truetype("arial.ttf", 18)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # Header
    draw.rectangle([0, 0, 500, 60], fill='#2c5aa0')
    draw.text((250, 30), "SUPER SALE EVENT", fill='white', font=title_font, anchor="mm")
    
    # Product area
    draw.rectangle([50, 100, 450, 250], fill='white', outline='#cccccc')
    draw.text((250, 175), "🎧 Premium Headphones", fill='black', font=title_font, anchor="mm")
    
    # Price
    draw.text((250, 280), "Originally ₹5,999", fill='#999999', font=text_font, anchor="mm")
    draw.line([200, 285, 300, 285], fill='#999999', width=2)
    draw.text((250, 310), "Now only ₹999!", fill='#cc0000', font=title_font, anchor="mm")
    
    # Footer
    draw.text((250, 360), "Visit our website or call now!", fill='black', font=text_font, anchor="mm")
    
    img.save(output_path)

def create_news_post_image(output_path):
    """Create news post image"""
    
    img = Image.new('RGB', (600, 400), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype("arial.ttf", 20)
        text_font = ImageFont.truetype("arial.ttf", 16)
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
    
    # News header
    draw.rectangle([0, 0, 600, 50], fill='#1f4e79')
    draw.text((300, 25), "TechNews Daily", fill='white', font=title_font, anchor="mm")
    
    # News content
    draw.text((50, 80), "BREAKING:", fill='#cc0000', font=title_font)
    draw.text((50, 110), "New smartphone technology", fill='black', font=title_font)
    draw.text((50, 140), "promises 50% better battery life", fill='black', font=title_font)
    
    draw.text((50, 180), "Industry experts report breakthrough in", fill='#333333', font=text_font)
    draw.text((50, 200), "battery technology that could revolutionize", fill='#333333', font=text_font)
    draw.text((50, 220), "mobile devices. Early tests show", fill='#333333', font=text_font)
    draw.text((50, 240), "significant improvements in power", fill='#333333', font=text_font)
    draw.text((50, 260), "efficiency and charging speed.", fill='#333333', font=text_font)
    
    # Source
    draw.text((50, 320), "Source: Technology Research Institute", fill='#666666', font=text_font)
    draw.text((50, 340), "Published: January 15, 2024", fill='#666666', font=text_font)
    
    img.save(output_path)

if __name__ == "__main__":
    create_demo_images()