from .models import Cart

def cart_counter(request):
    cart_id = request.session.get('cart_id')
    total_items = 0
    
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id)
            total_items = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            pass
            
    return {'cart_total_items': total_items}