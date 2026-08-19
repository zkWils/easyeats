from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Restaurant, Category, Dish, Order, OrderItem

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    pass

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'category', 'price')
    list_filter = ('restaurant', 'category')
    prepopulated_fields = {'slug': ('name',)}

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['dish']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'delivery_location', 'total_amount', 'created_at')
    list_filter = ('status', 'delivery_location', 'created_at')
    inlines = [OrderItemInline]