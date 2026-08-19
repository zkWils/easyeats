from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Restaurant, Category, Dish, Cart, CartItem, Order, OrderItem

def home(request):
    categories = Category.objects.all()
    restaurants = Restaurant.objects.all()
    
    query = request.GET.get('q', '').strip()
    selected_category_slug = request.GET.get('category')
    
    dishes = Dish.objects.filter(is_available=True)
    
    if query:
        dishes = dishes.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(restaurant__name__icontains=query)
        )
    
    if selected_category_slug:
        dishes = dishes.filter(category__slug=selected_category_slug)

    context = {
        'categories': categories,
        'restaurants': restaurants,
        'dishes': dishes,
        'selected_category': selected_category_slug,
        'query': query,
    }
    return render(request, 'food_orders/home.html', context)


def update_cart_quantity(request, item_id, action):
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            messages.info(request, f"Removed {cart_item.dish.name} from cart.")
            
    return redirect('cart_detail')

def restaurant_detail(request, slug):
    restaurant = get_object_or_404(Restaurant, slug=slug)
    dishes = restaurant.dishes.filter(is_available=True)
    categories = Category.objects.filter(dishes__restaurant=restaurant).distinct()

    context = {
        'restaurant': restaurant,
        'dishes': dishes,
        'categories': categories,
    }
    return render(request, 'food_orders/restaurant_detail.html', context)


def _get_or_create_cart(request):
    """Helper function to retrieve or initialize a cart in the session."""
    cart_id = request.session.get('cart_id')
    if cart_id:
        try:
            return Cart.objects.get(id=cart_id)
        except Cart.DoesNotExist:
            pass
            
    cart = Cart.objects.create()
    request.session['cart_id'] = str(cart.id)
    return cart


def add_to_cart(request, dish_id):
    cart = _get_or_create_cart(request)
    dish = get_object_or_404(Dish, id=dish_id)
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, dish=dish)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
        messages.info(request, f"Updated quantity for {dish.name}.")
    else:
        messages.success(request, f"Added {dish.name} to your cart!")
        
    return redirect(request.META.get('HTTP_REFERER', 'home'))


def cart_detail(request):
    cart = _get_or_create_cart(request)
    return render(request, 'food_orders/cart.html', {'cart': cart})


def remove_from_cart(request, item_id):
    cart = _get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')


def checkout(request):
    cart = _get_or_create_cart(request)
    if not cart.items.exists():
        return redirect('cart_detail')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        delivery_address = request.POST.get('delivery_address')

        total_price = cart.total_price() if callable(getattr(cart, 'total_price', None)) else cart.total_price

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone_number=phone_number,
            delivery_address=delivery_address,
            total_amount=total_price
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                dish=item.dish,
                price=item.dish.price,
                quantity=item.quantity
            )

        cart.delete()

        if 'cart_id' in request.session:
            del request.session['cart_id']

        messages.success(request, "Your order has been placed successfully!")
        return redirect('order_success', order_id=order.id)

    initial_data = {}
    if request.user.is_authenticated:
        initial_data = {
            'full_name': request.user.get_full_name() or request.user.username,
            'phone_number': getattr(request.user, 'phone_number', ''),
            'delivery_address': getattr(request.user, 'delivery_address', ''),
        }

    return render(request, 'food_orders/checkout.html', {'cart': cart, 'initial_data': initial_data})


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'food_orders/order_success.html', {'order': order})


from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'food_orders/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
        
    return render(request, 'food_orders/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'food_orders/my_orders.html', {'orders': orders})


from .models import Restaurant, Table, Reservation, ReservationItem, Cart
from django.utils.dateparse import parse_datetime

def make_reservation(request, restaurant_slug):
    restaurant = get_object_or_404(Restaurant, slug=restaurant_slug)
    cart = Cart.objects.filter(user=request.user).first() if request.user.is_authenticated else None

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        res_datetime_str = request.POST.get('reservation_datetime')  # From <input type="datetime-local">
        res_datetime = parse_datetime(res_datetime_str)
        
        table_id = request.POST.get('table_id')
        seat_number = int(request.POST.get('seat_number'))  # 1 to 4
        
        table = Table.objects.get(id=table_id, restaurant=restaurant)

        reservation = Reservation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            restaurant=restaurant,
            table=table,
            seat_number=seat_number,
            full_name=full_name,
            phone_number=phone_number,
            reservation_datetime=res_datetime
        )

        if cart and cart.items.exists():
            for item in cart.items.all():
                ReservationItem.objects.create(
                    reservation=reservation,
                    dish=item.dish,
                    quantity=item.quantity,
                    price=item.dish.price
                )
            cart.items.all().delete()

        return redirect('reservation_detail', reservation_id=reservation.id)

    tables = restaurant.tables.all()
    return render(request, 'food_orders/make_reservation.html', {
        'restaurant': restaurant,
        'tables': tables,
        'cart': cart
    })

def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    return render(request, 'food_orders/reservation_detail.html', {'reservation': reservation})

def my_reservations(request):
    if not request.user.is_authenticated:
        return redirect('login')
    reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'food_orders/my_reservations.html', {'reservations': reservations})