from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.text import slugify
import datetime

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username

LOCATION_CHOICES = [
    ('umuchima', 'Umuchima'),
    ('eziobodo', 'Eziobodo'),
    ('ihiagwa', 'Ihiagwa'),
    ('obinze', 'Obinze'),
    ('owerri_town', 'Owerri Town'),
]

TRAVEL_MATRIX = {
    'umuchima':    {'umuchima': 12, 'eziobodo': 18, 'ihiagwa': 15, 'obinze': 30, 'owerri_town': 45},
    'eziobodo':    {'umuchima': 18, 'eziobodo': 12, 'ihiagwa': 15, 'obinze': 32, 'owerri_town': 45},
    'ihiagwa':     {'umuchima': 15, 'eziobodo': 15, 'ihiagwa': 10, 'obinze': 25, 'owerri_town': 40},
    'obinze':      {'umuchima': 30, 'eziobodo': 32, 'ihiagwa': 25, 'obinze': 10, 'owerri_town': 30},
    'owerri_town': {'umuchima': 45, 'eziobodo': 45, 'ihiagwa': 40, 'obinze': 30, 'owerri_town': 15},
}

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='ihiagwa')

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Dish(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='dishes')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='dishes')
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='dishes/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart ({self.user})" if self.user else f"Cart #{self.id}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}x {self.dish.name}"

    @property
    def total_price(self):
        return self.dish.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = [
        ('placed', 'Order Placed'),
        ('preparing', 'Kitchen Preparing'),
        ('on_the_way', 'Out for Delivery'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='orders',
        null=True, 
        blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='placed')
    delivery_location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='ihiagwa')
    delivery_address = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"

    @property
    def estimated_delivery_minutes(self):
        first_item = self.items.first()
        origin = first_item.dish.restaurant.location if (first_item and first_item.dish) else 'ihiagwa'
        dest = self.delivery_location
        prep_time = 15
        travel_time = TRAVEL_MATRIX.get(origin, {}).get(dest, 20)
        return prep_time + travel_time

    @property
    def estimated_arrival_time(self):
        return self.created_at + datetime.timedelta(minutes=self.estimated_delivery_minutes)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.dish.name}"

class Table(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='tables')
    table_number = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField(default=4)  # 4 seats per table

    class Meta:
        unique_together = ('restaurant', 'table_number')

    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number}"

class Reservation(models.Model):

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations', null=True, blank=True)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reservations')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name='reservations')
    seat_number = models.PositiveIntegerField()  # 1 to 4
    
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    
    reservation_datetime = models.DateTimeField()  # Date & time reserved FOR
    created_at = models.DateTimeField(auto_now_add=True)  # Date & time reserved AT
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')

    def __str__(self):
        return f"Reservation #{self.id} at {self.restaurant.name} (Table {self.table.table_number}, Seat {self.seat_number})"

    @property
    def total_meal_amount(self):
        return sum(item.total_price for item in self.items.all())

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
        super().save(*args, **kwargs)


class ReservationItem(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Frozen price per item at booking time

    @property
    def total_price(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.dish.name} (Res #{self.reservation.id})"