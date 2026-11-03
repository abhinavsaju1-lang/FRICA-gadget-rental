from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.db import models
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from .models import Products, Customer, Cart, RentedItems, Wishlist
from .forms import RegistrationForm, UserLoginForm, AddToCartForm, CheckoutForm, KYCUploadForm


def home(request):
    """
    Flipkart/Amazon style homepage featuring dynamic promotional carousel,
    sub-navbar category quick links, brand filtering, sorting, and gadget catalog.
    """
    category_filter = request.GET.get('category', 'All').strip()
    brand_filter = request.GET.get('brand', '').strip()
    search_query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort', 'popular').strip()

    products = Products.objects.filter(availability=True)

    if category_filter and category_filter != 'All':
        products = products.filter(category__iexact=category_filter)

    if brand_filter:
        products = products.filter(
            Q(brand__iexact=brand_filter) |
            Q(brand__icontains=brand_filter) |
            Q(product_name__icontains=brand_filter)
        )

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(specs__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('rent_price')
    elif sort_by == 'price_high':
        products = products.order_by('-rent_price')
    elif sort_by == 'rating':
        products = products.order_by('-rating', '-reviews_count')
    else:
        products = products.order_by('-rating', '-created_at')

    categories = [
        {'name': 'All',       'slug': 'All',       'icon': 'bi-grid-fill',         'label': 'All Gadgets'},
        {'name': 'Mobiles',   'slug': 'Mobiles',   'icon': 'bi-phone-fill',        'label': 'Mobiles'},
        {'name': 'Laptop',    'slug': 'Laptop',    'icon': 'bi-laptop',            'label': 'Laptops'},
        {'name': 'TV',        'slug': 'TV',        'icon': 'bi-tv-fill',           'label': 'Smart TVs'},
        {'name': 'Camera',    'slug': 'Camera',    'icon': 'bi-camera-fill',       'label': 'Cameras'},
        {'name': 'Audio',     'slug': 'Audio',     'icon': 'bi-speaker-fill',      'label': 'Audio & Theatres'},
        {'name': 'Watches',   'slug': 'Watches',   'icon': 'bi-smartwatch',        'label': 'Watches'},
        {'name': 'Computers', 'slug': 'Computers', 'icon': 'bi-pc-display',        'label': 'Gaming Rigs'},
    ]

    top_brands = ['Apple', 'Samsung', 'Sony', 'Vivo', 'OnePlus', 'Canon', 'JBL', 'Dell', 'HP', 'Lenovo', 'Casio', 'Titan']

    features = [
        {
            'icon': 'bi-shield-check',
            'title': 'Zero Security Deposit',
            'sub': 'Verified KYC instant rental',
        },
        {
            'icon': 'bi-truck',
            'title': 'Free Doorstep Delivery',
            'sub': 'Fast dispatch to your doorstep',
        },
        {
            'icon': 'bi-arrow-repeat',
            'title': 'Flexible Extensions',
            'sub': 'Extend tenure dynamically',
        },
        {
            'icon': 'bi-award',
            'title': '100% Tested & Insured',
            'sub': 'Covered under FRICA Care',
        },
    ]

    context = {
        'products': products,
        'current_category': category_filter,
        'current_brand': brand_filter,
        'current_sort': sort_by,
        'search_query': search_query,
        'categories': categories,
        'top_brands': top_brands,
        'features': features,
        'total_count': products.count(),
    }
    return render(request, 'home.html', context)


def product_detail(request, pk):
    """
    Product details with specifications, date range picker, and live duration/price calculation.
    """
    product = get_object_or_404(Products, pk=pk)
    related_products = Products.objects.filter(category=product.category).exclude(pk=pk)[:4]

    today = timezone.localdate()
    tomorrow = today + timedelta(days=2)

    initial_data = {
        'rent_start_date': today,
        'rent_end_date': tomorrow,
    }
    form = AddToCartForm(initial=initial_data)

    context = {
        'product': product,
        'related_products': related_products,
        'form': form,
        'today': today.isoformat(),
        'default_start': today.isoformat(),
        'default_end': tomorrow.isoformat(),
    }
    return render(request, 'product_detail.html', context)


@login_required(login_url='usrlogin')
def add_to_cart(request, pk):
    """
    Processes rental duration dates, calculates days & total, and adds/updates item in user's cart.
    """
    product = get_object_or_404(Products, pk=pk)

    if not product.availability:
        messages.error(request, f"Sorry, {product.product_name} is currently out of stock.")
        return redirect('product_detail', pk=pk)

    if request.method == 'POST':
        start_str = request.POST.get('rent_start_date')
        end_str = request.POST.get('rent_end_date')

        try:
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid rental start and end dates.")
            return redirect('product_detail', pk=pk)

        today = timezone.localdate()
        if start_date < today:
            messages.error(request, "Rental start date cannot be in the past.")
            return redirect('product_detail', pk=pk)

        if end_date < start_date:
            messages.error(request, "Rental end date must be on or after start date.")
            return redirect('product_detail', pk=pk)

        total_days = max(1, (end_date - start_date).days + 1)
        total_amount = product.rent_price * total_days

        # Update existing cart item or create a new one
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={
                'rent_start_date': start_date,
                'rent_end_date': end_date,
                'total_days': total_days,
                'total_amount': total_amount,
            }
        )

        if not created:
            cart_item.rent_start_date = start_date
            cart_item.rent_end_date = end_date
            cart_item.total_days = total_days
            cart_item.total_amount = total_amount
            cart_item.save()
            messages.info(request, f"Updated rental dates for {product.product_name} in your cart.")
        else:
            messages.success(request, f"Added {product.product_name} to your rental cart for {total_days} days.")

        return redirect('cart_view')

    return redirect('product_detail', pk=pk)


@login_required(login_url='usrlogin')
def cart_view(request):
    """
    Displays items in user's cart with duration breakdown, daily rate, subtotal, and checkout link.
    """
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    subtotal = sum((item.total_amount for item in cart_items), Decimal('0.00'))
    delivery_fee = Decimal('0.00')
    security_deposit = Decimal('0.00')  # Zero security deposit feature of FRICA!
    grand_total = subtotal + delivery_fee
    customer_profile = getattr(request.user, 'customer_profile', None)

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'security_deposit': security_deposit,
        'grand_total': grand_total,
        'customer_profile': customer_profile,
    }
    return render(request, 'cart.html', context)


@login_required(login_url='usrlogin')
def remove_from_cart(request, item_id):
    """
    Removes item from user's cart.
    """
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    product_name = cart_item.product.product_name
    cart_item.delete()
    messages.success(request, f"Removed {product_name} from your cart.")
    return redirect('cart_view')


@login_required(login_url='usrlogin')
def checkout_view(request):
    """
    Checkout & mock payment selection (UPI, Card, Cash on Delivery).
    Generates RentedItems records with 'Waiting for Approval' status.
    """
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    if not cart_items.exists():
        messages.warning(request, "Your rental cart is empty. Please add items before checking out.")
        return redirect('home')

    grand_total = sum((item.total_amount for item in cart_items), Decimal('0.00'))

    customer_profile = getattr(request.user, 'customer_profile', None)
    initial_data = {}
    if customer_profile:
        initial_data['delivery_address'] = customer_profile.address
        initial_data['contact_phone'] = customer_profile.phone

    if request.method == 'POST':
        # Support both CheckoutForm and direct Modal POST
        form = CheckoutForm(request.POST)
        if form.is_valid():
            address = form.cleaned_data['delivery_address']
            phone = form.cleaned_data['contact_phone']
            payment_method = form.cleaned_data['payment_method']
        else:
            address = request.POST.get('delivery_address', '').strip()
            phone = request.POST.get('contact_phone', '').strip()
            payment_method = request.POST.get('payment_method', 'UPI')

        if not address:
            address = (customer_profile.address if customer_profile and customer_profile.address else None) or "Customer Registered Address"
        if not phone:
            phone = (customer_profile.phone if customer_profile and customer_profile.phone else None) or "+91 9876543210"

        # Update customer profile if blank
        if customer_profile:
            if not customer_profile.address and address != "Customer Registered Address":
                customer_profile.address = address
            if not customer_profile.phone and phone != "+91 9876543210":
                customer_profile.phone = phone
            customer_profile.save()

        created_rentals = []
        payment_status = 'Paid'  # Simulated payment gateway marks as PAID

        for item in cart_items:
            rental = RentedItems.objects.create(
                user=request.user,
                product=item.product,
                rent_start_date=item.rent_start_date,
                rent_end_date=item.rent_end_date,
                total_amount=item.total_amount,
                payment_method=payment_method,
                payment_status=payment_status,
                rental_status='Waiting for Approval',
                delivery_address=address,
                contact_phone=phone,
            )
            created_rentals.append(rental)

        # Clear user's cart
        cart_items.delete()

        first_order_id = created_rentals[0].rental_id if created_rentals else ""
        messages.success(
            request,
            f"Payment simulation successful! Order #{first_order_id} has been confirmed with status 'Waiting for Approval'."
        )
        return redirect('user_dashboard')
    else:
        form = CheckoutForm(initial=initial_data)

    context = {
        'cart_items': cart_items,
        'grand_total': grand_total,
        'form': form,
    }
    return render(request, 'checkout.html', context)


@login_required(login_url='usrlogin')
def user_dashboard(request):
    """
    User dashboard displaying active rentals, pending approvals, rental history, and receipt downloads.
    """
    rentals = RentedItems.objects.filter(user=request.user).select_related('product')
    
    waiting_count = rentals.filter(rental_status='Waiting for Approval').count()
    active_count = rentals.filter(rental_status='Active').count()
    returned_count = rentals.filter(rental_status='Returned').count()

    context = {
        'rentals': rentals,
        'waiting_count': waiting_count,
        'active_count': active_count,
        'returned_count': returned_count,
    }
    return render(request, 'user_dashboard.html', context)


@login_required(login_url='usrlogin')
def rental_receipt(request, rental_id):
    """
    Printable and downloadable rental invoice & receipt.
    """
    if request.user.is_staff:
        rental = get_object_or_404(RentedItems, rental_id=rental_id)
    else:
        rental = get_object_or_404(RentedItems, rental_id=rental_id, user=request.user)

    context = {
        'rental': rental,
        'today': timezone.now(),
    }
    return render(request, 'receipt.html', context)


@login_required(login_url='usrlogin')
def cancel_rental(request, rental_id):
    """
    Allows user to cancel a rental request while it is still 'Waiting for Approval'.
    """
    rental = get_object_or_404(RentedItems, rental_id=rental_id, user=request.user)
    if rental.rental_status == 'Waiting for Approval':
        rental.rental_status = 'Cancelled'
        if rental.payment_status == 'Paid':
            rental.payment_status = 'Pending'  # Refund initiated simulation
        rental.save()
        messages.info(request, f"Rental order {rental_id} has been cancelled.")
    else:
        messages.error(request, "This rental order cannot be cancelled at its current status.")
    return redirect('user_dashboard')


def usrregister(request):
    """
    User registration view, creating both User and Customer profile records.
    Automatically logs in the customer and redirects to the dashboard to complete KYC.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard_view')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            phone = form.cleaned_data.get('phone')
            address = form.cleaned_data.get('address')
            Customer.objects.create(
                user=user,
                phone=phone,
                address=address
            )

            login(request, user)
            messages.success(request, f"Welcome to FRICA, {user.first_name or user.username}! Your account has been created. Please complete your identity verification below.")
            return redirect('user_dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def usrlogin(request):
    """
    Unified User & Staff authentication view supporting both username and email login.
    - If staff / superuser: redirects directly to admin_dashboard_view.
    - If standard customer: redirects to next_url, user_dashboard, or catalog.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard_view')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            login_id = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']

            # Support login with either username or email
            username = login_id
            if '@' in login_id:
                try:
                    user_obj = User.objects.get(email__iexact=login_id)
                    username = user_obj.username
                except User.DoesNotExist:
                    pass

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_staff or user.is_superuser:
                    messages.success(request, f"Welcome to Staff Portal, {user.first_name or user.username}!")
                    return redirect('admin_dashboard_view')
                else:
                    messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                    next_url = request.GET.get('next') or request.POST.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('user_dashboard')
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def usrlogout(request):
    """
    Logs out user and redirects back to the login page with a success confirmation.
    """
    logout(request)
    messages.success(request, "You have been logged out successfully. Sign in again below.")
    return redirect('usrlogin')


# Convenient view aliases
user_login_view = usrlogin
user_logout_view = usrlogout


@login_required(login_url='usrlogin')
def kyc_verification(request):
    """Handle KYC document submission and redirect to dashboard.

    Allows customers to upload Aadhaar, PAN, or Driving License images.
    On successful POST the status is set to PENDING and a success message
    is shown on the dashboard.
    """
    # Ensure a Customer profile exists for the logged‑in user
    customer, _ = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = KYCUploadForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            customer.kyc_status = 'PENDING'
            customer.save()
            messages.success(request, "Your documents have been submitted for verification. You will be notified once approved.")
            return redirect('user_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = KYCUploadForm(instance=customer)

    return render(request, 'kyc_verify.html', {'form': form, 'customer': customer})

@login_required(login_url='usrlogin')
def request_rental_extension(request, rental_id):
    """Handle extension requests for an active rental.
    Expects POST with 'extra_days'. Updates dates, amount, and records extension.
    """
    rental = get_object_or_404(RentedItems, rental_id=rental_id)
    # Authorization
    if not (request.user.is_staff or rental.user == request.user):
        messages.error(request, "You are not authorized to modify this rental.")
        return redirect('user_dashboard')
    if rental.rental_status != 'Active':
        messages.error(request, "Only active rentals can be extended.")
        return redirect('user_dashboard')
    if request.method == 'POST':
        try:
            extra_days = int(request.POST.get('extra_days', 0))
        except (ValueError, TypeError):
            messages.error(request, "Please provide a valid number of days.")
            return redirect('request_rental_extension', rental_id=rental_id)
        if extra_days <= 0:
            messages.error(request, "Extension days must be greater than zero.")
            return redirect('request_rental_extension', rental_id=rental_id)
        # Compute new dates and cost
        new_end_date = rental.rent_end_date + timedelta(days=extra_days)
        extra_cost = rental.product.rent_price * extra_days
        # Update fields
        rental.rent_end_date = new_end_date
        rental.is_extension_requested = True
        rental.extended_days = (rental.extended_days or 0) + extra_days
        rental.extension_amount = (rental.extension_amount or Decimal('0.00')) + extra_cost
        rental.total_amount = (rental.total_amount or Decimal('0.00')) + extra_cost
        rental.save()
        messages.success(request, f"Rental extended by {extra_days} days. Additional charge ₹{extra_cost:.2f} applied.")
        return redirect('user_dashboard')
    else:
        return render(request, 'request_extension.html', {'rental': rental})


@login_required(login_url='usrlogin')
def request_rental_return(request, rental_id):
    """Mark an active rental as return requested.
    Sets return_status to 'RETURN_REQUESTED'.
    """
    rental = get_object_or_404(RentedItems, rental_id=rental_id)
    if not (request.user.is_staff or rental.user == request.user):
        messages.error(request, "You are not authorized to modify this rental.")
        return redirect('user_dashboard')
    if rental.rental_status != 'Active':
        messages.error(request, "Only active rentals can be returned.")
        return redirect('user_dashboard')
    rental.return_status = 'RETURN_REQUESTED'
    rental.save()
    messages.success(request, "Return request submitted. Our team will arrange pickup shortly.")
    return redirect('user_dashboard')


def category_view(request, category_name):
    """
    Displays products filtered by category name with full brand and sorting support.
    """
    get_params = request.GET.copy()
    get_params['category'] = category_name
    request.GET = get_params
    return home(request)


@login_required(login_url='usrlogin')
def user_details(request):
    """
    User details & profile view matching screenshot 12.2.3:
    Avatar on the left with username/email, and detail fields on the right:
    Name, Gender, Marital Status, Occupation, Email, Annual Income, Aadhar, PAN.
    """
    customer, _ = Customer.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        if first_name or last_name:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.save()

        customer.phone = request.POST.get('phone', customer.phone)
        customer.address = request.POST.get('address', customer.address)
        customer.gender = request.POST.get('gender', customer.gender)
        customer.marital_status = request.POST.get('marital_status', customer.marital_status)
        customer.occupation = request.POST.get('occupation', customer.occupation)

        income_str = request.POST.get('annual_income')
        if income_str:
            try:
                customer.annual_income = Decimal(income_str)
            except Exception:
                pass

        customer.aadhar_number = request.POST.get('aadhar_number', customer.aadhar_number)
        customer.pan_number = request.POST.get('pan_number', customer.pan_number)

        if 'profile_pic' in request.FILES:
            customer.profile_pic = request.FILES['profile_pic']

        customer.save()
        messages.success(request, "Profile details updated successfully!")
        return redirect('user_details')

    context = {
        'customer': customer,
        'user': request.user,
    }
    return render(request, 'user_details.html', context)


# ==============================================================================
# CUSTOM ADMIN & STAFF PORTAL VIEWS
# ==============================================================================

def admin_login_view(request):
    """
    Staff / Administrator login view.
    Authenticates user and ensures `user.is_staff`.
    """
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard_view')

    if request.method == 'POST':
        login_id = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        username = login_id
        if '@' in login_id:
            try:
                user_obj = User.objects.get(email__iexact=login_id)
                username = user_obj.username
            except User.DoesNotExist:
                pass

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                messages.success(request, f"Welcome to the Staff Portal, {user.first_name or user.username}!")
                return redirect('admin_dashboard_view')
            else:
                messages.error(request, "Access denied. Your account does not have staff administrator privileges.")
                return redirect('admin_login_view')
        else:
            messages.error(request, "Invalid administrator credentials. Please try again.")
            return redirect('admin_login_view')

    return render(request, 'admin_login.html')


@login_required(login_url='admin_login_view')
def admin_dashboard_view(request):
    """
    FRICA Staff & Admin Management Dashboard:
    - Stat Metrics: Total Bookings, Pending KYC, Waiting Approvals, Active Rentals.
    - KYC Verification Requests: View details/images & Approve/Reject.
    - Rental Orders: Approve (Active in-hand), Mark Returned, or Cancel.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Staff administrator privileges required to access the management portal.")
        return redirect('admin_login_view')

    total_bookings = RentedItems.objects.count()
    pending_kyc = Customer.objects.filter(kyc_status='PENDING').count()
    waiting_approvals = RentedItems.objects.filter(rental_status='Waiting for Approval').count()
    active_rentals = RentedItems.objects.filter(rental_status='Active').count()

    kyc_list = Customer.objects.all().select_related('user').order_by(
        models.Case(
            models.When(kyc_status='PENDING', then=0),
            models.When(kyc_status='VERIFIED', then=1),
            models.When(kyc_status='REJECTED', then=2),
            default=3,
            output_field=models.IntegerField(),
        ),
        '-kyc_submitted_at'
    )

    orders = RentedItems.objects.all().select_related('user', 'product').order_by('-created_at')

    context = {
        'total_bookings': total_bookings,
        'pending_kyc': pending_kyc,
        'waiting_approvals': waiting_approvals,
        'active_rentals': active_rentals,
        'kyc_list': kyc_list,
        'orders': orders,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required(login_url='admin_login_view')
def admin_approve_kyc_view(request, customer_id):
    """
    One-click KYC approval / rejection action for staff.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Staff administrator privileges required.")
        return redirect('admin_login_view')

    customer = get_object_or_404(Customer, id=customer_id)
    action = request.GET.get('action') or request.POST.get('action', 'approve')

    if action.lower() in ['approve', 'verified', 'verify']:
        customer.kyc_status = 'VERIFIED'
        customer.save()
        messages.success(request, f"KYC verified successfully for customer: {customer.user.username}.")
    else:
        customer.kyc_status = 'REJECTED'
        customer.save()
        messages.warning(request, f"KYC marked as Rejected for customer: {customer.user.username}.")

    return redirect('admin_dashboard_view')


@login_required(login_url='admin_login_view')
def admin_update_order_status_view(request, order_id, status):
    """
    Updates rental order lifecycle status:
    - 'Active' / 'approve': Customer received the gadget.
    - 'Returned': Gadget inspected and returned.
    - 'Cancelled': Order cancelled.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Staff administrator privileges required.")
        return redirect('admin_login_view')

    order = get_object_or_404(RentedItems, rental_id=order_id)
    status_lower = status.lower()

    if status_lower in ['active', 'approve', 'approved']:
        order.rental_status = 'Active'
        messages.success(request, f"Order #{order.rental_id} approved. Gadget is now Active in-hand with customer.")
    elif status_lower in ['returned', 'return']:
        order.rental_status = 'Returned'
        order.return_status = 'RETURN_COMPLETED'
        messages.success(request, f"Order #{order.rental_id} marked as Returned & Inspected.")
    elif status_lower in ['cancelled', 'cancel']:
        order.rental_status = 'Cancelled'
        messages.info(request, f"Order #{order.rental_id} has been cancelled.")
    else:
        order.rental_status = status
        messages.info(request, f"Order #{order.rental_id} status updated to {status}.")

    order.save()
    return redirect('admin_dashboard_view')


# ==============================================================================
# WISHLIST SYSTEM (AJAX Toggle, Dedicated Page, Move to Cart, Remove)
# ==============================================================================

def toggle_wishlist_view(request, pk):
    """
    AJAX endpoint to add or remove a gadget from user's wishlist without page refresh.
    Returns JSON response with updated action, wishlist_count, and status.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'login_required': True,
            'message': 'Please log in to add items to your wishlist.',
            'login_url': reverse('usrlogin'),
        }, status=401)

    product = get_object_or_404(Products, pk=pk)
    wishlist_entry = Wishlist.objects.filter(user=request.user, gadget=product).first()

    if wishlist_entry:
        wishlist_entry.delete()
        action = 'removed'
        is_wishlisted = False
        message = f"Removed '{product.product_name}' from your wishlist."
    else:
        Wishlist.objects.create(user=request.user, gadget=product)
        action = 'added'
        is_wishlisted = True
        message = f"Added '{product.product_name}' to your wishlist!"

    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return JsonResponse({
        'success': True,
        'action': action,
        'is_wishlisted': is_wishlisted,
        'wishlist_count': wishlist_count,
        'product_id': pk,
        'product_name': product.product_name,
        'message': message,
    })


@login_required(login_url='usrlogin')
def wishlist_page_view(request):
    """
    Renders dedicated Flipkart/Amazon style wishlist page with all saved gadgets.
    """
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('gadget').order_by('-created_at')
    
    return render(request, 'wishlist.html', {
        'wishlist_items': wishlist_items,
        'total_items': wishlist_items.count(),
    })


@login_required(login_url='usrlogin')
def remove_from_wishlist(request, pk):
    """
    Standard view to remove item from wishlist (used in wishlist page buttons).
    """
    product = get_object_or_404(Products, pk=pk)
    Wishlist.objects.filter(user=request.user, gadget=product).delete()
    messages.info(request, f"'{product.product_name}' removed from your wishlist.")
    return redirect('wishlist_page_view')


@login_required(login_url='usrlogin')
def move_to_cart_from_wishlist(request, pk):
    """
    One-click move from wishlist to shopping cart with default 2-day rental period,
    then automatically redirects to the cart view.
    """
    product = get_object_or_404(Products, pk=pk)

    if not product.availability:
        messages.error(request, f"Sorry, {product.product_name} is currently out of stock.")
        return redirect('wishlist_page_view')

    today = timezone.localdate()
    end_date = today + timedelta(days=2)

    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={
            'rent_start_date': today,
            'rent_end_date': end_date,
            'total_days': 2,
            'total_amount': product.rent_price * 2,
        }
    )

    if not created:
        cart_item.rent_start_date = today
        cart_item.rent_end_date = end_date
        cart_item.calculate_totals()
        cart_item.save()

    # Remove from wishlist once moved to cart
    Wishlist.objects.filter(user=request.user, gadget=product).delete()

    messages.success(request, f"'{product.product_name}' moved to your rental cart!")
    return redirect('cart_view')


# ==============================================================================
# FEATURE 1: AI SMART TECH MATCHER API & CURATED KIT HANDLER
# ==============================================================================

def api_smart_match(request):
    """
    AI Smart Tech Matcher API endpoint.
    Accepts:
      - purpose: 'gaming', 'photography', 'coding', 'movie', 'travel'
      - budget: 'low' (<500/day), 'mid' (500-1500/day), 'premium' (>1500/day)
    Returns JSON with matching primary gadget, recommended accessory bundle, score, and explanation.
    """
    purpose = request.GET.get('purpose', 'gaming').strip().lower()
    budget = request.GET.get('budget', 'mid').strip().lower()

    qs = Products.objects.filter(availability=True)

    # Budget filtering
    if budget == 'low':
        budget_qs = qs.filter(rent_price__lte=499)
    elif budget == 'premium':
        budget_qs = qs.filter(rent_price__gte=999)
    else:  # mid
        budget_qs = qs.filter(rent_price__gte=400, rent_price__lte=1500)

    if not budget_qs.exists():
        budget_qs = qs

    score = 98
    reason = ""

    if purpose == 'gaming':
        primary_gadget = budget_qs.filter(
            Q(category__in=['Laptop', 'Computers']) &
            (Q(product_name__icontains='gaming') | Q(product_name__icontains='tuf') | Q(product_name__icontains='victus') | Q(product_name__icontains='legion') | Q(product_name__icontains='rtx') | Q(specs__icontains='rtx') | Q(category='Laptop'))
        ).first() or qs.filter(category='Laptop').first()
        accessory_gadget = qs.filter(category='Audio').first()
        score = 99
        reason = "Equipped with high-refresh display and dedicated ray-tracing GPU for ultra-smooth competitive gaming and esports performance."

    elif purpose == 'photography':
        primary_gadget = budget_qs.filter(category='Camera').first() or qs.filter(category='Camera').first()
        accessory_gadget = qs.filter(category='Mobiles').order_by('-rent_price').first()
        score = 97
        reason = "Equipped with cinema-grade sensor dynamic range, optical stabilization, and 4K/8K RAW recording capabilities."

    elif purpose == 'coding':
        primary_gadget = budget_qs.filter(
            Q(category='Laptop') & (Q(product_name__icontains='macbook') | Q(product_name__icontains='apple') | Q(product_name__icontains='hp') | Q(product_name__icontains='pro'))
        ).first() or qs.filter(category='Laptop').first()
        accessory_gadget = qs.filter(category='Audio').first()
        score = 98
        reason = "Blazing multi-core compilation throughput, extensive RAM, and crisp Retina/OLED display tailored for developers."

    elif purpose == 'movie':
        primary_gadget = budget_qs.filter(category='TV').first() or qs.filter(category='TV').first()
        accessory_gadget = qs.filter(category='Audio').first()
        score = 96
        reason = "Infinite OLED contrast, cinema Dolby Vision HDR, and immersive room-filling spatial surround sound."

    else:  # travel & roadtrip
        primary_gadget = budget_qs.filter(
            Q(category__in=['Mobiles', 'Camera', 'Watches'])
        ).order_by('-rent_price').first() or qs.filter(category='Mobiles').first()
        accessory_gadget = qs.filter(category='Watches').first()
        score = 95
        reason = "Weather-sealed compact body, flagship camera zoom lenses, and long battery endurance for vacations and content capture."

    if not primary_gadget:
        primary_gadget = qs.first()

    def serialize_gadget(g):
        if not g:
            return None
        return {
            'id': g.id,
            'name': g.product_name,
            'brand': g.brand or g.category,
            'category': g.category,
            'rent_price': float(g.rent_price),
            'market_value': g.estimated_market_value,
            'rating': float(g.rating or 4.8),
            'reviews_count': g.reviews_count or 48,
            'image_url': g.get_image_url or (g.image.url if g.image else ''),
            'specs_preview': [f"{s['key']}: {s['value']}" for s in g.specs_preview],
        }

    p_data = serialize_gadget(primary_gadget)
    a_data = serialize_gadget(accessory_gadget)

    bundled_price = float(primary_gadget.rent_price) if primary_gadget else 0
    if accessory_gadget:
        bundled_price += float(accessory_gadget.rent_price)

    discounted_price = round(bundled_price * 0.85, 0)

    return JsonResponse({
        'success': True,
        'purpose': purpose,
        'budget': budget,
        'score': score,
        'reason': reason,
        'primary_gadget': p_data,
        'accessory_gadget': a_data,
        'bundled_price': bundled_price,
        'discounted_price': discounted_price,
        'savings_percent': 15,
    })


@login_required(login_url='usrlogin')
def add_curated_kit(request):
    """
    One-click action to add primary gadget and accessory bundle to cart,
    reserving them for a standard 2-day period with celebratory redirect to cart.
    """
    primary_id = request.POST.get('primary_id') or request.GET.get('primary_id')
    accessory_id = request.POST.get('accessory_id') or request.GET.get('accessory_id')

    if not primary_id:
        messages.error(request, "No gadget selected.")
        return redirect('home')

    today = timezone.localdate()
    end_date = today + timedelta(days=2)

    added_names = []
    for pid in [primary_id, accessory_id]:
        if pid:
            try:
                prod = Products.objects.get(pk=pid, availability=True)
                cart_item, created = Cart.objects.get_or_create(
                    user=request.user,
                    product=prod,
                    defaults={
                        'rent_start_date': today,
                        'rent_end_date': end_date,
                        'total_days': 2,
                        'total_amount': prod.rent_price * 2,
                    }
                )
                if not created:
                    cart_item.rent_start_date = today
                    cart_item.rent_end_date = end_date
                    cart_item.calculate_totals()
                    cart_item.save()
                added_names.append(prod.product_name)
            except (Products.DoesNotExist, ValueError):
                pass

    if added_names:
        messages.success(request, f"✨ AI Curated Kit added to your rental cart: {' + '.join(added_names)}!")
    else:
        messages.error(request, "Selected kit items are currently unavailable.")

    return redirect('cart_view')


# ==============================================================================
# FEATURE 2: SMART RENT-TO-OWN (TRY BEFORE YOU BUY) CALCULATOR
# ==============================================================================

def apply_buyout_inquiry(request, pk):
    """
    Simulates or registers a Rent-to-Own Buyout calculation.
    Calculates 70% equity credit applied toward full purchase price.
    """
    product = get_object_or_404(Products, pk=pk)
    try:
        days = int(request.GET.get('days') or request.POST.get('days') or 30)
    except (ValueError, TypeError):
        days = 30

    market_val = product.estimated_market_value
    rent_paid = float(product.rent_price) * days
    equity_credit = round(rent_paid * 0.70, 2)
    buyout_price = max(0, round(market_val - equity_credit, 2))

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.product_name,
            'market_value': market_val,
            'days': days,
            'rent_paid': rent_paid,
            'equity_credit': equity_credit,
            'buyout_price': buyout_price,
            'savings': round(rent_paid * 0.30, 2),
        })

    messages.success(
        request,
        f"💡 Rent-to-Own Simulation for '{product.product_name}': After {days} days of rental, you get ₹{equity_credit:,.0f} credited! You can own it for just ₹{buyout_price:,.0f}."
    )
    return redirect('product_detail', pk=pk)






