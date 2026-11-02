from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Customer, Cart, RentedItems


class RegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Last Name'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'name@example.com'
    }))
    phone = forms.CharField(max_length=15, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Contact Phone Number (e.g. +91 9876543210)'
    }))
    address = forms.CharField(required=True, widget=forms.Textarea(attrs={
        'class': 'form-control', 'rows': 3, 'placeholder': 'Complete Residential/Delivery Address'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Create strong password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Confirm your password'
    }))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose unique username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Username or Email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control form-control-lg', 'placeholder': 'Password'
    }))


class AddToCartForm(forms.ModelForm):
    class Meta:
        model = Cart
        fields = ['rent_start_date', 'rent_end_date']
        widgets = {
            'rent_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'rent_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('rent_start_date')
        end = cleaned_data.get('rent_end_date')
        today = timezone.localdate()

        if start and start < today:
            self.add_error('rent_start_date', "Start date cannot be in the past.")

        if start and end and end < start:
            self.add_error('rent_end_date', "End date must be equal to or after start date.")

        return cleaned_data


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control', 'rows': 3, 'placeholder': 'Enter doorstep delivery address'
    }), required=True)
    contact_phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Phone number for delivery agent'
    }), required=True)
    payment_method = forms.ChoiceField(
        choices=RentedItems.PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='UPI'
    )


class KYCUploadForm(forms.ModelForm):
    """Form for uploading KYC documents (Aadhaar, PAN, Driving License)."""

    class Meta:
        model = Customer
        fields = [
            'id_proof_type',
            'id_number',
            'id_front_image',
            'id_back_image',
        ]
        widgets = {
            'id_proof_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter document number',
            }),
            'id_front_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'id_back_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
        }
        labels = {
            'id_proof_type': 'Document Type',
            'id_number': 'Document Number',
            'id_front_image': 'Front Side Image',
            'id_back_image': 'Back Side Image',
        }

    def clean(self):
        """Ensure all fields are present on submission."""
        cleaned = super().clean()
        required_fields = ['id_proof_type', 'id_number', 'id_front_image', 'id_back_image']
        for field in required_fields:
            if not cleaned.get(field):
                self.add_error(field, 'This field is required for KYC submission.')
        return cleaned
