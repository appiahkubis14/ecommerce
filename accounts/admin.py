from django.contrib import admin
from .models import Profile, Cart, CartItem, Order, OrderItem,ShippingAddress

# Register your models here.

admin.site.register(Profile)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'city', 'country', 'phone')
    search_fields = ('user__username', 'first_name', 'last_name', 'city')
