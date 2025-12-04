from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import (
    Haber, Kategori, Galeri, HaftaninFotografi, 
    Ilce, EczaneLinki, KoseYazari, KoseYazisi, Destekci
)
from .forms import YorumForm

# --- YARDIMCI FONKSİYON: ROZET SİSTEMİ ---
def yorumlara_rozet_ekle(yorumlar):
    """
    Bu fonksiyon yorumları tarar. Eğer yorumu yapan kişinin e-postası
    aktif bir destekçi ile eşleşiyorsa, yorum nesnesine 'destekci_tipi' bilgisini ekler.
    """
    # 1. Aktif ve süresi dolmamış destekçileri çek
    aktif_destekciler = Destekci.objects.filter(aktif_mi=True, bitis_tarihi__gte=timezone.now())
    
    # 2. Hızlı arama için sözlüğe çevir: {'ahmet@mail.com': 'gonul'}
    destekci_dict = {d.email: d.paket for d in aktif_destekciler}

    # 3. Yorumları tek tek kontrol et
    for yorum in yorumlar:
        if yorum.email in destekci_dict:
            # Eşleşme var! Rozet tipini (gonul, sponsor vs.) yoruma ekle
            yorum.destekci_tipi = destekci_dict[yorum.email]
        else:
            yorum.destekci_tipi = None
            
    return yorumlar

# --- ANASAYFA ---
def anasayfa(request):
    haber_listesi = Haber.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)

    mansetler = Haber.objects.filter(aktif_mi=True, manset_mi=True).order_by('-yayin_tarihi')[:10]
    haftanin_fotosu = HaftaninFotografi.objects.filter(aktif_mi=True).last()
    eczaneler = EczaneLinki.objects.all().order_by('sira')
    yazarlar = KoseYazari.objects.filter(aktif_mi=True)

    return render(request, 'anasayfa.html', {
        'haberler': haberler, 
        'mansetler': mansetler,
        'haftanin_fotosu': haftanin_fotosu,
        'eczaneler': eczaneler,
        'yazarlar': yazarlar
    })

# --- KATEGORİ SAYFASI ---
def kategori_haberleri(request, pk):
    secilen_kategori = get_object_or_404(Kategori, pk=pk)
    haber_listesi = Haber.objects.filter(kategori=secilen_kategori, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)
    return render(request, 'anasayfa.html', {'haberler': haberler, 'secilen_kategori': secilen_kategori})

# --- İLÇE SAYFASI ---
def ilce_haberleri(request, pk):
    secilen_ilce = get_object_or_404(Ilce, pk=pk)
    haber_listesi = Haber.objects.filter(ilce=secilen_ilce, aktif_mi=True).order_by('-yayin_tarihi')
    paginator = Paginator(haber_listesi, 9)
    sayfa_no = request.GET.get('page')
    haberler = paginator.get_page(sayfa_no)
    return render(request, 'anasayfa.html', {'haberler': haberler, 'secilen_kategori': secilen_ilce})

# --- HABER DETAY (DÜZELTİLDİ: TEKRARLAMA ENGELLENDİ) ---
def haber_detay(request, pk):
    haber = get_object_or_404(Haber, pk=pk)
    benzer_haberler = Haber.objects.filter(kategori=haber.kategori, aktif_mi=True).exclude(id=haber.id).order_by('-yayin_tarihi')[:3]

    # Yorumları getir ve ROZET KONTROLÜ yap
    ham_yorumlar = haber.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.haber = haber
            yeni_yorum.save()
            # KRİTİK EKLEME: Kayıt bitince sayfayı temizleyip yeniden yükle
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

# --- KÖŞE YAZISI DETAY (DÜZELTİLDİ: TEKRARLAMA ENGELLENDİ) ---
def yazi_detay(request, pk):
    yazi = get_object_or_404(KoseYazisi, pk=pk)
    
    # Yorumları getir ve ROZET KONTROLÜ yap
    ham_yorumlar = yazi.yorumlar.filter(aktif=True)
    onayli_yorumlar = yorumlara_rozet_ekle(ham_yorumlar)

    if request.method == 'POST':
        yorum_form = YorumForm(data=request.POST)
        if yorum_form.is_valid():
            yeni_yorum = yorum_form.save(commit=False)
            yeni_yorum.kose_yazisi = yazi 
            yeni_yorum.save()
            # KRİTİK EKLEME: Kayıt bitince sayfayı temizleyip yeniden yükle
            return redirect('yazi_detay', pk=pk)
    else:
        yorum_form = YorumForm()

    return render(request, 'yazi_detay.html', {
        'yazi': yazi,
        'yorumlar': onayli_yorumlar,
        'yorum_form': yorum_form
    })

# --- DESTEKÇİLER SAYFASI ---
def destek(request):
    # Sadece 'sponsor' paketini alan, aktif olan ve süresi dolmamış kişileri getir
    # En yeniden eskiye doğru sırala
    sponsorlar = Destekci.objects.filter(
        paket='sponsor', 
        aktif_mi=True, 
        bitis_tarihi__gte=timezone.now()
    ).order_by('-baslangic_tarihi')

    return render(request, 'destek.html', {'sponsorlar': sponsorlar})

# --- DİĞER SAYFALAR ---
def galeri_listesi(request):
    galeriler = Galeri.objects.all().order_by('-yayin_tarihi')
    return render(request, 'galeri_listesi.html', {'galeriler': galeriler})

def galeri_detay(request, pk):
    galeri = get_object_or_404(Galeri, pk=pk)
    return render(request, 'galeri_detay.html', {'galeri': galeri})

def kimdir(request): return render(request, 'kimdir.html')
def iletisim(request): return render(request, 'iletisim.html')
def destek(request): return render(request, 'destek.html')
def tesekkur(request): return render(request, 'tesekkur.html')

def arama(request):
    query = request.GET.get('q')
    sonuclar = []
    if query:
        sonuclar = Haber.objects.filter(Q(baslik__icontains=query) | Q(icerik__icontains=query), aktif_mi=True).order_by('-yayin_tarihi')
    return render(request, 'arama.html', {'sonuclar': sonuclar, 'query': query})