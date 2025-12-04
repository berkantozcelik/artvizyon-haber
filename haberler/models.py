from django.db import models
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from PIL import Image  # Resim işleme kütüphanesi

# --- İLÇE ---
class Ilce(models.Model):
    isim = models.CharField(max_length=100, verbose_name="İlçe Adı")
    def __str__(self): return self.isim
    class Meta: verbose_name_plural = "İlçeler"

# --- KATEGORİ ---
class Kategori(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Kategori Adı")
    def __str__(self): return self.isim
    class Meta: verbose_name_plural = "Kategoriler"

# --- HABER (Sıkıştırma Eklendi) ---
class Haber(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Haber Başlığı")
    ozet = models.TextField(verbose_name="Kısa Özet", blank=True)
    
    # Resim yüklenebilir alan
    icerik = RichTextUploadingField(verbose_name="Haber İçeriği")
    
    resim = models.ImageField(upload_to='haber_resimleri/', verbose_name="Haber Resmi", blank=True)
    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, verbose_name="Kategori")
    ilce = models.ForeignKey(Ilce, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlçe (Varsa)")
    
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Yayınlanma Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")
    manset_mi = models.BooleanField(default=False, verbose_name="Manşette Göster")

    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Haberler"

    # --- SİHİRLİ SIKIŞTIRMA KODU BURADA ---
    def save(self, *args, **kwargs):
        # Önce normal kaydet ki dosya oluşsun
        super().save(*args, **kwargs)

        if self.resim:
            try:
                img = Image.open(self.resim.path)
                
                # Eğer resim çok büyükse (genişlik veya yükseklik 1000px üstü)
                if img.height > 1000 or img.width > 1000:
                    output_size = (1000, 1000)
                    img.thumbnail(output_size) # Orantılı küçült
                    # Optimize ederek aynı yere kaydet
                    img.save(self.resim.path, quality=60, optimize=True)
            except Exception as e:
                print(f"Resim sıkıştırma hatası: {e}")
                # Hata olsa bile akışı bozma, devam et

# --- FOTO GALERİ ---
class Galeri(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Galeri Başlığı")
    kapak_resmi = models.ImageField(upload_to='galeri_kapak/', verbose_name="Kapak Resmi")
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Yayın Tarihi")
    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Foto Galerileri"

class GaleriResim(models.Model):
    galeri = models.ForeignKey(Galeri, on_delete=models.CASCADE, related_name='resimler')
    resim = models.ImageField(upload_to='galeri_resimleri/')
    alt_yazi = models.CharField(max_length=200, blank=True, verbose_name="Alt Yazı (Opsiyonel)")

# --- HAFTANIN FOTOĞRAFI ---
class HaftaninFotografi(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Fotoğraf Adı")
    fotografci = models.CharField(max_length=100, verbose_name="Fotoğrafçı")
    resim = models.ImageField(upload_to='haftanin_fotografi/', verbose_name="Fotoğraf Dosyası")
    aktif_mi = models.BooleanField(default=True, verbose_name="Sitede Göster")
    class Meta: verbose_name_plural = "Haftanın Fotoğrafları"

# --- NÖBETÇİ ECZANE LİNKLERİ ---
class EczaneLinki(models.Model):
    ilce_adi = models.CharField(max_length=100, verbose_name="İlçe Adı (Örn: Hopa)")
    url = models.URLField(max_length=500, verbose_name="Eczane Listesi Linki")
    sira = models.IntegerField(default=0, verbose_name="Sıralama")
    def __str__(self): return self.ilce_adi
    class Meta: verbose_name_plural = "Nöbetçi Eczane Linkleri"; ordering = ['sira']

# --- KÖŞE YAZARLARI SİSTEMİ ---
class KoseYazari(models.Model):
    ad_soyad = models.CharField(max_length=100, verbose_name="Yazar Adı Soyadı")
    resim = models.ImageField(upload_to='yazar_resimleri/', verbose_name="Yazar Resmi (Kare)")
    aktif_mi = models.BooleanField(default=True, verbose_name="Sitede Göster")

    def __str__(self):
        return self.ad_soyad
    
    def son_yazisi(self):
        return self.yazilar.filter(aktif_mi=True).order_by('-yayin_tarihi').first()

    class Meta:
        verbose_name = "Köşe Yazarı"
        verbose_name_plural = "Köşe Yazarları"

class KoseYazisi(models.Model):
    yazar = models.ForeignKey(KoseYazari, on_delete=models.CASCADE, related_name='yazilar', verbose_name="Yazar")
    baslik = models.CharField(max_length=200, verbose_name="Yazı Başlığı")
    icerik = RichTextUploadingField(verbose_name="Yazı İçeriği")
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Yayın Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")

    def __str__(self):
        return f"{self.yazar.ad_soyad} - {self.baslik}"

    class Meta:
        verbose_name = "Köşe Yazısı"
        verbose_name_plural = "Köşe Yazıları"

# --- YORUM SİSTEMİ (GÜNCEL) ---
class Yorum(models.Model):
    haber = models.ForeignKey(Haber, on_delete=models.CASCADE, related_name='yorumlar', verbose_name="Haber", null=True, blank=True)
    kose_yazisi = models.ForeignKey(KoseYazisi, on_delete=models.CASCADE, related_name='yorumlar', verbose_name="Köşe Yazısı", null=True, blank=True)
    
    isim = models.CharField(max_length=80, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta", blank=True)
    govde = models.TextField(verbose_name="Yorumunuz")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Tarih")
    aktif = models.BooleanField(default=False, verbose_name="Yayınlansın mı?")

    class Meta:
        ordering = ['-olusturulma_tarihi']
        verbose_name = "Yorum"
        verbose_name_plural = "Yorumlar"

    def __str__(self):
        if self.haber:
            return f"Haber Yorumu: {self.isim} - {self.haber}"
        elif self.kose_yazisi:
            return f"Köşe Yazısı Yorumu: {self.isim} - {self.kose_yazisi}"
        return f"Yorum: {self.isim}"
    # models.py en altı

from datetime import timedelta

# --- ABONELİK SİSTEMİ ---
class Destekci(models.Model):
    PAKETLER = (
        ('okur', 'Okur Desteği (250 TL)'),
        ('gonul', 'Gönül Dostu (500 TL)'),
        ('sponsor', 'Sponsor (1.000 TL)'),
    )
    
    isim = models.CharField(max_length=100, verbose_name="Destekçi Adı")
    email = models.EmailField(verbose_name="E-Posta Adresi (Yorumlarla Eşleşmesi İçin)")
    paket = models.CharField(max_length=10, choices=PAKETLER, default='okur', verbose_name="Abonelik Paketi")
    
    baslangic_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Abonelik Başlangıcı")
    bitis_tarihi = models.DateTimeField(verbose_name="Abonelik Bitişi", blank=True, null=True)
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")

    def save(self, *args, **kwargs):
        # Eğer bitiş tarihi girilmediyse otomatik 30 gün ekle
        if not self.bitis_tarihi:
            self.bitis_tarihi = self.baslangic_tarihi + timedelta(days=30)
        super().save(*args, **kwargs)

    def sure_doldu_mu(self):
        # Bugünün tarihi bitiş tarihini geçtiyse False döner
        return timezone.now() <= self.bitis_tarihi

    def __str__(self):
        return f"{self.isim} - {self.get_paket_display()}"

    class Meta:
        verbose_name = "Abone"
        verbose_name_plural = "Aboneler"