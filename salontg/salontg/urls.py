"""
URL configuration for salontg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('/', admin.site.urls),
    path('', views.index_page, name='index'),
    path('services/', views.services_page, name='services'),
    path('masters/', views.masters_page, name='masters'),
    path('promotions/', views.promotions_page, name='promotions'),
    path('booking/', views.booking_page, name='booking'),
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('client/', views.profile_page, name='client'),
    path('profile/cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('master/dashboard/', views.master_dashboard, name='master_dashboard'),

    path('upload/', views.upload_photo, name='upload_photo'),
    path('photos/', views.photo_list, name='photo_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)