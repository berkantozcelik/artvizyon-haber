from django.urls import path
from . import views

urlpatterns = [
    # Ana sayfaya girince views.py içindeki 'anasayfa' fonksiyonunu çalıştır
    path('', views.anasayfa, name='anasayfa'), 
]