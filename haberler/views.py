from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from itertools import chain
from operator import attrgetter
import re

# Modeller
from .models import (
    Haber, Kategori, Galeri, HaftaninFotografi, 
    Ilce, EczaneLinki, KoseYazari, KoseYazisi, Destekci, Siir,
    OzelGun, TebrikMesaji, TarihiYer, Profil, get_youtube_embed
)

# Formlar
from .forms import KayitFormu, YorumForm, KullaniciGuncellemeForm, ProfilGuncellemeForm

# --- YARDIMCI FONKSİYONLAR ---

def metin_ici_video_duzelt(icerik):
    """(video: ...) bloğu içindeki 11 haneli YouTube ID'sini çeker."""
    if not icerik: return ""
    block_pattern = re.compile(r'\(\s*video\s*:(.*?)\)', re.DOTALL | re.IGNORECASE)
    
    def replacement(match):
        embed_url = get_youtube_embed(match.group(1))
        if not embed_url:
            return ""
        return f'''
        <div class="ratio ratio-16x9 my-4 shadow rounded border" style="width: 100%; display: block;">
            <iframe src="{embed_url}" title="Video" loading="lazy"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="border:0;"></iframe>
        </div>
        '''
    return block_pattern.sub(replacement, icerik)

def yorumlara_rozet_ekle(yorumlar):
    aktif_destekciler = Destekci.objects.filter(aktif_mi=True, bitis_tarihi__gte=timezone.now())
    destekci_dict = {d.email: d.paket for d in aktif_destekciler}
    for yorum in yorumlar:
        if yorum.email in destekci_dict:
            yorum.destekci_tipi = destekci_dict[yorum.email]
        else:
            yorum.destekci_tipi = None
    return yorumlar

# --- CONTEXT PROCESSOR (HATAYI ÇÖZEN KISIM) ---
# Bu fonksiyon sitenin her yerinde kategori ve ilçe verilerinin görünmesini sağlar.
def global_context(request):
    return {
        'global_kategoriler': Kategori.objects.all(),
        'global_ilceler': Ilce.objects.all(),
        'son_dakika': Haber.objects.filter(aktif_mi=True, son_dakika=True, yayin_tarihi__gte=timezone.now()-timedelta(hours=24)).order_by('-yayin_tarihi')
    }

# =========================================================
# 🏠 ANASAYFA
# =========================================================
def anasayfa(request):
    haber_listesi = Haber.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 10)
    haberler = paginator.get_page(request.GET.get('page'))

    manset_haberler = Haber.objects.filter(aktif_mi=True, manset_mi=True)
    manset_yazilar = KoseYazisi.objects.filter(aktif_mi=True, manset_mi=True)
    mansetler = sorted(chain(manset_haberler, manset_yazilar), key=attrgetter('yayin_tarihi'), reverse=True)[:15]

    aktif_ozel_gun = OzelGun.objects.filter(aktif_mi=True, anasayfada_goster=True).first()
    haftanin_fotosu = HaftaninFotografi.objects.filter(aktif_mi=True).last()
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    yazarlar = KoseYazari.objects.filter(aktif_mi=True).order_by('-basyazar_mi', 'id')
    
    gunun_siiri = Siir.objects.filter(aktif_mi=True, gunun_siiri_mi=True).first() or Siir.objects.filter(aktif_mi=True).last()

    return render(request, 'anasayfa.html', {
        'haberler': haberler, 'mansetler': mansetler, 'haftanin_fotosu': haftanin_fotosu,
        'eczaneler': eczaneler, 'yazarlar': yazarlar, 'gunun_siiri': gunun_siiri,
        'aktif_ozel_gun': aktif_ozel_gun
    })

# --- KATEGORİ VE İLÇE ---
def kategori_haberleri(request, pk):
    secilen_kategori = get_object_or_404(Kategori, pk=pk)
    haber_listesi = Haber.objects.filter(kategori=secilen_kategori, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 12)
    haberler = paginator.get_page(request.GET.get('page'))
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    return render(request, 'kategori.html', {'haberler': haberler, 'secilen_kategori': secilen_kategori, 'eczaneler': eczaneler})

def ilce_haberleri(request, pk):
    secilen_ilce = get_object_or_404(Ilce, pk=pk)
    haber_listesi = Haber.objects.filter(ilce=secilen_ilce, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 12)
    haberler = paginator.get_page(request.GET.get('page'))
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    return render(request, 'kategori.html', {'haberler': haberler, 'secilen_kategori': secilen_ilce, 'eczaneler': eczaneler})

# =========================================================
# 📄 DETAY SAYFALARI
# =========================================================
def haber_detay(request, pk):
    haber = get_object_or_404(Haber, pk=pk)
    haber.icerik = metin_ici_video_duzelt(haber.icerik)
    
    benzer_haberler = Haber.objects.filter(kategori=haber.kategori, aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:5]
    if not benzer_haberler:
        benzer_haberler = Haber.objects.filter(aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:5]

    onayli_yorumlar = yorumlara_rozet_ekle(haber.yorumlar.filter(aktif=True))

    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        form = YorumForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.haber = haber
            yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yorum.email = request.user.email
            yorum.save()
            messages.success(request, "Yorumunuz gönderildi.")
            return redirect('haber_detay', pk=pk)
    else: form = YorumForm()

    return render(request, 'detay.html', {'haber': haber, 'benzer_haberler': benzer_haberler, 'yorumlar': onayli_yorumlar, 'yorum_form': form})

def yazi_detay(request, pk):
    yazi = get_object_or_404(KoseYazisi, pk=pk)
    yazi.icerik = metin_ici_video_duzelt(yazi.icerik)
    onayli_yorumlar = yorumlara_rozet_ekle(yazi.yorumlar.filter(aktif=True))

    if request.method == 'POST':
        if not request.user.is_authenticated: return redirect('login')
        form = YorumForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.kose_yazisi = yazi
            yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yorum.email = request.user.email
            yorum.save()
            return redirect('yazi_detay', pk=pk)
    else: form = YorumForm()

    return render(request, 'yazi_detay.html', {'yazi': yazi, 'yorumlar': onayli_yorumlar, 'yorum_form': form})

# --- DİĞER SAYFALAR ---
def ozel_gun_detay(request, slug):
    ozel_gun = get_object_or_404(OzelGun, slug=slug, aktif_mi=True)
    mesajlar = ozel_gun.mesajlar.all().order_by('sira')
    return render(request, 'ozel_gun_detay.html', {'ozel_gun': ozel_gun, 'mesajlar': mesajlar})

def siir_listesi(request):
    gunun_siiri = Siir.objects.filter(aktif_mi=True, gunun_siiri_mi=True).first() or Siir.objects.filter(aktif_mi=True).last()
    liste = Siir.objects.filter(aktif_mi=True).exclude(id=gunun_siiri.id).order_by('-yayin_tarihi') if gunun_siiri else Siir.objects.filter(aktif_mi=True)
    paginator = Paginator(liste, 9)
    siirler = paginator.get_page(request.GET.get('page'))
    return render(request, 'siir_listesi.html', {'siirler': siirler, 'gunun_siiri': gunun_siiri})

def siir_detay(request, pk):
    siir = get_object_or_404(Siir, pk=pk)
    onayli_yorumlar = yorumlara_rozet_ekle(siir.yorumlar.filter(aktif=True))
    return render(request, 'siir_detay.html', {'siir': siir, 'yorumlar': onayli_yorumlar, 'yorum_form': YorumForm()})

def galeri_listesi(request):
    galeriler = Galeri.objects.all().order_by('-yayin_tarihi')
    return render(request, 'galeri_listesi.html', {'galeriler': galeriler})

def galeri_detay(request, pk):
    galeri = get_object_or_404(Galeri, pk=pk)
    return render(request, 'galeri_detay.html', {'galeri': galeri})


# --- PROFİL YÖNETİMİ (TEK VE DOĞRU OLAN) ---
@login_required
def profil(request):
    if not hasattr(request.user, 'profil'):
        Profil.objects.create(user=request.user)

    if request.method == 'POST':
        u_form = KullaniciGuncellemeForm(request.POST, instance=request.user)
        p_form = ProfilGuncellemeForm(request.POST, request.FILES, instance=request.user.profil)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profiliniz güncellendi!')
            return redirect('profil')
    else:
        u_form = KullaniciGuncellemeForm(instance=request.user)
        p_form = ProfilGuncellemeForm(instance=request.user.profil)

    return render(request, 'profil.html', {'u_form': u_form, 'p_form': p_form})

# --- TARİHİ VE TURİSTİK YERLER ---
def tarihi_yerler_listesi(request):
    yerler = TarihiYer.objects.filter(aktif_mi=True).order_by('sira')
    return render(request, 'tarihi_yerler_listesi.html', {'yerler': yerler})

def tarihi_yer_detay(request, slug):
    yer = get_object_or_404(TarihiYer, slug=slug)
    return render(request, 'tarihi_yer_detay.html', {'yer': yer})

# --- DİĞER ---
def destek(request): return render(request, 'destek.html')
def kimdir(request): return render(request, 'kimdir.html')
def iletisim(request): return render(request, 'iletisim.html')
def tesekkur(request): return render(request, 'tesekkur.html')

def arama(request):
    query = request.GET.get('q')
    sonuclar = Haber.objects.filter(Q(baslik__icontains=query)|Q(icerik__icontains=query), aktif_mi=True).order_by('-yayin_tarihi') if query else []
    return render(request, 'arama.html', {'sonuclar': sonuclar, 'query': query})
