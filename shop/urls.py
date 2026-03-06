from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Product and category URLs
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),

    # Cart and others URLs
    path('login/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
]


# media files setup for dynamic image urls
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)