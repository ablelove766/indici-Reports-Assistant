#!/usr/bin/env python3
"""
Create placeholder icons for Microsoft Teams app.
Run this script to generate the required icon files.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_color_icon():
    """Create the 192x192 color icon."""
    # Create a 192x192 image with blue background
    img = Image.new('RGB', (192, 192), '#2563eb')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple chart icon
    # Draw bars
    bar_width = 20
    bar_spacing = 30
    base_y = 150
    
    # Bar heights
    heights = [60, 90, 45, 75, 100]
    colors = ['#ffffff', '#e0e7ff', '#c7d2fe', '#a5b4fc', '#818cf8']
    
    for i, (height, color) in enumerate(zip(heights, colors)):
        x = 30 + i * (bar_width + bar_spacing)
        draw.rectangle([x, base_y - height, x + bar_width, base_y], fill=color)
    
    # Draw title text
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Draw "INDICI" text
    text = "INDICI"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (192 - text_width) // 2
    draw.text((text_x, 20), text, fill='white', font=font)
    
    # Draw "Reports" text
    try:
        small_font = ImageFont.truetype("arial.ttf", 16)
    except:
        small_font = ImageFont.load_default()
    
    text2 = "Reports"
    bbox2 = draw.textbbox((0, 0), text2, font=small_font)
    text2_width = bbox2[2] - bbox2[0]
    text2_x = (192 - text2_width) // 2
    draw.text((text2_x, 50), text2, fill='#e0e7ff', font=small_font)
    
    # Save the image
    img.save('teams/color.png', 'PNG')
    print("✅ Created color.png (192x192)")

def create_outline_icon():
    """Create the 32x32 outline icon."""
    # Create a 32x32 transparent image
    img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw simple chart outline in white
    # Draw bars outline
    bar_width = 3
    bar_spacing = 4
    base_y = 26
    
    # Bar heights (scaled down)
    heights = [8, 12, 6, 10, 14]
    
    for i, height in enumerate(heights):
        x = 4 + i * (bar_width + bar_spacing)
        # Draw outline
        draw.rectangle([x, base_y - height, x + bar_width, base_y], 
                      outline='white', width=1)
    
    # Draw a simple "i" for indici
    draw.text((14, 2), "i", fill='white')
    
    # Save the image
    img.save('teams/outline.png', 'PNG')
    print("✅ Created outline.png (32x32)")

def main():
    """Create both icon files."""
    # Create teams directory if it doesn't exist
    os.makedirs('teams', exist_ok=True)
    
    print("🎨 Creating Microsoft Teams app icons...")
    
    try:
        create_color_icon()
        create_outline_icon()
        print("\n🎉 Icons created successfully!")
        print("\n📝 Next steps:")
        print("1. Review the generated icons in the teams/ folder")
        print("2. Replace with your branded icons if needed")
        print("3. Create the Teams app package (ZIP file)")
        print("4. Upload to Microsoft Teams")
        
    except ImportError:
        print("❌ PIL (Pillow) is required to create icons.")
        print("Install it with: pip install Pillow")
        print("\nAlternatively, create the icons manually:")
        print("- color.png: 192x192px with your brand colors")
        print("- outline.png: 32x32px simple outline version")
    except Exception as e:
        print(f"❌ Error creating icons: {e}")
        print("\nPlease create the icons manually:")
        print("- color.png: 192x192px with your brand colors")
        print("- outline.png: 32x32px simple outline version")

if __name__ == "__main__":
    main()
