import os
import django
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from products.models import Product

MEDIA_DIR = Path('media/products')
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCT_IMAGES = {
    "SKU-BEV-001": ("coca_cola.jpg", "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&q=80", (220, 38, 38)),
    "SKU-BEV-002": ("pepsi.jpg", "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=400&q=80", (37, 99, 235)),
    "SKU-BEV-003": ("red_bull.jpg", "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400&q=80", (234, 179, 8)),
    "SKU-BEV-004": ("mineral_water.jpg", "https://images.unsplash.com/photo-1548839140-29a749e1bc4e?w=400&q=80", (14, 165, 233)),
    "SKU-SNK-001": ("lays_chips.jpg", "https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&q=80", (245, 158, 11)),
    "SKU-SNK-002": ("doritos.jpg", "https://images.unsplash.com/photo-1576402187878-974f70c890a5?w=400&q=80", (239, 68, 68)),
    "SKU-SNK-003": ("oreo.jpg", "https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400&q=80", (30, 41, 59)),
    "SKU-SNK-004": ("kitkat.jpg", "https://images.unsplash.com/photo-1606313564200-e75d5e30476c?w=400&q=80", (185, 28, 28)),
    "SKU-GRO-001": ("instant_noodles.jpg", "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=400&q=80", (217, 119, 6)),
    "SKU-GRO-002": ("basmati_rice.jpg", "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80", (16, 185, 129)),
    "SKU-GRO-003": ("sunflower_oil.jpg", "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&q=80", (234, 179, 8)),
    "SKU-BAK-001": ("white_bread.jpg", "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80", (180, 83, 9)),
    "SKU-BAK-002": ("chocolate_muffin.jpg", "https://images.unsplash.com/photo-1586985289688-ca3cf47d3e6e?w=400&q=80", (120, 53, 15)),
    "SKU-PER-001": ("dove_soap.jpg", "https://images.unsplash.com/photo-1607006314187-5c5ebf5cb03c?w=400&q=80", (14, 165, 233)),
    "SKU-PER-002": ("toothpaste.jpg", "https://images.unsplash.com/photo-1559591937-e10c598c1995?w=400&q=80", (220, 38, 38)),
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

for product in Product.objects.all():
    info = PRODUCT_IMAGES.get(product.sku)
    if not info:
        # Default fallback
        filename = f"{product.id}.jpg"
        url = None
        color = (79, 70, 229)
    else:
        filename, url, color = info

    file_path = MEDIA_DIR / filename
    downloaded = False

    if url:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                with open(file_path, 'wb') as f:
                    f.write(data)
                downloaded = True
                print(f"Downloaded image for {product.name}: {filename}")
        except Exception as e:
            print(f"Error downloading {url} for {product.name}: {e}")

    if not downloaded and not file_path.exists():
        # Generate stylized Pillow image
        img = Image.new('RGB', (400, 300), color=color)
        draw = ImageDraw.Draw(img)
        # Draw a lighter rectangle box in center
        draw.rectangle([20, 20, 380, 280], outline=(255, 255, 255), width=3)
        img.save(file_path, 'JPEG')
        print(f"Generated fallback image for {product.name}: {filename}")

    product.image = f"products/{filename}"
    product.save()
    print(f"Updated product {product.name} with image: {product.image}")

print("All product images populated successfully!")
