"""
WSGI config for rental_site project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_site.settings')
application = get_wsgi_application()

# Auto-migrate and initial data bootstrap fallback
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)

    # Auto-seed products if database is empty
    try:
        from ecomapp.models import Products
        if Products.objects.count() == 0:
            call_command('seed_gadgets')
    except Exception as seed_err:
        print(f"WSGI product seed error: {seed_err}")

    # Ensure default admin/demo user exists
    try:
        from django.contrib.auth.models import User
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='adminpassword123'
            )
    except Exception as user_err:
        print(f"WSGI superuser creation note: {user_err}")

except Exception as e:
    print(f"WSGI startup bootstrap error: {e}")
