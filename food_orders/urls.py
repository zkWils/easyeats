from django.urls import path
from . import views

# app_name = 'food_orders'

urlpatterns = [
    path('', views.home, name='home'),
    path('restaurant/<slug:slug>/', views.restaurant_detail, name='restaurant_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:dish_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    
    path('restaurant/<slug:restaurant_slug>/reserve/', views.make_reservation, name='make_reservation'),
    path('reservation/<int:reservation_id>/', views.reservation_detail, name='reservation_detail'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    
    # Auth & Profile
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-orders/', views.my_orders, name='my_orders'),
]