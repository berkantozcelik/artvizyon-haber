from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Yorum

# --- 1. KAYIT FORMU (E-posta Zorunlu) ---
class KayitFormu(UserCreationForm):
    email = forms.EmailField(required=True, label="E-Posta Adresi")
    first_name = forms.CharField(required=True, label="Adınız")
    last_name = forms.CharField(required=True, label="Soyadınız")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

# --- 2. PROFİL DÜZENLEME FORMU (EKSİK OLAN BU OLABİLİR) ---
class ProfilGuncellemeFormu(forms.ModelForm):
    email = forms.EmailField(required=True, label="E-Posta Adresi")
    first_name = forms.CharField(required=True, label="Adınız")
    last_name = forms.CharField(required=True, label="Soyadınız")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

# --- 3. YORUM FORMU ---
class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ('govde',) # İsim ve E-posta otomatik alınıyor