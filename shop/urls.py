from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.home, name='home'),
]


# media files setup for dynamic image urls
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)