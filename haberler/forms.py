# forms.py (Yoksa oluştur)

from django import forms
from .models import Yorum

class YorumForm(forms.ModelForm):
    class Meta:
        model = Yorum
        fields = ('isim', 'email', 'govde')
        widgets = {
            'isim': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Adınız Soyadınız',
                'style': 'background-color: #f8f9fa; border: 1px solid #ddd;'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control', 
                'placeholder': 'E-posta adresiniz (Yayınlanmaz)',
                'style': 'background-color: #f8f9fa; border: 1px solid #ddd;'
            }),
            'govde': forms.Textarea(attrs={
                'class': 'form-control', 
                'placeholder': 'Yorumunuzu buraya yazın...',
                'rows': 4,
                'style': 'background-color: #f8f9fa; border: 1px solid #ddd;'
            }),
        }