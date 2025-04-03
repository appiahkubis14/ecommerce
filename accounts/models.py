from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product
from django.conf import settings
import os
import uuid
from django.urls import reverse
from django.db import models
from django import forms
from django_countries.fields import CountryField
from django.utils.timezone import now




from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

class ShippingAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')  # ForeignKey to User
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    street = models.CharField(max_length=200)
    street_number = models.CharField(max_length=200)
    zip_code = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    country = CountryField(max_length=200)  # CountryField for better country handling
    phone = models.CharField(max_length=200)
    current_address = models.BooleanField(default=False)  # Indicates whether this is the current address

    def __str__(self):
        return f'{self.first_name} {self.last_name}, {self.street} {self.street_number}, {self.city}, {self.country} , {self.phone}'

    def get_absolute_url(self):
        return reverse('shipping-address-detail', kwargs={'pk': self.pk})


class ShippingAddressForm(forms.ModelForm):
    save_address = forms.BooleanField(required=False, label='Save the billing addres')

    class Meta:
        model = ShippingAddress
        fields = [
            'first_name',
            'last_name',
            'street',
            'street_number',
            'zip_code',
            'city',
            'country',
            'phone'
        ]

class Profile(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    shipping_address = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE, related_name="shipping_address", null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()
    
    def save(self, *args, **kwargs):
        # Check if the profile image is being updated and profile exists
        if self.pk:  # Only if profile exists
            try:
                old_profile = Profile.objects.get(pk=self.pk)
                if old_profile.profile_image and old_profile.profile_image != self.profile_image:
                    old_image_path = os.path.join(settings.MEDIA_ROOT, old_profile.profile_image.path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
            except Profile.DoesNotExist:
                # Profile does not exist, so nothing to do
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
    quantity = models.IntegerField(default=1)

    def get_product_price(self):
        return self.product.price * self.quantity if self.product else 0


class Order(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=100)
    shipping_address = models.TextField(blank=True, null=True)
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
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)

    def get_total_price(self):
        return self.product_price * self.quantity if self.product_price else 0
