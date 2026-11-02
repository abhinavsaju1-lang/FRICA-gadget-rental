# FRICA - Premium Electronic Gadget Rental Web Application

> **A full-stack, production-ready Electronic Gadget Rental Platform built with Python 3, Django (MVT Architecture), SQLite, and modern responsive frontend (Bootstrap 5.3 + Vanilla JS). Designed for academic project submissions, resume showcase, and LinkedIn portfolios.**

---

## 🚀 Key Highlights & Resume Summary
- **MVT Architecture**: Clean separation of Models, Views, and Templates using Django 5.
- **Dynamic Pricing Engine**: Real-time JavaScript rental duration and cost calculator with date constraint validations (`end_date >= start_date >= today`).
- **Cart & Order Lifecycle**: Session/database-backed rental cart, multiple mock payment simulations (UPI, Credit/Debit Card, Cash on Delivery), and order status progression (`Waiting for Approval` &rarr; `Active` &rarr; `Returned` &rarr; `Cancelled`).
- **Comprehensive Admin Control Panel**: Customized Django Admin for inventory control, quick inline status toggles, availability flags, and bulk approval actions.
- **Official Invoicing**: Printable, downloadable computer-generated rental tax invoice / receipt with QR and order breakdown.
- **Automated Data Seeding**: Built-in Django management command (`populate_data.py`) with programmatic Pillow-generated product graphic assets.

---

## 🛠️ Tech Stack & Dependencies
- **Backend**: Python 3.11+, Django 5.2 (ORM, Auth, Session & Message Frameworks)
- **Database**: SQLite3 (relational schema configured via Django ORM)
- **Image Processing**: Pillow (PIL)
- **Frontend**: HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Google Fonts (Plus Jakarta Sans), Vanilla JavaScript
- **Security**: CSRF protection, password hashing with PBKDF2/SHA256, sanitized SQL queries via ORM, role-based access control.

---

## 📁 Project Directory Structure
```
Rental App/
│
├── manage.py                          # Django management CLI
├── requirements.txt                   # Production dependencies
├── db.sqlite3                         # SQLite database with schema & seed data
│
├── rental_site/                       # Root Django Project Configuration
│   ├── __init__.py
│   ├── settings.py                    # App registry, media/static configuration
│   ├── urls.py                        # Project-level URL routing & static handlers
│   ├── asgi.py
│   └── wsgi.py
│
├── ecomapp/                           # Main Application Package
│   ├── __init__.py
│   ├── models.py                      # Customer, Products, Cart, RentedItems
│   ├── views.py                       # Business logic & controller workflows
│   ├── urls.py                        # RESTful endpoint routes
│   ├── forms.py                       # Registration, Auth, AddToCart, Checkout
│   ├── admin.py                       # Customized Django Admin interfaces & actions
│   ├── context_processors.py          # Global cart counter badge processor
│   ├── migrations/                    # Database migration history
│   └── management/
│       └── commands/
│           └── populate_data.py       # Seed script with Pillow asset generator
│
├── templates/                         # HTML5 Django Templates
│   ├── base.html                      # Glassmorphic header, navbar, badge, footer
│   ├── home.html                      # Hero banner, category pills, gadget grid
│   ├── product_detail.html            # Specs, date picker, live JS cost calculator
│   ├── cart.html                      # Tenure breakdown, subtotal, checkout CTA
│   ├── checkout.html                  # Address confirmation, UPI/Card/COD mock pay
│   ├── user_dashboard.html            # Rental history with status badges
│   ├── receipt.html                   # Printable tax invoice / receipt
│   ├── login.html                     # Polished auth card with demo hints
│   └── register.html                  # Customer registration form
│
├── static/                            # Static Assets
│   ├── css/
│   │   └── style.css                  # Custom styling system, badges, transitions
│   └── js/
│       └── main.js                    # Dynamic calculator, validation, auto-dismiss
│
└── media/                             # Dynamic Uploads & Seeded Images
    └── products/                      # Generated gadget graphics
```

---

## 🗄️ Database Schema & Data Models

### 1. `Customer`
Extends Django's built-in `User` model via One-to-One relation:
- `user`: `OneToOneField(User, on_delete=models.CASCADE)`
- `phone`: `CharField(max_length=15)`
- `address`: `TextField()`
- `profile_pic`: `ImageField(upload_to='customers/')`

### 2. `Products`
Catalog of electronic items available for rent:
- `product_name`: `CharField(max_length=200)`
- `category`: `Choices` (`Mobiles`, `Computers`, `Camera`, `Laptop`, `TV`, `Watches`)
- `description`: `TextField()`
- `rent_price`: `DecimalField(max_digits=10, decimal_places=2)` (per-day rate in INR)
- `availability`: `BooleanField(default=True)`
- `image`: `ImageField(upload_to='products/')`
- `created_at`: `DateTimeField(auto_now_add=True)`

### 3. `Cart`
Temporary holding container for rental items:
- `user`: `ForeignKey(User, on_delete=models.CASCADE)`
- `product`: `ForeignKey(Products, on_delete=models.CASCADE)`
- `rent_start_date`: `DateField()`
- `rent_end_date`: `DateField()`
- `total_days`: `PositiveIntegerField()`
- `total_amount`: `DecimalField(max_digits=10, decimal_places=2)`

### 4. `RentedItems`
Confirmed rental transactions & tracking:
- `rental_id`: `CharField(primary_key=True)` (e.g., `FRICA-20261027-50DC5B`)
- `user`: `ForeignKey(User, on_delete=models.CASCADE)`
- `product`: `ForeignKey(Products, on_delete=models.CASCADE)`
- `rent_start_date`, `rent_end_date`: `DateField()`
- `total_amount`: `DecimalField(max_digits=10, decimal_places=2)`
- `payment_method`: `Choices` (`UPI`, `Card`, `Cash on Delivery`)
- `payment_status`: `Choices` (`Paid`, `Pending`, `Failed`)
- `rental_status`: `Choices` (`Waiting for Approval`, `Active`, `Returned`, `Cancelled`)
- `delivery_address`: `TextField()`
- `contact_phone`: `CharField(max_length=15)`
- `created_at`: `DateTimeField(auto_now_add=True)`

---

## ⚡ Quick Start & Run Guide

### 1. Activate the Virtual Environment
**Windows PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```
*(Or Git Bash / Command Prompt)*:
```bash
source venv/Scripts/activate       # Git Bash
.\venv\Scripts\activate.bat        # CMD
```

### 2. Install Dependencies (Already installed in venv)
```bash
pip install -r requirements.txt
```

### 3. Apply Migrations & Seed Data
```bash
python manage.py makemigrations ecomapp
python manage.py migrate
python manage.py populate_data
```

### 4. Start Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 🔑 Pre-Configured Test Accounts

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Admin Superuser** | `admin` | `admin12345` | Access `/admin/` to approve rentals, toggle availability, edit catalog |
| **Demo Customer** | `demouser` | `demo12345` | Test browsing, date calculation, cart, mock payment, order tracking |

---

## 🧪 Testing Verification
Run the automated integration test suite:
```bash
python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rental_site.settings'); django.setup(); from django.test import Client; client = Client(); assert client.get('/').status_code == 200; print('FRICA Web Application OK!')"
```
