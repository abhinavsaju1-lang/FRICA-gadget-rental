from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from .models import Products, Customer, Cart, RentedItems
from .forms import RegistrationForm, UserLoginForm, AddToCartForm, CheckoutForm, KYCUploadForm


def home(request):
    """
    Homepage displaying gadget catalog with category filter pills and dynamic search bar.
    """
    category_filter = request.GET.get('category', 'All')
    search_query = request.GET.get('q', '').strip()

    products = Products.objects.filter(availability=True)

    if category_filter and category_filter != 'All':
        products = products.filter(category=category_filter)

    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    categories = [
        {'name': 'All',       'icon': 'bi-grid-fill'},
        {'name': 'Mobiles',   'icon': 'bi-phone-fill'},
        {'name': 'Laptop',    'icon': 'bi-laptop'},
        {'name': 'Camera',    'icon': 'bi-camera-fill'},
        {'name': 'TV',        'icon': 'bi-tv-fill'},
        {'name': 'Watches',   'icon': 'bi-smartwatch'},
        {'name': 'Computers', 'icon': 'bi-pc-display'},
    ]

    features = [
        {
            'icon': 'bi-wallet2',
            'icon_bg': 'bg-primary bg-opacity-10',
            'icon_color': 'text-primary',
            'title': 'Affordable Daily Rates',
            'sub': 'Pay only for the days you use',
        },
        {
            'icon': 'bi-shield-lock',
            'icon_bg': 'bg-success bg-opacity-10',
            'icon_color': 'text-success',
            'title': 'Zero Security Deposit',
            'sub': 'KYC-verified rentals, no cash lock-in',
        },
        {
            'icon': 'bi-arrow-repeat',
            'icon_bg': 'bg-warning bg-opacity-10',
            'icon_color': 'text-warning',
            'title': 'Flexible Tenure',
            'sub': 'Extend, shorten, or return anytime',
        },
        {
            'icon': 'bi-box-seam',
            'icon_bg': 'bg-info bg-opacity-10',
            'icon_color': 'text-info',
            'title': 'Doorstep Delivery',
            'sub': 'Hassle-free delivery & pickup',
        },
    ]

    context = {
        'products': products,
        'current_category': category_filter,
        'search_query': search_query,
        'categories': categories,
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
    """
    if request.user.is_authenticated:
        return redirect('home')

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
            messages.success(request, f"Welcome to FRICA, {user.first_name or user.username}! Your account has been created.")
            return redirect('home')
    else:
        form = RegistrationForm()

    return render(request, 'register.html', {'form': form})


def usrlogin(request):
    """
    User authentication view supporting both username and email login.
    """
    if request.user.is_authenticated:
        return redirect('home')

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
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('home')
            else:
                messages.error(request, "Invalid username/email or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def usrlogout(request):
    """
    Logs out user and redirects to home with confirmation.
    """
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('home')

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
    Displays products filtered by category name.
    """
    categories = [
        {'name': 'All',       'icon': 'bi-grid-fill'},
        {'name': 'Mobiles',   'icon': 'bi-phone-fill'},
        {'name': 'Computers', 'icon': 'bi-pc-display'},
        {'name': 'Camera',    'icon': 'bi-camera-fill'},
        {'name': 'Laptop',    'icon': 'bi-laptop'},
        {'name': 'TV',        'icon': 'bi-tv-fill'},
        {'name': 'Watches',   'icon': 'bi-smartwatch'},
    ]

    products = Products.objects.filter(availability=True)
    if category_name and category_name.lower() != 'all':
        products = products.filter(category__iexact=category_name)

    context = {
        'products': products,
        'current_category': category_name,
        'categories': categories,
        'total_count': products.count(),
    }
    return render(request, 'home.html', context)


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



