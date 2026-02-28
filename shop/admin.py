from django.contrib import admin

from .models import Cart, CartItem, Category, Order, OrderItem, Product, Rating

# Register your models here.
admin.site.register([Category, Product, Rating, Cart, CartItem, Order, OrderItem])