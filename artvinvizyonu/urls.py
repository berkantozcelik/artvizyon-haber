from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views # Giriş/Çıkış sistemi
from haberler import views # Senin uygulamanın adı 'haberler'

urlpatterns = [
    # --- GÜVENLİK: ÖZEL ADMİN YOLU ---
    path('artvizyon-sami/', admin.site.urls),
    
    # ==========================================
    # 👤 ÜYELİK VE HESAP İŞLEMLERİ
    # ==========================================
    path('giris-yap/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('cikis-yap/', auth_views.LogoutView.as_view(next_page='anasayfa'), name='logout'),
    path('kayit-ol/', views.kayit_ol, name='register'),
    path('hesabim/', views.profil, name='profil'), # <-- YENİ EKLENEN PROFİL SAYFASI

    # ==========================================
    # 🏠 SİTE İÇERİK SAYFALARI
    # ==========================================
    path('', views.anasayfa, name='anasayfa'),
    
    # Haberler
    path('haber/<int:pk>/', views.haber_detay, name='haber_detay'),
    path('kategori/<int:pk>/', views.kategori_haberleri, name='kategori_haberleri'),
    path('ilce/<int:pk>/', views.ilce_haberleri, name='ilce_haberleri'),
    
    # Kültür & Sanat
    path('galeri/', views.galeri_listesi, name='galeri_listesi'),
    path('galeri/<int:pk>/', views.galeri_detay, name='galeri_detay'),
    path('siir-kosesi/', views.siir_listesi, name='siir_listesi'),
    path('siir/<int:pk>/', views.siir_detay, name='siir_detay'),

    # Köşe Yazıları
    path('yazi/<int:pk>/', views.yazi_detay, name='yazi_detay'),

    # Sabit Sayfalar
    path('kimdir/', views.kimdir, name='kimdir'),
    path('iletisim/', views.iletisim, name='iletisim'),
    path('arama/', views.arama, name='arama'),
    
    # Abonelik / Destek
    path('destek-ol/', views.destek, name='destek'),
    path('tesekkur/', views.tesekkur, name='tesekkur'),

    # Editör Resim Yükleme (CKEditor)
    path('ckeditor/', include('ckeditor_uploader.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)