"""
URL configuration for Bluetooth Presence Detection backend.
"""

from django.urls import path, include

urlpatterns = [
    path('api/', include('bluetooth_api.urls')),
]
