from django.contrib import admin
from .models import *

# Register Category Model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_name', 'slug', 'category_image', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('category_name',)}

# Register ColorVariant Model
@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'price', 'created_at', 'updated_at']

# Register SizeVariant Model
@admin.register(SizeVariant)
class SizeVariantAdmin(admin.ModelAdmin):
    list_display = ['size_name', 'price', 'order', 'created_at', 'updated_at']

# Register Product Image Model (Inline for Product)
class ProductImageAdmin(admin.StackedInline):
    model = ProductImage
    fields = ['product', 'image', ]  # Include the image preview in the inline form

# Register Product Model
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'category', 'price', 'newest_product', 'get_rating', 'created_at', 'updated_at']
    inlines = [ProductImageAdmin]

# Register Product Image Model
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image', 'created_at', 'updated_at']  # Show image preview
    

# Register ProductReview Model
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'stars', 'content', 'date_added', 'like_count', 'dislike_count']
    list_filter = ['stars', 'date_added']

# Register Coupon Model
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['coupon_code', 'is_expired', 'discount_amount', 'minimum_amount', 'created_at', 'updated_at']

# Register Wishlist Model
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'added_on', 'created_at', 'updated_at']
    list_filter = ['added_on']
