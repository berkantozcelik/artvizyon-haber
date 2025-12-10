from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Yorum, Profil  # <-- DİKKAT: Profil modelini buraya ekledik

# --- 1. KAYIT FORMU (Mevcut) ---
class KayitFormu(UserCreationForm):
    email = forms.EmailField(required=True, label="E-Posta Adresi")
    first_name = forms.CharField(required=True, label="Adınız")
    last_name = forms.CharField(required=True, label="Soyadınız")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

# --- 2. KULLANICI BİLGİLERİ GÜNCELLEME (Ad, Soyad, Email) ---
# Bunu views.py dosyasında 'KullaniciGuncellemeForm' adıyla çağırmıştık, o yüzden ismini düzelttim.
class KullaniciGuncellemeForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="E-Posta Adresi")
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

# --- 3. PROFİL RESMİ VE DETAYLARI (YENİ EKLEDİĞİMİZ KISIM) ---
# İşte resim yükleme kutusu burası!
class ProfilGuncellemeForm(forms.ModelForm):
    class Meta:
        model = Profil
        fields = ['resim', 'telefon', 'biyografi']

# --- 4. YORUM FORMU (Mevcut) ---
class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ('govde',)