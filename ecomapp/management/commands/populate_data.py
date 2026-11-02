import os
from pathlib import Path
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from ecomapp.models import Products, Customer


def create_product_graphic(filepath, title, category, price, bg_color):
    """
    Generates a modern graphic placeholder card using Pillow.
    """
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Draw stylish rounded inner card
    margin = 30
    card_bounds = [margin, margin, width - margin, height - margin]
    draw.rectangle(card_bounds, outline=(255, 255, 255, 40), width=3)

    # Top Brand bar
    draw.rectangle([margin, margin, width - margin, margin + 70], fill=(15, 23, 42))
    
    # Simple default font rendering
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_med = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font_large = ImageFont.load_default()
        font_med = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((margin + 25, margin + 20), "FRICA  |  PREMIUM TECH RENTALS", fill=(248, 250, 252), font=font_small)

    # Category badge
    badge_x, badge_y = margin + 25, 140
    draw.rectangle([badge_x, badge_y, badge_x + 180, badge_y + 40], fill=(79, 70, 229))
    draw.text((badge_x + 15, badge_y + 10), category.upper(), fill=(255, 255, 255), font=font_small)

    # Product Title (wrapped if needed)
    draw.text((margin + 25, 210), title, fill=(255, 255, 255), font=font_large)

    # Divider line
    draw.line([(margin + 25, 360), (width - margin - 25, 360)], fill=(255, 255, 255, 60), width=2)

    # Pricing badge
    draw.text((margin + 25, 400), "DAILY RENTAL TARIFF", fill=(148, 163, 184), font=font_small)
    draw.text((margin + 25, 435), f"INR {price} / day", fill=(52, 211, 153), font=font_large)

    # Assurance pill
    draw.text((margin + 25, 510), "* Zero Security Deposit on KYC  |  100% Transit Insured", fill=(203, 213, 225), font=font_small)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath, format='JPEG', quality=90)


class Command(BaseCommand):
    help = 'Populates database with initial gadgets, demo users, and realistic product graphics'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing seed process for FRICA Rental App..."))

        # Setup media directory
        products_media_dir = Path(settings.MEDIA_ROOT) / 'products'
        products_media_dir.mkdir(parents=True, exist_ok=True)

        sample_products = [
            {
                'name': 'Samsung Galaxy S23 Ultra 5G (Phantom Black, 256GB)',
                'category': 'Mobiles',
                'price': Decimal('499.00'),
                'description': 'Flagship smartphone featuring Snapdragon 8 Gen 2, 200MP Quad Camera with 100x Space Zoom, built-in S-Pen, and 6.8-inch Dynamic AMOLED 2X 120Hz display. Ideal for high-end photography, travel vlogging, and mobile productivity.',
                'image_name': 'samsung_s23_ultra.jpg',
                'bg_color': (30, 41, 59),
            },
            {
                'name': 'Apple iPhone 15 Pro Max (Natural Titanium, 256GB)',
                'category': 'Mobiles',
                'price': Decimal('599.00'),
                'description': 'Aerospace-grade titanium design powered by the A17 Pro chip. Features 5x optical telephoto lens, USB-C 3 speeds, Action Button, and ProMotion 120Hz display with Always-On.',
                'image_name': 'iphone_15_pro_max.jpg',
                'bg_color': (24, 24, 27),
            },
            {
                'name': 'Apple MacBook Pro 16" (M3 Max, 36GB RAM, 1TB SSD)',
                'category': 'Laptop',
                'price': Decimal('799.00'),
                'description': 'High-performance powerhouse for developers, video editors, and 3D animators. Features Liquid Retina XDR display, 22-hour battery life, and revolutionary hardware-accelerated ray tracing.',
                'image_name': 'macbook_pro_m3.jpg',
                'bg_color': (39, 39, 42),
            },
            {
                'name': 'HP Victus 16 Gaming Laptop (Core i7, RTX 4060, 16GB)',
                'category': 'Laptop',
                'price': Decimal('449.00'),
                'description': 'Ready for AAA esports and streaming. Powered by 13th Gen Intel Core i7, NVIDIA GeForce RTX 4060 8GB GPU, and 165Hz FHD IPS anti-glare display with OMEN Gaming Hub cooling.',
                'image_name': 'hp_victus_16.jpg',
                'bg_color': (15, 23, 42),
            },
            {
                'name': 'Canon EOS R6 Mark II Mirrorless Camera (with 24-105mm Lens)',
                'category': 'Camera',
                'price': Decimal('699.00'),
                'description': '24.2 MP full-frame sensor, 40 fps electronic burst, 4K 60p oversampled video, dual pixel CMOS AF II, and in-body 8-stop image stabilization. Perfect for commercial shoots, events, and cinematic filmmaking.',
                'image_name': 'canon_eos_r6_ii.jpg',
                'bg_color': (20, 24, 33),
            },
            {
                'name': 'Sony Alpha A7 IV Full-Frame Hybrid Camera',
                'category': 'Camera',
                'price': Decimal('649.00'),
                'description': '33MP full-frame Exmor R CMOS sensor, BIONZ XR processing engine, 4K 60p 10-bit recording, Real-time Eye AF for humans, animals, and birds.',
                'image_name': 'sony_alpha_a7iv.jpg',
                'bg_color': (18, 22, 34),
            },
            {
                'name': 'Titan Smartwatch Apex (1.96" AMOLED, Metallic Finish)',
                'category': 'Watches',
                'price': Decimal('149.00'),
                'description': 'Ultra-clear AMOLED always-on display, Bluetooth calling with AI voice assistant, 110+ sports modes, SpO2 & 24/7 heart rate tracker in a premium aerospace alloy case.',
                'image_name': 'titan_smartwatch_apex.jpg',
                'bg_color': (24, 28, 42),
            },
            {
                'name': 'Apple Watch Ultra 2 GPS + Cellular (49mm Titanium)',
                'category': 'Watches',
                'price': Decimal('299.00'),
                'description': 'Rugged outdoor smartwatch with 3000-nit display, precision dual-frequency GPS, depth gauge for scuba diving, Action button, and 72-hour Low Power Mode battery.',
                'image_name': 'apple_watch_ultra_2.jpg',
                'bg_color': (31, 41, 55),
            },
            {
                'name': 'LG C3 55-inch 4K OLED evo Smart TV (Dolby Vision & Atmos)',
                'category': 'TV',
                'price': Decimal('549.00'),
                'description': 'Self-lit OLED pixels delivering infinite contrast and 100% color fidelity. α9 AI Processor Gen6, 120Hz native refresh rate, 4 HDMI 2.1 ports for next-gen PS5/Xbox consoles.',
                'image_name': 'lg_c3_55_oled.jpg',
                'bg_color': (15, 23, 42),
            },
            {
                'name': 'Pro Custom Gaming PC Rig (Ryzen 7 7800X3D + RTX 4080 Super)',
                'category': 'Computers',
                'price': Decimal('899.00'),
                'description': 'Elite desktop tower with liquid AIO cooling, 32GB DDR5 6000MHz RAM, 2TB Gen4 NVMe, and ultra-high frame rates at 4K resolution. Ideal for LAN parties and 3D rendering.',
                'image_name': 'gaming_rig_pc.jpg',
                'bg_color': (17, 24, 39),
            },
        ]

        # Populate products
        for item in sample_products:
            img_rel_path = f"products/{item['image_name']}"
            img_full_path = Path(settings.MEDIA_ROOT) / img_rel_path

            create_product_graphic(
                filepath=img_full_path,
                title=item['name'][:36] + "...",
                category=item['category'],
                price=item['price'],
                bg_color=item['bg_color']
            )

            product, created = Products.objects.update_or_create(
                product_name=item['name'],
                defaults={
                    'category': item['category'],
                    'rent_price': item['price'],
                    'description': item['description'],
                    'availability': True,
                    'image': img_rel_path,
                }
            )
            action_verb = "Created" if created else "Updated"
            self.stdout.write(f"  [+] {action_verb} product: {product.product_name}")

        # Ensure demo user exists
        demo_user, u_created = User.objects.get_or_create(
            username='demouser',
            defaults={
                'first_name': 'Rahul',
                'last_name': 'Sharma',
                'email': 'rahul.sharma@example.com',
            }
        )
        if u_created:
            demo_user.set_password('demo12345')
            demo_user.save()
            Customer.objects.create(
                user=demo_user,
                phone='+91 9876543210',
                address='Flat 402, Green Glen Heights, Outer Ring Road, Bangalore - 560103'
            )
            self.stdout.write(self.style.SUCCESS("  [+] Created demo user: demouser (password: demo12345)"))
        else:
            self.stdout.write("  [-] Demo user demouser already exists.")

        # Ensure admin superuser exists
        admin_user, a_created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@frica.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if a_created:
            admin_user.set_password('admin12345')
            admin_user.save()
            Customer.objects.get_or_create(
                user=admin_user,
                defaults={'phone': '+91 9999999999', 'address': 'FRICA HQ, Cyber City, Gurgaon'}
            )
            self.stdout.write(self.style.SUCCESS("  [+] Created admin superuser: admin (password: admin12345)"))
        else:
            self.stdout.write("  [-] Admin user admin already exists.")

        self.stdout.write(self.style.SUCCESS("\nDatabase population completed successfully!"))
