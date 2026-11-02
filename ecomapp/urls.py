from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('receipt/<str:rental_id>/', views.rental_receipt, name='rental_receipt'),
    path('rental/cancel/<str:rental_id>/', views.cancel_rental, name='cancel_rental'),
    path('register/', views.usrregister, name='usrregister'),
    path('login/', views.usrlogin, name='usrlogin'),
    path('logout/', views.usrlogout, name='usrlogout'),
    path('kyc/', views.kyc_verification, name='kyc_verification'),
    path('category/<str:category_name>/', views.category_view, name='category'),
    path('user_details/', views.user_details, name='user_details'),
    path('profile/', views.user_details, name='user_profile'),
    # Rental extension & return workflow
    path('rental/<str:rental_id>/extend/', views.request_rental_extension, name='extend_rental'),
    path('rental/<str:rental_id>/return/', views.request_rental_return, name='return_rental'),
]
