from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm, RatingForm, CheckoutForm
from . import models
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from django.db.models import Avg, Min, Max, Q
from . import sslcommerz



# Manual authentication without login with google

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('')  # Redirect to a success page.
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, '')


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST) #custom form for registration
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm() 
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return render(request, '')

def home_view(request):
    featured_products = Product.objects.filter(available=True).order_by('-created_at')[:8]
    categories = Category.objects.all()

    return render(request, 'home.html', {'featured_products': featured_products, 'categories': categories})


# Product page with filtering and search functionality
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    min_price = products.aggregate(Min('price'))['price__min']
    max_price = products.aggregate(Max('price'))['price__max']

    if request.GET.get('min_price'): # min_price and max_price are used for filtering products based on price range
        products = products.filter(price__gte=request.GET['min_price'])
    
    if request.GET.get('max_price'):
        products = products.filter(price__lte=request.GET['max_price'])

    if request.GET.get('rating'):
        products = products.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=request.GET['rating'])

    if request.GET.get('search'):
        query = request.GET.get('search')
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    return render(request, 'product_list.html', {
        'category': category, 
        'categories': categories, 
        'products': products, 
        'min_price': min_price, 
        'max_price': max_price
        })

# Product detail page
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product, user=request.user)
        except Rating.DoesNotExist:
            pass
        rating_form = RatingForm(instance=user_rating)
    
    return render(request, '', {
        'product': product, 
        'related_products': related_products,
        'user_rating': user_rating,
        'rating_form': 'rating_form'
        })

def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('cart_detail')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart_detail')

    if request.method == 'POST':
        form = CheckoutForm(request.POST) # Corrected POSR to POST
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user # Corrected request.user_rating to request.user
            order.save()
            
            # Create OrderItem records from Cart items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            # Clear the cart after successful order creation
            cart.items.all().delete()
            request.session['order_id'] = order.id
            return redirect('payment_success')
    else:
        form = CheckoutForm()
    return render(request, 'checkout.html', {'form': form, 'cart': cart})

def cart_add(request, product_id):
    product = get_object_or_404(Product, id = product_id)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product, quantity=1)
    messages.success(request, f'Added {product.name} to cart.')
    return redirect('')

def cart_update(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    quantity = int(request.POST.get('quantity', 1))
    if quantity <= 0:
        cart_item.delete()
        messages.info(request, f'Removed {product.name} from cart.')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f'Updated {product.name} quantity to {quantity}.')
    return redirect('')

def cart_remove(request, product_id):
    cart = get_object_or_404(Cart, user=request.user)
    product = get_object_or_404(Product, id=product_id)
    cart_item = get_object_or_404(CartItem, cart=cart, product=product)

    cart_item.delete()
    messages.info(request, f'Removed {product.name} from cart.')
    return redirect('')

def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)
    return render(request, 'cart_detail.html', {'cart': cart})

def checkout(request):
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty.')
            return redirect('')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty.')
        return redirect('')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user_rating
            order.save()
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price =item.product.price,
                    quantity=item.quantity
                )
            cart.items.all().delete()
            request.session['order_id'] = order.id
            return redirect('')
    else:
        form = CheckoutForm()
    return render(request, '', {'form': form, 'cart': cart})

def payment_process()
    order_id = request.session.get('order_id')
    if not order_id:
        messages.error(request, 'No order found for payment.')
        return redirect('')
    order = get_object_or_404(Order, id=order_id)
    payment_data = sslcommerz.generate_ssl_commerz_payment(request, order)
    if payment_data.get('status') == 'SUCCESS':
        return redirect()
    else:
        messages.error(request, 'Failed to initiate payment. Please try again.')
        return redirect('')

def payment_success(request):
    order = get_object_or_404(Order, id=request.session.get('order_id'))
    order.paid = True
    status = 'processing'
    order.transaction_id = f'TXN{order.id}{order.created_at.strftime("%Y%m%d%H%M%S")}'
    order.save()
    order_items = order.order_items.all()
    for item in order_items:
        item.product.stock -= item.quantity
        
        if item.product.stock < 0:
            item.product.stock = 0
        item.product.save()
    messages.success(request, 'Your payment was successful! Your order is being processed.')
    return render(request, 'payment_success.html', {'order': order})

def payment_fail(request):
    order = get_object_or_404(Order, id=request.session.get('order_id'))
    status = 'canceled'
    order.save()
    return redirect('')

def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    status = 'canceled'
    order.save()
    messages.info(request, 'Your order has been canceled.')
    return redirect('')
