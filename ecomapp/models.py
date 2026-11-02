import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
ID_PROOF_CHOICES = [
    ('AADHAAR', 'Aadhaar Card'),
    ('PAN', 'PAN Card'),
    ('DL', 'Driving License'),
]

KYC_STATUS_CHOICES = [
    ('NOT_SUBMITTED', 'Not Submitted'),
    ('PENDING', 'Pending'),
    ('VERIFIED', 'Verified'),
    ('REJECTED', 'Rejected'),
]


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='customers/', blank=True, null=True)
    gender = models.CharField(max_length=15, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    annual_income = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    aadhar_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=20, blank=True, null=True)
    pancard_front_img = models.ImageField(upload_to='kyc_docs/', blank=True, null=True)
    aadhar_front_img = models.ImageField(upload_to='kyc_docs/', blank=True, null=True)
    # KYC documents & status
    id_proof_type = models.CharField(max_length=10, choices=ID_PROOF_CHOICES, blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    id_front_image = models.ImageField(upload_to='kyc_docs/', blank=True, null=True)
    id_back_image = models.ImageField(upload_to='kyc_docs/', blank=True, null=True)
    kyc_status = models.CharField(max_length=20, default='NOT_SUBMITTED', choices=KYC_STATUS_CHOICES)
    kyc_submitted_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.user.email})"


# Allow both user.customer and user.customer_profile
User.customer = property(lambda u: getattr(u, 'customer_profile', None))


class Products(models.Model):
    CATEGORY_CHOICES = [
        ('Mobiles', 'Mobiles'),
        ('Computers', 'Computers'),
        ('Camera', 'Camera'),
        ('Laptop', 'Laptop'),
        ('TV', 'TV'),
        ('Watches', 'Watches'),
    ]

    product_name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    # Rich specs stored as newline-separated key:value pairs e.g. "Processor:A17 Pro\nRAM:8GB"
    specs = models.TextField(blank=True, null=True, help_text="Key specs, one per line e.g. Processor:Snapdragon 8 Gen 2")
    rent_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rent price per day in INR")
    availability = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    # CDN fallback URL for high-resolution product imagery (e.g. Unsplash)
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="External image URL as fallback")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    @property
    def get_image_url(self):
        """Returns the best available image URL: direct http link → local upload → CDN URL → None."""
        if self.image:
            img_str = str(self.image)
            if img_str.startswith('http://') or img_str.startswith('https://'):
                return img_str
            try:
                return self.image.url
            except Exception:
                pass
        if self.image_url:
            return self.image_url
        return None

    @property
    def specs_list(self):
        """Returns specs as a list of {'key': ..., 'value': ...} dicts for template rendering."""
        if not self.specs:
            return []
        result = []
        for line in self.specs.strip().splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                result.append({'key': key.strip(), 'value': value.strip()})
        return result

    @property
    def specs_preview(self):
        """Returns first 2 specs as compact chip strings for card previews."""
        return self.specs_list[:2]

    def __str__(self):
        return f"{self.product_name} - ₹{self.rent_price}/day ({self.category})"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    rent_start_date = models.DateField()
    rent_end_date = models.DateField()
    total_days = models.PositiveIntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_totals(self):
        if self.rent_start_date and self.rent_end_date:
            days = (self.rent_end_date - self.rent_start_date).days + 1
            self.total_days = max(1, days)
        else:
            self.total_days = 1

        if self.product and self.product.rent_price:
            self.total_amount = self.product.rent_price * self.total_days

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Cart: {self.user.username} - {self.product.product_name} ({self.total_days} days)"


class RentedItems(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
    ]

    RENTAL_STATUS_CHOICES = [
        ('Waiting for Approval', 'Waiting for Approval'),
        ('Active', 'Active'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI Payment'),
        ('Card', 'Credit / Debit Card'),
        ('Cash on Delivery', 'Cash on Delivery (Pay on Receipt)'),
    ]

    rental_id = models.CharField(max_length=30, primary_key=True, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    rent_start_date = models.DateField()
    rent_end_date = models.DateField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='UPI')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    rental_status = models.CharField(max_length=30, choices=RENTAL_STATUS_CHOICES, default='Waiting for Approval')
    # Extension & Return workflow fields
    is_extension_requested = models.BooleanField(default=False)
    extended_days = models.PositiveIntegerField(default=0)
    extension_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    RETURN_STATUS_CHOICES = [
        ('NOT_INITIATED', 'In Possession'),
        ('RETURN_REQUESTED', 'Return & Inspection Requested'),
        ('PICKED_UP', 'Picked Up / In Transit'),
        ('RETURN_COMPLETED', 'Returned & Inspected'),
    ]
    return_status = models.CharField(max_length=30, choices=RETURN_STATUS_CHOICES, default='NOT_INITIATED')
    return_notes = models.TextField(blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rented Item'
        verbose_name_plural = 'Rented Items'
        ordering = ['-created_at']

    @property
    def total_days(self):
        if self.rent_start_date and self.rent_end_date:
            return max(1, (self.rent_end_date - self.rent_start_date).days + 1)
        return 1

    def save(self, *args, **kwargs):
        if not self.rental_id:
            short_id = uuid.uuid4().hex[:6].upper()
            self.rental_id = f"FRICA-{timezone.now().strftime('%Y%m%d')}-{short_id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.rental_id} | {self.product.product_name} | {self.user.username} ({self.rental_status})"
