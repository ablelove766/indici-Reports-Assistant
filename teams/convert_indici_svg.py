#!/usr/bin/env python3
"""
Convert Indici SVG logo to Microsoft Teams app icons.
Creates color.png (192x192) and outline.png (32x32) from indici.svg
"""

import os
import sys
from pathlib import Path

def convert_svg_to_png():
    """Convert SVG to PNG files using cairosvg."""
    
    # Check if SVG file exists
    svg_path = Path("indici.svg")
    if not svg_path.exists():
        print("❌ indici.svg not found in teams directory")
        return False
    
    print("🎨 Converting Indici SVG to Teams app icons...")
    
    try:
        import cairosvg
        from PIL import Image
        import io
        
        # Convert SVG to PNG at high resolution for color icon
        print("🖼️ Creating color.png (192x192)...")
        color_png_data = cairosvg.svg2png(
            url="indici.svg", 
            output_width=192, 
            output_height=192,
            background_color='white'  # White background for color icon
        )
        
        with open("color.png", "wb") as f:
            f.write(color_png_data)
        print("✅ Created color.png")
        
        # Create outline icon (32x32)
        print("🖼️ Creating outline.png (32x32)...")
        
        # First create a 32x32 version
        outline_png_data = cairosvg.svg2png(
            url="indici.svg",
            output_width=32,
            output_height=32,
            background_color='transparent'
        )
        
        # Load with PIL and convert to white outline
        img = Image.open(io.BytesIO(outline_png_data))
        img = img.convert('RGBA')
        
        # Create white outline version
        pixels = img.load()
        for i in range(img.width):
            for j in range(img.height):
                r, g, b, a = pixels[i, j]
                if a > 50:  # If pixel is not transparent
                    pixels[i, j] = (255, 255, 255, a)  # Make it white
        
        img.save("outline.png", "PNG")
        print("✅ Created outline.png")
        
        return True
        
    except ImportError:
        print("❌ Missing required packages")
        print("Installing cairosvg and pillow...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "cairosvg", "pillow"])
            print("✅ Packages installed, retrying conversion...")
            return convert_svg_to_png()  # Retry after installation
        except Exception as e:
            print(f"❌ Failed to install packages: {e}")
            print("\n🔧 Manual installation required:")
            print("pip install cairosvg pillow")
            return False
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def create_teams_package():
    """Create the Teams app package ZIP file."""
    required_files = ["manifest.json", "color.png", "outline.png"]
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files for Teams package: {missing_files}")
        return False
    
    try:
        import zipfile
        
        print("📦 Creating Teams app package...")
        with zipfile.ZipFile("indici-reports-assistant.zip", "w") as zip_file:
            for file in required_files:
                zip_file.write(file)
                print(f"   ✅ Added {file}")
        
        print("🎉 Created indici-reports-assistant.zip")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create package: {e}")
        return False

def main():
    """Main function."""
    print("🎯 Indici SVG to Teams Icons Converter")
    print("=" * 50)
    
    # Ensure we're in the teams directory
    if not Path("indici.svg").exists():
        print("❌ Please run this script from the teams directory")
        print("❌ Make sure indici.svg is in the teams directory")
        return
    
    # Convert SVG to PNG icons
    if convert_svg_to_png():
        print("\n🎉 Icon conversion completed!")
        
        # Verify files were created
        if Path("color.png").exists() and Path("outline.png").exists():
            print("✅ Both icon files created successfully")
            
            # Show file sizes
            color_size = Path("color.png").stat().st_size
            outline_size = Path("outline.png").stat().st_size
            print(f"📊 color.png: {color_size:,} bytes")
            print(f"📊 outline.png: {outline_size:,} bytes")
            
            # Create Teams package
            if create_teams_package():
                print("\n📦 Teams app package ready!")
                print("📁 Files created:")
                print("   ✅ color.png (192x192)")
                print("   ✅ outline.png (32x32)")
                print("   ✅ indici-reports-assistant.zip")
                
                print("\n🚀 Next steps:")
                print("1. Upload indici-reports-assistant.zip to Microsoft Teams")
                print("2. Apps → Manage your apps → Upload a custom app")
                print("3. Test the app in Teams")
            
        else:
            print("❌ Icon files were not created properly")
    else:
        print("\n❌ Icon conversion failed")
        print("Please install required packages: pip install cairosvg pillow")

if __name__ == "__main__":
    main()
