#!/usr/bin/env python3
"""
Create PWA icons from a simple design
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create an icon with the specified size."""
    # Create image with gradient background
    img = Image.new('RGB', (size, size), color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw a simple yield curve symbol
    # Draw a curve shape
    width, height = size, size
    margin = size // 6
    
    # Draw a stylized yield curve
    points = []
    for i in range(9):
        x = margin + (i * (width - 2*margin) // 8)
        # Create upward sloping curve
        y = height - margin - (i * (height - 2*margin) // 8) // 2
        points.append((x, y))
    
    # Draw curve line
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill='white', width=max(2, size//32))
    
    # Draw points
    for point in points:
        draw.ellipse([point[0]-size//32, point[1]-size//32, 
                     point[0]+size//32, point[1]+size//32], 
                    fill='white')
    
    # Save
    img.save(output_path, 'PNG')
    print(f"Created {output_path} ({size}x{size})")

if __name__ == '__main__':
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)
    
    # Create icons
    create_icon(192, os.path.join(static_dir, 'icon-192.png'))
    create_icon(512, os.path.join(static_dir, 'icon-512.png'))
    
    print("Icons created successfully!")

