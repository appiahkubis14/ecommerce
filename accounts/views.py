import os
import json
import uuid
from weasyprint import CSS, HTML
from products.models import *
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
# from home.models import ShippingAddress
from django.contrib.auth.models import User
from django.template.loader import get_template
from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from base.emails import send_account_activation_email
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect, render, get_object_or_404
from accounts.forms import UserUpdateForm, UserProfileForm, ShippingAddressForm, CustomPasswordChangeForm
from .utils import Paystack
import requests
from django.http import HttpResponseNotFound
from .models import ShippingAddress
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ShippingAddress
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View
# Create your views here.

def login_page(request):
    if request.method == "POST":
        # Get and strip the username and password values
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        
        # Check that both username and password are provided
        if not username or not password:
            error_message = "Please enter both username and password."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_message})
            return render(request, "accounts/login.html", {"error": error_message})
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Log the user in
            login(request, user)
            # Redirect to home page
            redirect_url = request.POST.get("next", "index") 
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": True, "redirect_url": redirect_url})
            return redirect('index')
        else:
            error_message = "Invalid username or password."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"success": False, "message": error_message})
            return render(request, "accounts/login.html", {"error": error_message})
        
        
    
    # Render the login page for GET requests
    return render(request, "accounts/login.html")

def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({"success": False, "message": "Username already taken."})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({"success": False, "message": "Email is already in use."})

        # Create and save the user
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )
        user.save()

        return JsonResponse({"success": True, "message": "Registration successful!"})

    return render(request, "accounts/register.html")


@login_required
def user_logout(request):
    logout(request)
    messages.warning(request, "Logged Out Successfully!")
    return redirect('index')


def activate_email_account(request, email_token):
    try:
        user = Profile.objects.get(email_token=email_token)
        user.is_email_verified = True
        user.save()
        messages.success(request, 'Account verification successful.')
        return redirect('login')
    except Exception as e:
        return HttpResponse('Invalid email token.')


@login_required
def add_to_cart(request, uid):
    try:
        # variant = request.GET.get('size')
        # if not variant:
        #     messages.warning(request, 'Please select a size variant!')
        #     return redirect(request.META.get('HTTP_REFERER'))

        product = get_object_or_404(Product, uid=uid)
        cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
        # size_variant = get_object_or_404(SizeVariant, size_name=variant)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product)
        if not created:
            cart_item.quantity += 1
            cart_item.save()

        messages.success(request, 'Item added to cart successfully.')

    except Exception as e:
        messages.error(request, 'Error adding item to cart.', str(e))

    return redirect(reverse('cart'))




login_required
def cart(request):
    user = request.user
    cart_obj = None

    try:
        cart_obj = Cart.objects.get(is_paid=False, user=user)
    except Cart.DoesNotExist:
        messages.warning(request, "Your cart is empty. Please add a product to cart.")
        return redirect(reverse('index'))

    cart_total_in_paise = cart_obj.get_cart_total()
    payment_reference = str(uuid.uuid4())  # Generate unique reference

    # Get or initialize shipping address
    try:
        shipping_address = ShippingAddress.objects.get(user=user)
        has_shipping_address = True
    except ShippingAddress.DoesNotExist:
        shipping_address = None
        has_shipping_address = False

    if request.method == "GET":
        # Handle AJAX request for shipping details
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            if shipping_address:
                return JsonResponse({
                    "has_shipping_address": True,
                    "first_name": shipping_address.first_name,
                    "last_name": shipping_address.last_name,
                    "street": shipping_address.street,
                    "street_number": shipping_address.street_number,
                    "city": shipping_address.city,
                    "zip_code": shipping_address.zip_code,
                    "country": shipping_address.country,
                    "phone": shipping_address.phone,
                    "current_address": shipping_address.current_address,
                })
            return JsonResponse({"has_shipping_address": False})

        # Render cart page with shipping details
        return render(request, "accounts/cart.html", {
            "cart": cart_obj,
            "quantity_range": range(1, 11),
            "payment_reference": payment_reference,
            "shipping_address": shipping_address,
        })
    elif request.method == "POST":
        # Handle shipping address update
        try:
            data = json.loads(request.body)
            if shipping_address:
                shipping_address.first_name = data.get("first_name", shipping_address.first_name)
                shipping_address.last_name = data.get("last_name", shipping_address.last_name)
                shipping_address.street = data.get("street", shipping_address.street)
                shipping_address.street_number = data.get("street_number", shipping_address.street_number)
                shipping_address.city = data.get("city", shipping_address.city)
                shipping_address.zip_code = data.get("zip_code", shipping_address.zip_code)
                shipping_address.country = data.get("country", shipping_address.country)
                shipping_address.phone = data.get("phone", shipping_address.phone)
                shipping_address.current_address = data.get("current_address", shipping_address.current_address)
            else:
                shipping_address = ShippingAddress.objects.create(
                    user=user,
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    street=data["street"],
                    street_number=data["street_number"],
                    city=data["city"],
                    zip_code=data["zip_code"],
                    country=data["country"],
                    phone=data["phone"],
                    current_address=data["current_address"],
                )

            shipping_address.save()
            return JsonResponse({"success": True, "message": "Shipping address updated successfully."})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Invalid JSON data"}, status=400)
        except KeyError as e:
            return JsonResponse({"success": False, "message": f"Missing field: {str(e)}"}, status=400)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=405)




def initiate_payment(request):
    cart = get_object_or_404(Cart, user=request.user, is_paid=False)
    payment_reference = str(uuid.uuid4())  # Generate a unique reference
    
    cart.paystack_reference = payment_reference  # Save it in the cart
    cart.save()

    return JsonResponse({"payment_reference": payment_reference})



def verify_paystack_payment(request):
    reference = request.GET.get("paystack_reference")
    if not reference:
        return JsonResponse({"error": "No reference provided"}, status=400)

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    response = requests.get(url, headers=headers)
    response_data = response.json()

    if response_data["status"] and response_data["data"]["status"] == "success":
        # Mark order as paid
        order = Order.objects.get(paystack_reference=reference)
        order.payment_status = "Paid"
        order.save()

        # Mark cart as paid
        cart = Cart.objects.get(user=order.user)
        cart.is_paid = True
        cart.paystack_reference = reference
        cart.paystack_status = "success"
        cart.save()

        return redirect("payment_success")
    else:
        return redirect("payment_failed")


@login_required
def process_payment(request):
    """
    Process payment and create order.
    Shipping cost is added to the cart total.
    """
    if request.method == "POST":
        user = request.user
        
        # Retrieve the cart. Ensure it's not paid yet.
        try:
            cart = Cart.objects.get(user=user, is_paid=False)
        except Cart.DoesNotExist:
            messages.error(request, "Your cart is empty.")
            return redirect("cart")
        
        # Ensure the cart has items
        if not cart.cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect("cart")

        # Generate a unique order ID
        order_id = str(uuid.uuid4())[:10]

        # Define shipping cost.
        # You can hard-code this value or pull it from settings (e.g., settings.SHIPPING_COST)
        shipping_cost = settings.SHIPPING_COST

        # Calculate the total cost including shipping.
        cart_total = cart.get_total_price()  # Assuming this method returns the cart's total price
        order_total = cart_total + shipping_cost

        # Create the Order. Make sure your Order model has fields for order_total_price and optionally shipping_cost.
        order = Order.objects.create(
            user=user,
            order_id=order_id,
            payment_status="Paid",  # Change this as per your payment flow
            shipping_address=user.profile.address,  # Ensure the user profile has an address
            payment_mode="Credit Card",  # Adjust based on actual payment mode
            order_total_price=order_total,
            grand_total=order_total,  # If applicable, adjust if there are taxes or discounts
            shipping_cost=shipping_cost  # Ensure your Order model has this field
        )

        # Transfer items from the cart to the order.
        for cart_item in cart.cart_items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                product_price=cart_item.get_product_price(),  # Ensure this returns the correct price
            )

        # Clear cart items after order creation
        cart.cart_items.all().delete()

        messages.success(request, "Your order has been placed successfully!")
        return redirect("order_history")  # Redirect to the order history page

    return redirect("cart")

@require_POST
@login_required
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        cart_item_id = data.get("cart_item_id")
        quantity = int(data.get("quantity"))

        cart_item = CartItem.objects.get(uid=cart_item_id, cart__user=request.user, cart__is_paid=False)
        cart_item.quantity = quantity
        cart_item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


def remove_cart(request, uid):
    try:
        cart_item = get_object_or_404(CartItem, uid=uid)
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')

    except Exception as e:
        print(e)
        messages.warning(request, 'Error removing item from cart.')

    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_coupon(request, cart_id):
    cart = Cart.objects.get(uid=cart_id)
    cart.coupon = None
    cart.save()

    messages.success(request, 'Coupon Removed.')
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Payment success view
def success(request):
    order_id = request.GET.get('order_id')

    if not order_id:
        return HttpResponseNotFound("Order ID is missing.")

    cart = get_object_or_404(Cart, paystack_reference=order_id)
    # Mark the cart as paid
    cart.is_paid = True
    cart.save()

    # Create the order after payment is confirmed
    order = create_order(cart)
    context = {'order_id': order_id, 'order': order}
    return render(request, 'payment_success/payment_success.html', context)


# HTML to PDF Conversion
def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)

    static_root = settings.STATIC_ROOT
    css_files = [
        os.path.join(static_root, 'css', 'bootstrap.css'),
        os.path.join(static_root, 'css', 'responsive.css'),
        os.path.join(static_root, 'css', 'ui.css'),
    ]
    css_objects = [CSS(filename=css_file) for css_file in css_files]
    pdf_file = HTML(string=html).write_pdf(stylesheets=css_objects)

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{context_dict["order"].order_id}.pdf"'
    return response


def download_invoice(request, order_id):
    order = Order.objects.filter(order_id=order_id).first()
    order_items = order.order_items.all()

    context = {
        'order': order,
        'order_items': order_items,
    }

    pdf = render_to_pdf('accounts/order_pdf_generate.html', context)
    if pdf:
        return pdf
    return HttpResponse("Error generating PDF", status=400)


@login_required
def profile_view(request, username):
    user_name = get_object_or_404(User, username=username)
    user = request.user
    profile = user.profile

    user_form = UserUpdateForm(instance=user)
    profile_form = UserProfileForm(instance=profile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    context = {
        'user_name': user_name,
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.warning(request, 'Please correct the error below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def update_shipping_address(request):
    shipping_address = ShippingAddress.objects.filter(
        user=request.user, current_address=True).first()

    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=shipping_address)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.current_address = True
            shipping_address.save()

            messages.success(request, "The Address Has Been Successfully Saved/Updated!")

            form = ShippingAddressForm()
        else:
            form = ShippingAddressForm(request.POST, instance=shipping_address)
    else:
        form = ShippingAddressForm(instance=shipping_address)

    return render(request, 'accounts/shipping_address_form.html', {'form': form})


# Order history view
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'accounts/order_history.html', {'orders': orders})


# Create an order view
def create_order(cart):
    """
    Creates an order from a cart after successful payment.
    """
    order_total = cart.get_cart_total()
    grand_total = order_total  # Modify if additional charges apply

    order = Order.objects.create(
        user=cart.user,
        order_id=cart.paystack_reference,  # Use Paystack reference for tracking
        payment_status="Paid",
        shipping_address=cart.user.profile.shipping_address if cart.user.profile else None,
        payment_mode="Paystack",
        order_total_price=order_total,
        grand_total=grand_total,
    )

    # Create OrderItem instances for each cart item
    cart_items = CartItem.objects.filter(cart=cart)
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            shipping_address=order.shipping_address,
            product=cart_item.product,
            quantity=cart_item.quantity,
            product_price=cart_item.get_product_price(),
        )

    return order


# Order Details view
@login_required
def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order,
        'order_items': order_items,
        'order_total_price': sum(item.get_total_price() for item in order_items),
        # 'coupon_discount': order.coupon.discount_amount if order.coupon else 0,
        'grand_total': order.get_order_total_price()
    }
    return render(request, 'accounts/order_details.html', context)


# Delete user account feature
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('index')




class ShippingAddressView(View):
    """Handles getting and updating a user's shipping address."""
    
    # Prevents redirect to login page; returns JSON instead
    login_url = None  # Prevents redirect to login page
    redirect_field_name = None  # Ensures no redirect

    def dispatch(self, request, *args, **kwargs):
        """Ensure JSON response for unauthenticated users instead of redirecting."""
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "User is not authenticated"}, status=401)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        """Handles retrieving the shipping address for an AJAX request."""
        
        # ✅ Ensure request is AJAX
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Invalid request. Expected AJAX."}, status=400)

        try:
            shipping_address = ShippingAddress.objects.get(user=request.user)
            return JsonResponse({
                "success": True,
                "has_shipping_address": True,
                "first_name": shipping_address.first_name,
                "last_name": shipping_address.last_name,
                "street": shipping_address.street,
                "street_number": shipping_address.street_number,
                "city": shipping_address.city,
                "zip_code": shipping_address.zip_code,
                "country": shipping_address.country,
                "phone": shipping_address.phone,
                "current_address": shipping_address.current_address,
            })

        except ShippingAddress.DoesNotExist:
            return JsonResponse({"success": True, "has_shipping_address": False})

        except Exception as e:
            return JsonResponse({"success": False, "error": f"Unexpected error: {str(e)}"}, status=500)

    def post(self, request):
        """Handles creating or updating the shipping address."""

        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Invalid request. Expected AJAX."}, status=400)

        try:
            data = json.loads(request.body)
            required_fields = [
                "first_name", "last_name", "street", "street_number",
                "city", "zip_code", "country", "phone", "current_address"
            ]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return JsonResponse({"success": False, "error": f"Missing fields: {', '.join(missing_fields)}"}, status=400)

            shipping_address, created = ShippingAddress.objects.update_or_create(
                user=request.user,
                defaults={field: data[field] for field in required_fields}
            )

            message = "Shipping address created successfully." if created else "Shipping address updated successfully."
            return JsonResponse({"success": True, "message": message})

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON data"}, status=400)
        
        except Exception as e:
            print(f"🔥 Unexpected error: {e}") 
            return JsonResponse({"success": False, "error": f"An error occurred: {str(e)}"}, status=500)
