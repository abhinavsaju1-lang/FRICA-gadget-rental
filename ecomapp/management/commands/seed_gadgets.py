from django.core.management.base import BaseCommand
from decimal import Decimal
from ecomapp.models import Products


class Command(BaseCommand):
    help = 'Seed initial gadget products as per APP.pdf documentation'

    def handle(self, *args, **options):
        gadgets = [
            {
                "product_name": "Samsung Galaxy S23 Ultra",
                "category": "Mobiles",
                "description": "Flagship Samsung phone with Snapdragon processor, 200MP camera, 120Hz display.",
                "rent_price": Decimal('999.00'),
                "availability": True,
                "image_url": "https://images.unsplash.com/photo-1610945265064-0e34e5519bbf?auto=format&fit=crop&w=600&q=80",
            },
            {
                "product_name": "Titan Smartwatch",
                "category": "Watch",
                "description": "Titan smartwatch with health monitoring and customizable watch faces.",
                "rent_price": Decimal('299.00'),
                "availability": True,
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80",
            },
            {
                "product_name": "Canon EOS Camera",
                "category": "Camera",
                "description": "Canon EOS DSLR camera, 24MP sensor, 4K video recording.",
                "rent_price": Decimal('599.00'),
                "availability": True,
                "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=600&q=80",
            },
        ]

        for gadget in gadgets:
            product, created = Products.objects.get_or_create(
                product_name=gadget["product_name"],
                defaults={
                    "category": gadget["category"],
                    "description": gadget["description"],
                    "rent_price": gadget["rent_price"],
                    "availability": gadget["availability"],
                    "image_url": gadget.get("image_url"),
                },
            )
            # Update image URL & image fields with the direct image link
            product.image_url = gadget["image_url"]
            product.image = gadget["image_url"]
            product.rent_price = gadget["rent_price"]
            product.availability = gadget["availability"]
            product.save()

            if created:
                self.stdout.write(self.style.SUCCESS(f"Created product: {product.product_name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated product image: {product.product_name}"))
