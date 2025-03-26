from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product
from django.conf import settings
import os


class ShippingAddress(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="shipping_address"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    street_number = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    current_address = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.street}, {self.city}"


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to="profile", null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, related_name="profiles", null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.profile_image and old_profile.profile_image != self.profile_image:
                    old_image_path = os.path.join(
                        settings.MEDIA_ROOT, old_profile.profile_image.path
                    )
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Profile.DoesNotExist:
                pass

        super(Profile, self).save(*args, **kwargs)


class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    paystack_reference = models.CharField(max_length=100, null=True, blank=True)
    paystack_status = models.CharField(max_length=100, null=True, blank=True)

    def get_cart_total(self):
        return sum(cart_item.get_product_price() for cart_item in self.cart_items.all())


class CartItem(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE, related_name="cart_shipping_address", null=True, blank=True)
    quantity = models.IntegerField(default=1)

    def get_product_price(self):
        return self.product.price * self.quantity if self.product else 0


class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=100)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_shipping")
    payment_mode = models.CharField(max_length=100)
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paystack_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"

    def get_order_total_price(self):
        return self.order_total_price

    def save(self, *args, **kwargs):
        """Ensure that the order automatically retrieves the user's shipping address if available."""
        if not self.shipping_address and self.user.profile and self.user.profile.shipping_address:
            self.shipping_address = self.user.profile.shipping_address
        super(Order, self).save(*args, **kwargs)



class OrderItem(BaseModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="order_items")
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE, related_name="order_shipping_address")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def get_total_price(self):
        return self.product_price * self.quantity if self.product_price else 0
