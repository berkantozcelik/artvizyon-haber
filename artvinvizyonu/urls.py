from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from haberler import views # Senin uygulamanın adı 'haberler'
from django.views.generic import TemplateView

urlpatterns = [
    # --- GÜVENLİK: ÖZEL ADMİN YOLU ---
    path('artvizyon-sami/', admin.site.urls),
    
    # ==========================================
    # 👤 ÜYELİK VE HESAP İŞLEMLERİ (SADECE ALLAUTH VE PROFİL KALDI)
    # ==========================================
    
    # Tüm Giriş/Çıkış/Kayıt/Şifre Sıfırlama işleri artık Allauth'tan gelir.
    path('accounts/', include('allauth.urls')), 
    path('hesabim/', views.profil, name='profil'), 

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

    # Özel Gün Detay Sayfası
    path('ozel-gun/<slug:slug>/', views.ozel_gun_detay, name='ozel_gun_detay'),
        
    # Tarihi ve Turistik Yerler
    path('tarihi-yerler/', views.tarihi_yerler_listesi, name='tarihi_yerler_listesi'),
    path('tarihi-yerler/<slug:slug>/', views.tarihi_yer_detay, name='tarihi_yer_detay'),

    path('ckeditor/', include('ckeditor_uploader.urls')),
    
    # Haberler uygulaması için ek URL'ler
    path('', include('haberler.urls')),
    path('gizlilik-politikasi/', TemplateView.as_view(template_name='gizlilik.html'), name='gizlilik_politikasi'),
    path('hizmet-sartlari/', TemplateView.as_view(template_name='hizmet_sartlari.html'), name='hizmet_sartlari'),
]
    
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)