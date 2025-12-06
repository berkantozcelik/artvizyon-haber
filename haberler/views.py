from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

# Modeller ve Formlar
from .models import (
    Haber, Kategori, Galeri, HaftaninFotografi, 
    Ilce, EczaneLinki, KoseYazari, KoseYazisi, Destekci, Siir
)
from .forms import YorumForm, KayitFormu, ProfilGuncellemeFormu

# --- YARDIMCI FONKSİYON: YORUMLARA ROZET EKLEME ---
def yorumlara_rozet_ekle(yorumlar):
    """
    Yorum yapan kişinin e-postası Destekçi tablosunda varsa,
    yorum nesnesine geçici olarak 'destekci_tipi' alanı ekler.
    """
    aktif_destekciler = Destekci.objects.filter(aktif_mi=True, bitis_tarihi__gte=timezone.now())
    destekci_dict = {d.email: d.paket for d in aktif_destekciler}
    for yorum in yorumlar:
        if yorum.email in destekci_dict:
            yorum.destekci_tipi = destekci_dict[yorum.email]
        else:
            yorum.destekci_tipi = None
    return yorumlar

# =========================================================
# 👤 KULLANICI İŞLEMLERİ (KAYIT & PROFİL)
# =========================================================

def kayit_ol(request):
    if request.method == 'POST':
        form = KayitFormu(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Kayıt olunca otomatik giriş yap
            return redirect('anasayfa')
    else:
        form = KayitFormu()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profil(request):
    if request.method == 'POST':
        form = ProfilGuncellemeFormu(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profil') # Sayfayı yenile
    else:
        form = ProfilGuncellemeFormu(instance=request.user)
    return render(request, 'registration/profil.html', {'form': form})

# =========================================================
# 🏠 ANASAYFA VE LİSTELEMELER
# =========================================================

def anasayfa(request):
    # Haberler
    haber_listesi = Haber.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)

    # Manşetler (Sadece manset_mi=True olanlar)
    mansetler = Haber.objects.filter(aktif_mi=True, manset_mi=True).order_by('-yayin_tarihi')[:10]
    
    # Diğer Bileşenler
    haftanin_fotosu = HaftaninFotografi.objects.filter(aktif_mi=True).last()
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    
    # Yazarlar (Başyazar en üstte olacak şekilde)
    yazarlar = KoseYazari.objects.filter(aktif_mi=True).order_by('-basyazar_mi', 'id')

    # Günün Şiiri (Rastgele)
    gunun_siiri = Siir.objects.filter(aktif_mi=True).order_by('?').first()

    return render(request, 'anasayfa.html', {
        'haberler': haberler, 
        'mansetler': mansetler,
        'haftanin_fotosu': haftanin_fotosu,
        'eczaneler': eczaneler,
        'yazarlar': yazarlar,
        'gunun_siiri': gunun_siiri
    })

def kategori_haberleri(request, pk):
    secilen_kategori = get_object_or_404(Kategori, pk=pk)
    haber_listesi = Haber.objects.filter(kategori=secilen_kategori, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)
    return render(request, 'anasayfa.html', {'haberler': haberler, 'secilen_kategori': secilen_kategori})

def ilce_haberleri(request, pk):
    secilen_ilce = get_object_or_404(Ilce, pk=pk)
    haber_listesi = Haber.objects.filter(ilce=secilen_ilce, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)
    return render(request, 'anasayfa.html', {'haberler': haberler, 'secilen_kategori': secilen_ilce})

# =========================================================
# 📄 DETAY SAYFALARI (HABER & KÖŞE YAZISI)
# =========================================================

def haber_detay(request, pk):
    haber = get_object_or_404(Haber, pk=pk)
    benzer_haberler = Haber.objects.filter(kategori=haber.kategori, aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:3]
    
    # Yorumları Getir
    ham_yorumlar = haber.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        # Güvenlik: Sadece giriş yapanlar yorum atabilir
        if not request.user.is_authenticated:
             return redirect('login')

        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.haber = haber
            # Kullanıcı bilgilerini otomatik doldur
            yeni_yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yeni_yorum.email = request.user.email
            yeni_yorum.save()
            return redirect('haber_detay', pk=pk)
    else:
        yorum_form = YorumForm()

    context = {
        'haber': haber,
        'benzer_haberler': benzer_haberler,
        'yorumlar': onayli_yorumlar,
        'yorum_form': yorum_form,
    }
    return render(request, 'detay.html', context)

def yazi_detay(request, pk):
    yazi = get_object_or_404(KoseYazisi, pk=pk)
    ham_yorumlar = yazi.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        if not request.user.is_authenticated:
             return redirect('login')

        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.kose_yazisi = yazi 
            # Kullanıcı bilgilerini otomatik doldur
            yeni_yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yeni_yorum.email = request.user.email
            yeni_yorum.save()
            return redirect('yazi_detay', pk=pk)
    else:
        yorum_form = YorumForm()

    return render(request, 'yazi_detay.html', {'yazi': yazi, 'yorumlar': onayli_yorumlar, 'yorum_form': yorum_form})

# =========================================================
# 🎭 KÜLTÜR & SANAT (ŞİİR & GALERİ)
# =========================================================

def siir_listesi(request):
    siirler = Siir.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(siirler, 9)
    sayfa_no = request.GET.get('page')
    siirler_sayfasi = paginator.get_page(sayfa_no)
    return render(request, 'siir_listesi.html', {'siirler': siirler_sayfasi})

def siir_detay(request, pk):
    siir = get_object_or_404(Siir, pk=pk)
    return render(request, 'siir_detay.html', {'siir': siir})

def galeri_listesi(request):
    galeriler = Galeri.objects.all().order_by('-yayin_tarihi')
    return render(request, 'galeri_listesi.html', {'galeriler': galeriler})

def galeri_detay(request, pk):
    galeri = get_object_or_404(Galeri, pk=pk)
    return render(request, 'galeri_detay.html', {'galeri': galeri})

# =========================================================
# 📌 SABİT SAYFALAR & İŞLEVLER
# =========================================================

def destek(request):
    if request.method == 'POST':
        isim = request.POST.get('isim')
        email = request.POST.get('email')
        paket = request.POST.get('paket')
        # Destekçi kaydı oluştur (Varsayılan pasif, ödeme onayıyla aktif olur)
        Destekci.objects.create(isim=isim, email=email, paket=paket, aktif_mi=False)
        return redirect('tesekkur')

    sponsorlar = Destekci.objects.filter(paket='sponsor', aktif_mi=True, bitis_tarihi__gte=timezone.now()).order_by('-baslangic_tarihi')
    return render(request, 'destek.html', {'sponsorlar': sponsorlar})

def kimdir(request): return render(request, 'kimdir.html')
def iletisim(request): return render(request, 'iletisim.html')
def tesekkur(request): return render(request, 'tesekkur.html')

def arama(request):
    query = request.GET.get('q')
    sonuclar = []
    if query:
        # Hem başlıkta hem içerikte ara
        sonuclar = Haber.objects.filter(Q(baslik__icontains=query) | Q(icerik__icontains=query), aktif_mi=True).order_by('-yayin_tarihi')
    return render(request, 'arama.html', {'sonuclar': sonuclar, 'query': query})

# =========================================================
# 🌍 GLOBAL CONTEXT PROCESSOR (HER SAYFADA ÇALIŞIR)
# =========================================================
def global_context(request):
    # Menüler için Kategoriler ve İlçeler
    kategoriler = Kategori.objects.all()
    ilceler = Ilce.objects.all()
    
    # SON DAKİKA MANTIĞI:
    # 1. 'son_dakika' kutusu işaretli olmalı.
    # 2. Yayınlanma tarihi üzerinden 24 saat geçmemiş olmalı.
    zaman_siniri = timezone.now() - timedelta(hours=24)
    
    son_dakika_haberleri = Haber.objects.filter(
        aktif_mi=True,
        son_dakika=True,
        yayin_tarihi__gte=zaman_siniri
    ).order_by('-yayin_tarihi')

    return {
        'global_kategoriler': kategoriler,
        'global_ilceler': ilceler,
        'son_dakika': son_dakika_haberleri,
    }