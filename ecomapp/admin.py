from django.contrib import admin
from .models import Customer, Products, Cart, RentedItems


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'phone', 'address')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'category', 'rent_price', 'availability', 'created_at')
    list_filter = ('category', 'availability', 'created_at')
    search_fields = ('product_name', 'description')
    list_editable = ('rent_price', 'availability')
    actions = ['make_available', 'make_unavailable']

    @admin.action(description='Mark selected products as Available')
    def make_available(self, request, queryset):
        queryset.update(availability=True)

    @admin.action(description='Mark selected products as Unavailable')
    def make_unavailable(self, request, queryset):
        queryset.update(availability=False)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'rent_start_date', 'rent_end_date', 'total_days', 'total_amount', 'created_at')
    list_filter = ('rent_start_date', 'created_at')
    search_fields = ('user__username', 'product__product_name')


@admin.register(RentedItems)
class RentedItemsAdmin(admin.ModelAdmin):
    list_display = ('rental_id', 'product', 'user', 'rent_start_date', 'rent_end_date', 'total_amount', 'payment_status', 'rental_status', 'created_at')
    list_filter = ('rental_status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('rental_id', 'user__username', 'user__email', 'product__product_name', 'contact_phone')
    list_editable = ('rental_status', 'payment_status')
    actions = ['approve_rentals', 'mark_as_active', 'mark_as_returned', 'cancel_rentals']

    @admin.action(description='Approve selected rentals (Set to Active & Paid)')
    def approve_rentals(self, request, queryset):
        queryset.update(rental_status='Active', payment_status='Paid')

    @admin.action(description='Mark selected rentals as Active')
    def mark_as_active(self, request, queryset):
        queryset.update(rental_status='Active')

    @admin.action(description='Mark selected rentals as Returned')
    def mark_as_returned(self, request, queryset):
        queryset.update(rental_status='Returned')

    @admin.action(description='Cancel selected rentals')
    def cancel_rentals(self, request, queryset):
        queryset.update(rental_status='Cancelled')
