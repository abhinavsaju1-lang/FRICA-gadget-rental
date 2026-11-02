from .models import Cart

def cart_counter(request):
    """
    Context processor to pass cart_count globally to templates.
    """
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
    return {'cart_count': cart_count}
