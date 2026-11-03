from .models import Cart, Wishlist

def cart_counter(request):
    """
    Context processor to pass cart_count, wishlist_count, and user_wishlist_ids globally to templates.
    """
    cart_count = 0
    wishlist_count = 0
    user_wishlist_ids = set()
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('gadget_id', flat=True))
        wishlist_count = len(user_wishlist_ids)
    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
        'user_wishlist_ids': user_wishlist_ids,
    }
