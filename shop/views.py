from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm, RatingForm, CheckoutForm
from . import models
from .models import Category, Product, Rating, Cart, CartItem, Order, OrderItem
from django.db.models import Avg, Min, Max, Q



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
        }

def rate_product(request, product_id): # If purchased then only user can rate the product
    product =  get_object_or_404(Product, id=product_id)

    ordered_items = OrderItem.objects.filter(
        order_user = request.user,
        product = product,
        order__paid = True
    )
    if not ordered_items.exists():
        messages.error(request, 'You can only rate products when you have purchased.')
        return redirect('')

    try:
        rating = Rating.objects.get(product=product, user = request.user)
    except Rating.DoesNotExist:
        rating = None
    
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            new_rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user
            new_rating.save()
            messages.success(request, 'Your rating has been submitted.')
            return redirect('')
    else:
        form = RatingForm(instance=rating)
        return render(request, '', {'form': form, 'product': product})