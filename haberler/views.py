from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from itertools import chain
from operator import attrgetter
import re

# Modeller ve Formlar
from .models import (
    Haber, Kategori, Galeri, HaftaninFotografi, 
    Ilce, EczaneLinki, KoseYazari, KoseYazisi, Destekci, Siir,
    OzelGun, TebrikMesaji 
)
from .forms import YorumForm, KayitFormu, ProfilGuncellemeFormu

# views.py dosyasındaki metin_ici_video_duzelt fonksiyonunu bununla değiştir:

def metin_ici_video_duzelt(icerik):
    """
    (video: ...) bloğu içindeki karmaşayı görmezden gelir.
    Sadece 11 haneli YouTube ID'sini (örn: dQw4w9WgXcQ) çekip alır.
    """
    if not icerik: return ""
    
    # 1. Adım: Önce (video: ... ) kutusunu bul
    block_pattern = re.compile(r'\(\s*video\s*:(.*?)\)', re.DOTALL | re.IGNORECASE)
    
    def replacement(match):
        content = match.group(1) # Parantez içindeki her şey (HTML kodları dahil)
        
        # 2. Adım: İçinden sadece 11 haneli ID'yi bul (En güvenli yöntem)
        # YouTube ID'leri harf, rakam, tire (-) ve alt çizgi (_) içerir.
        # Genelde 'v=' den sonra veya 'be/' den sonra gelir.
        
        id_pattern = re.compile(r'(?:v=|/|embed/|shorts/)([a-zA-Z0-9_-]{11})')
        found = id_pattern.search(content)
        
        if found:
            video_id = found.group(1)
            # Tertemiz bir player oluştur
            return f'''
            <div class="ratio ratio-16x9 my-4 shadow rounded border" style="width: 100%; display: block;">
                <iframe src="https://www.youtube.com/embed/{video_id}?rel=0" title="Video" allowfullscreen style="border:0;"></iframe>
            </div>
            '''
        return "" # ID bulamazsa boş döndür

    return block_pattern.sub(replacement, icerik)

# --- DİĞER FONKSİYONLAR AYNEN KALIYOR ---

def yorumlara_rozet_ekle(yorumlar):
    aktif_destekciler = Destekci.objects.filter(aktif_mi=True, bitis_tarihi__gte=timezone.now())
    destekci_dict = {d.email: d.paket for d in aktif_destekciler}
    for yorum in yorumlar:
        if yorum.email in destekci_dict:
            yorum.destekci_tipi = destekci_dict[yorum.email]
        else:
            yorum.destekci_tipi = None
    return yorumlar

# =========================================================
# 🏠 ANASAYFA
# =========================================================

def anasayfa(request):
    # 1. Haber Akışı (Aktif olanlar)
    haber_listesi = Haber.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')
    
    # Simetri bozulmasın diye 10'lu sayfalama yapıyoruz
    paginator = Paginator(haber_listesi, 10)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)

    # 2. Manşet Mantığı
    manset_haberler = Haber.objects.filter(aktif_mi=True, manset_mi=True)
    manset_yazilar = KoseYazisi.objects.filter(aktif_mi=True, manset_mi=True)
    
    mansetler = sorted(
        chain(manset_haberler, manset_yazilar),
        key=attrgetter('yayin_tarihi'),
        reverse=True
    )[:15]

    # 3. ÖZEL GÜN KARTI (Yılbaşı vb.)
    aktif_ozel_gun = OzelGun.objects.filter(aktif_mi=True, anasayfada_goster=True).first()

    # 4. DİĞER BİLEŞENLER
    haftanin_fotosu = HaftaninFotografi.objects.filter(aktif_mi=True).last()
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    yazarlar = KoseYazari.objects.filter(aktif_mi=True).order_by('-basyazar_mi', 'id')
    
    # --- GÜNÜN ŞİİRİ (YENİ MANTIK) ---
    # Önce senin "Günün Şiiri" olarak seçtiğin (tik attığın) şiiri arar
    gunun_siiri = Siir.objects.filter(aktif_mi=True, gunun_siiri_mi=True).first()
    
    # Eğer tikli şiir yoksa, en son eklenen şiiri getirir (Yedek Plan)
    if not gunun_siiri:
        gunun_siiri = Siir.objects.filter(aktif_mi=True).last()

    return render(request, 'anasayfa.html', {
        'haberler': haberler, 
        'mansetler': mansetler,
        'haftanin_fotosu': haftanin_fotosu,
        'eczaneler': eczaneler,
        'yazarlar': yazarlar,
        'gunun_siiri': gunun_siiri,     # <-- Artık seçtiğin şiir gelecek
        'aktif_ozel_gun': aktif_ozel_gun
    })

# --- KATEGORİ SAYFASI (YENİ ŞABLONU KULLANIR) ---
def kategori_haberleri(request, pk):
    secilen_kategori = get_object_or_404(Kategori, pk=pk)
    
    haber_listesi = Haber.objects.filter(kategori=secilen_kategori, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 12) 
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)

    # Yan Menü Verileri (Sadece Eczane ve Hava Durumu kaldı, Yazarlar Yok)
    eczaneler = EczaneLinki.objects.all().order_by('sira')

    # DİKKAT: Artık 'kategori.html' dosyasını çağırıyoruz!
    return render(request, 'kategori.html', {
        'haberler': haberler, 
        'secilen_kategori': secilen_kategori,
        'eczaneler': eczaneler,     
    })

# --- İLÇE SAYFASI (YENİ ŞABLONU KULLANIR) ---
def ilce_haberleri(request, pk):
    secilen_ilce = get_object_or_404(Ilce, pk=pk)
    
    haber_listesi = Haber.objects.filter(ilce=secilen_ilce, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 12)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)

    eczaneler = EczaneLinki.objects.all().order_by('sira')

    # DİKKAT: Artık 'kategori.html' dosyasını çağırıyoruz!
    return render(request, 'kategori.html', {
        'haberler': haberler, 
        'secilen_kategori': secilen_ilce, 
        'eczaneler': eczaneler,
    })

# =========================================================
# 📄 DETAY SAYFALARI
# =========================================================

def haber_detay(request, pk):
    haber = get_object_or_404(Haber, pk=pk)
    
    # --- YENİ DÖNÜŞTÜRÜCÜ BURADA ÇALIŞIYOR ---
    haber.icerik = metin_ici_video_duzelt(haber.icerik)
    
    # Yan Menü (Boş kalmasın diye fallback ekledik)
    benzer_haberler = Haber.objects.filter(kategori=haber.kategori, aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:5]
    if not benzer_haberler:
        benzer_haberler = Haber.objects.filter(aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:5]

    ham_yorumlar = haber.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        if not request.user.is_authenticated:
             return redirect('login')
        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.haber = haber
            yeni_yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yeni_yorum.email = request.user.email
            yeni_yorum.save()
            return redirect('haber_detay', pk=pk)
    else:
        yorum_form = YorumForm()

    return render(request, 'detay.html', {
        'haber': haber,
        'benzer_haberler': benzer_haberler,
        'yorumlar': onayli_yorumlar,
        'yorum_form': yorum_form,
    })

def yazi_detay(request, pk):
    yazi = get_object_or_404(KoseYazisi, pk=pk)
    
    # Köşe yazılarında da çalışsın
    yazi.icerik = metin_ici_video_duzelt(yazi.icerik)
    
    ham_yorumlar = yazi.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        if not request.user.is_authenticated:
             return redirect('login')
        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.kose_yazisi = yazi 
            yeni_yorum.isim = f"{request.user.first_name} {request.user.last_name}" or request.user.username
            yeni_yorum.email = request.user.email
            yeni_yorum.save()
            return redirect('yazi_detay', pk=pk)
    else:
        yorum_form = YorumForm()

    return render(request, 'yazi_detay.html', {'yazi': yazi, 'yorumlar': onayli_yorumlar, 'yorum_form': yorum_form})

def ozel_gun_detay(request, slug):
    ozel_gun = get_object_or_404(OzelGun, slug=slug, aktif_mi=True)
    mesajlar = ozel_gun.mesajlar.all().order_by('sira')
    return render(request, 'ozel_gun_detay.html', {'ozel_gun': ozel_gun, 'mesajlar': mesajlar})

# Diğer Fonksiyonlar
def siir_listesi(request):
    # 1. Vitrin Şiirini Bul (Tikli olan)
    gunun_siiri = Siir.objects.filter(aktif_mi=True, gunun_siiri_mi=True).first()
    
    # Eğer tikli yoksa en son eklenen vitrine çıkar
    if not gunun_siiri:
        gunun_siiri = Siir.objects.filter(aktif_mi=True).last()

    # 2. Listeyi Hazırla (Vitrindeki hariç diğerleri)
    if gunun_siiri:
        liste = Siir.objects.filter(aktif_mi=True).exclude(id=gunun_siiri.id).order_by('-yayin_tarihi')
    else:
        liste = Siir.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')

    # 3. Sayfalama (9 Şiir)
    paginator = Paginator(liste, 9) 
    sayfa_no = request.GET.get('page')
    siirler_sayfasi = paginator.get_page(sayfa_no)

    return render(request, 'siir_listesi.html', {
        'siirler': siirler_sayfasi,
        'gunun_siiri': gunun_siiri
    })

def siir_detay(request, pk):
    siir = get_object_or_404(Siir, pk=pk)
    ham_yorumlar = siir.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)
    return render(request, 'siir_detay.html', {'siir': siir, 'yorumlar': onayli_yorumlar, 'yorum_form': YorumForm()})

def galeri_listesi(request):
    galeriler = Galeri.objects.all().order_by('-yayin_tarihi')
    return render(request, 'galeri_listesi.html', {'galeriler': galeriler})

def galeri_detay(request, pk):
    galeri = get_object_or_404(Galeri, pk=pk)
    return render(request, 'galeri_detay.html', {'galeri': galeri})

def kayit_ol(request):
    if request.method == 'POST':
        form = KayitFormu(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('anasayfa')
    else: form = KayitFormu()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profil(request):
    if request.method == 'POST':
        form = ProfilGuncellemeFormu(request.POST, instance=request.user)
        if form.is_valid(): form.save(); return redirect('profil')
    else: form = ProfilGuncellemeFormu(instance=request.user)
    return render(request, 'registration/profil.html', {'form': form})

def destek(request): return render(request, 'destek.html')
def kimdir(request): return render(request, 'kimdir.html')
def iletisim(request): return render(request, 'iletisim.html')
def tesekkur(request): return render(request, 'tesekkur.html')

def arama(request):
    query = request.GET.get('q')
    sonuclar = Haber.objects.filter(Q(baslik__icontains=query)|Q(icerik__icontains=query), aktif_mi=True).order_by('-yayin_tarihi') if query else []
    return render(request, 'arama.html', {'sonuclar': sonuclar, 'query': query})

def global_context(request):
    return {
        'global_kategoriler': Kategori.objects.all(),
        'global_ilceler': Ilce.objects.all(),
        'son_dakika': Haber.objects.filter(aktif_mi=True, son_dakika=True, yayin_tarihi__gte=timezone.now()-timedelta(hours=24)).order_by('-yayin_tarihi')
    }