from .models import Cart,Order

def cart_item_count(request):
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            return {'cart_item_count': cart.get_total_items()}
        except Cart.DoesNotExist:
            return {'cart_item_count': 0}
    return {'cart_item_count': 0}