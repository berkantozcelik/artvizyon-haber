from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Tüm sayfaları (fonksiyonları) çağırıyoruz
# Buraya yeni eklediğimiz siir_listesi ve siir_detay fonksiyonlarını da dahil ettim
from haberler.views import (
    anasayfa, 
    haber_detay, 
    kimdir, 
    kategori_haberleri, 
    ilce_haberleri,
    arama, 
    iletisim, 
    destek, 
    tesekkur, 
    galeri_listesi, 
    galeri_detay,
    yazi_detay,
    siir_listesi,  # <-- Yeni
    siir_detay     # <-- Yeni
)

urlpatterns = [
    # GÜVENLİK ÖNLEMİ: Admin paneli giriş adresi
    path('artvizyon-sami/', admin.site.urls),
    
    # Anasayfa
    path('', anasayfa, name='anasayfa'),
    
    # Haberler, Kategoriler ve İlçeler
    path('haber/<int:pk>/', haber_detay, name='haber_detay'),
    path('kategori/<int:pk>/', kategori_haberleri, name='kategori_haberleri'),
    path('ilce/<int:pk>/', ilce_haberleri, name='ilce_haberleri'),
    
    # Foto Galeri
    path('galeri/', galeri_listesi, name='galeri_listesi'),
    path('galeri/<int:pk>/', galeri_detay, name='galeri_detay'),

    # Köşe Yazısı
    path('yazi/<int:pk>/', yazi_detay, name='yazi_detay'),

    # --- YENİ: ŞİİR KÖŞESİ ---
    path('siir-kosesi/', siir_listesi, name='siir_listesi'),
    path('siir/<int:pk>/', siir_detay, name='siir_detay'),

    # Sabit Sayfalar
    path('kimdir/', kimdir, name='kimdir'),
    path('iletisim/', iletisim, name='iletisim'),
    path('arama/', arama, name='arama'),
    path('destek-ol/', destek, name='destek'),
    path('tesekkur/', tesekkur, name='tesekkur'),

    # Editör Resim Yükleme Yolu (CKEditor)
    path('ckeditor/', include('ckeditor_uploader.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)