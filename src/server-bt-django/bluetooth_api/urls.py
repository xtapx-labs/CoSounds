"""
URL configuration for Bluetooth API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health, name='health'),
    path('register-device', views.register_device, name='register_device'),
    path('check-in', views.check_in, name='check_in'),
    path('scanner/device-detected', views.device_detected, name='device_detected'),
    path('my-status', views.my_status, name='my_status'),
]
