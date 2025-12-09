from django.db import models
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from django.core.files.base import ContentFile
from django.utils.text import slugify 
import textwrap
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
import re  # <-- YENİ EKLENDİ

# --- DÜZELTME: Doğru Kütüphane Eklendi ---
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFit

# --- YARDIMCI FONKSİYON: YOUTUBE EMBED ÇEVİRİCİ ---
# --- GÜNCELLENMİŞ YARDIMCI FONKSİYON ---
def get_youtube_embed(url):
    """
    Normal videoları ve SHORTS videolarını embed koduna çevirir.
    """
    if not url: return None
    
    # 1. Eğer zaten embed linki ise dokunma
    if "embed" in url: return url

    # 2. Eğer SHORTS videosu ise (YENİ EKLENEN KISIM)
    if "shorts/" in url:
        try:
            # youtube.com/shorts/VIDEO_ID?feature=share gibi gelebilir
            video_id = url.split("shorts/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except:
            return url

    # 3. Eğer kısaltılmış link ise (youtu.be)
    if "youtu.be" in url:
        try:
            video_id = url.split("/")[-1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except: return url
        
    # 4. Eğer normal link ise (watch?v=)
    if "watch?v=" in url:
        try:
            video_id = url.split("watch?v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"
        except: return url
        
    return url

# ==========================================
# 📌 TEMEL KATEGORİ VE İLÇE MODELLERİ
# ==========================================

class Kategori(models.Model):
    isim = models.CharField(max_length=100, verbose_name="Kategori Adı")
    slug = models.SlugField(unique=True, verbose_name="Link Uzantısı", null=True, blank=True)
    
    def __str__(self): return self.isim
    class Meta: verbose_name_plural = "Kategoriler"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.isim)
        super().save(*args, **kwargs)

class Ilce(models.Model):
    isim = models.CharField(max_length=100, verbose_name="İlçe Adı")
    def __str__(self): return self.isim
    class Meta: verbose_name_plural = "İlçeler"

# ==========================================
# ✍️ KÖŞE YAZARLARI VE YAZILARI
# ==========================================

class KoseYazari(models.Model):
    ad_soyad = models.CharField(max_length=100, verbose_name="Ad Soyad")
    
    resim = ProcessedImageField(
        upload_to='yazarlar/',
        processors=[ResizeToFit(500, 500)],
        format='JPEG',
        options={'quality': 70},
        verbose_name="Yazar Resmi"
    )
    
    biyografi = models.TextField(blank=True, verbose_name="Kısa Biyografi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    basyazar_mi = models.BooleanField(default=False, verbose_name="Başyazar mı?")
    def __str__(self): return self.ad_soyad
    class Meta: verbose_name_plural = "Köşe Yazarları"
    
    @property
    def son_yazisi(self):
        return self.yazilar.filter(aktif_mi=True).order_by('-yayin_tarihi').first()

class KoseYazisi(models.Model):
    yazar = models.ForeignKey(KoseYazari, on_delete=models.CASCADE, related_name='yazilar', verbose_name="Yazar")
    baslik = models.CharField(max_length=200, verbose_name="Yazı Başlığı")
    icerik = RichTextUploadingField(verbose_name="Yazı İçeriği")
    
    manset_mi = models.BooleanField(default=False, verbose_name="Manşette Gösterilsin mi?")
    
    manset_resmi = ProcessedImageField(
        upload_to='manset_yazilari/',
        processors=[ResizeToFit(800, 600)],
        format='JPEG',
        options={'quality': 60},
        verbose_name="Manşet Görseli (Yatay)",
        blank=True, null=True
    )
    
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Yayınlanma Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")
    video_link = models.URLField(blank=True, null=True, verbose_name="Video Linki (YouTube)")

    def __str__(self): return f"{self.yazar.ad_soyad} - {self.baslik}"
    class Meta: verbose_name_plural = "Köşe Yazıları"; ordering = ['-yayin_tarihi']
    
    @property
    def embed_video_url(self): return get_youtube_embed(self.video_link)

# ==========================================
# 📰 HABER MODELİ (GÜNCELLENDİ)
# ==========================================

class Haber(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Haber Başlığı")
    ozet = models.TextField(verbose_name="Kısa Özet", blank=True)
    icerik = RichTextUploadingField(verbose_name="Haber İçeriği")
    
    resim = ProcessedImageField(
        upload_to='haber_resimleri/',
        processors=[ResizeToFit(800, 600)],
        format='JPEG',
        options={'quality': 60},
        verbose_name="Haber Resmi",
        blank=True
    )

    # 1. Alan zaten buradaydı, koruyoruz:
    video_link = models.URLField(blank=True, null=True, verbose_name="Video Linki (YouTube)")
    
    son_dakika = models.BooleanField(default=False, verbose_name="Son Dakika Haberi mi?")
    ulusal_mi = models.BooleanField(default=False, verbose_name="Ulusal Haber mi?")
    manset_mi = models.BooleanField(default=False, verbose_name="Manşette Göster")

    kategori = models.ForeignKey(Kategori, on_delete=models.CASCADE, verbose_name="Kategori")
    ilce = models.ForeignKey(Ilce, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="İlçe (Varsa)")
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Yayınlanma Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")

    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Haberler"; ordering = ['-yayin_tarihi']

    # 2. Template'de kullanacağımız SİHİRLİ DÖNÜŞTÜRÜCÜ (Yeni ekledim)
    @property
    def youtube_embed_url(self):
        if self.video_link:
            # YouTube linkinden ID'yi çeken basit mantık
            video_id = None
            if "youtube.com" in self.video_link and "v=" in self.video_link:
                try:
                    video_id = self.video_link.split("v=")[1].split("&")[0]
                except:
                    return None
            elif "youtu.be" in self.video_link:
                try:
                    video_id = self.video_link.split("/")[-1].split("?")[0]
                except:
                    return None
            
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"
        return None

# ==========================================
# 🎄 ÖZEL GÜN VE TEBRİK MESAJLARI
# ==========================================

class OzelGun(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Özel Gün Adı (Örn: 2025 Yılbaşı)")
    slug = models.SlugField(unique=True, verbose_name="Link Uzantısı (Otomatik)")
    aciklama = models.TextField(blank=True, verbose_name="Sayfa Üst Yazısı / Artvizyon Mesajı")
    
    kapak_resmi = ProcessedImageField(
        upload_to='ozel_gunler/',
        processors=[ResizeToFit(1000, 800)],
        format='JPEG',
        options={'quality': 70},
        blank=True,
        verbose_name="Sayfa Kapak Resmi"
    )
    
    aktif_mi = models.BooleanField(default=True, verbose_name="Aktif mi?")
    anasayfada_goster = models.BooleanField(default=False, verbose_name="Anasayfada Slayt Olarak Göster")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Özel Gün Yönetimi"

class TebrikMesaji(models.Model):
    ozel_gun = models.ForeignKey(OzelGun, on_delete=models.CASCADE, related_name='mesajlar')
    ad_soyad = models.CharField(max_length=100, verbose_name="Kişi / Kurum Adı")
    unvan = models.CharField(max_length=150, blank=True, verbose_name="Ünvanı")
    mesaj_metni = models.TextField(blank=True, verbose_name="Mesajı")
    
    resim = ProcessedImageField(
        upload_to='tebrikler/',
        processors=[ResizeToFit(600, 600)],
        format='JPEG',
        options={'quality': 70},
        verbose_name="Kişi Fotoğrafı"
    )
    
    instagram_gorseli = models.ImageField(upload_to='instagram_postlari/', blank=True, null=True, verbose_name="Hazır Post")
    video_link = models.URLField(blank=True, null=True, verbose_name="Video Linki (Varsa)")
    sira = models.PositiveIntegerField(default=0, verbose_name="Sıralama")

    def __str__(self): return self.ad_soyad
    class Meta: ordering = ['sira']
    
    @property
    def embed_video_url(self): return get_youtube_embed(self.video_link)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.resim and not self.instagram_gorseli:
            self.instagram_gorseli_olustur()

    def instagram_gorseli_olustur(self):
        try:
            W, H = 1080, 1080
            img = Image.new('RGB', (W, H), color='#0f2c1f')
            draw = ImageDraw.Draw(img)
            draw.rectangle([(20, 20), (W-20, H-20)], outline="#D4AF37", width=15)
            
            try:
                font_baslik = ImageFont.truetype("Arial", 60)
                font_isim = ImageFont.truetype("Arial", 55)
                font_unvan = ImageFont.truetype("Arial", 35)
                font_mesaj = ImageFont.truetype("Arial", 40)
            except:
                font_baslik = ImageFont.load_default()
                font_isim = ImageFont.load_default()
                font_unvan = ImageFont.load_default()
                font_mesaj = ImageFont.load_default()

            draw.text((W/2, 100), "ARTVİZYON HABER", font=font_baslik, fill="#D4AF37", anchor="mm")
            draw.text((W/2, 170), "YENİ YIL ÖZEL", font=font_unvan, fill="white", anchor="mm")

            if self.resim:
                kisi_img = Image.open(self.resim.path).convert("RGBA")
                size = (450, 450)
                mask = Image.new('L', size, 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0) + size, fill=255)
                kisi_img = ImageOps.fit(kisi_img, size, centering=(0.5, 0.5))
                kisi_img.putalpha(mask)
                img.paste(kisi_img, (int((W-450)/2), 250), kisi_img)
                draw.ellipse((int((W-450)/2), 250, int((W-450)/2)+450, 700), outline="#D4AF37", width=8)

            draw.text((W/2, 760), self.ad_soyad.upper(), font=font_isim, fill="white", anchor="mm")
            draw.text((W/2, 820), self.unvan, font=font_unvan, fill="#cccccc", anchor="mm")

            mesaj = f'"{self.mesaj_metni}"'
            lines = textwrap.wrap(mesaj, width=40)
            y_text = 900
            for line in lines:
                draw.text((W/2, y_text), line, font=font_mesaj, fill="#D4AF37", anchor="mm")
                y_text += 50

            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=95)
            self.instagram_gorseli.save(f'insta_{self.id}.jpg', ContentFile(buffer.getvalue()), save=False)
            super().save(update_fields=['instagram_gorseli'])
            
        except Exception as e:
            print(f"HATA: {e}")

# ==========================================
# 🎭 DİĞER MODELLER
# ==========================================

class Galeri(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Galeri Başlığı")
    kapak_resmi = ProcessedImageField(
        upload_to='galeri_kapak/',
        processors=[ResizeToFit(800, 600)],
        format='JPEG',
        options={'quality': 60},
        verbose_name="Kapak Resmi"
    )
    yayin_tarihi = models.DateTimeField(default=timezone.now)
    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Fotoğraf Galerileri"

class GaleriResim(models.Model):
    galeri = models.ForeignKey(Galeri, on_delete=models.CASCADE, related_name='resimler')
    resim = ProcessedImageField(
        upload_to='galeri_resimleri/',
        processors=[ResizeToFit(1024, 768)], 
        format='JPEG',
        options={'quality': 70}
    )
    aciklama = models.CharField(max_length=200, blank=True, verbose_name="Resim Açıklaması (Opsiyonel)")

class HaftaninFotografi(models.Model):
    resim = ProcessedImageField(
        upload_to='haftanin_fotografi/',
        processors=[ResizeToFit(1200, 900)],
        format='JPEG',
        options={'quality': 75},
        verbose_name="Fotoğraf"
    )
    baslik = models.CharField(max_length=200, verbose_name="Başlık / Açıklama")
    ceken = models.CharField(max_length=100, verbose_name="Fotoğrafı Çeken", default='Artvizyon')
    aktif_mi = models.BooleanField(default=True)
    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Haftanın Fotoğrafı"

class Siir(models.Model):
    baslik = models.CharField(max_length=200, verbose_name="Şiir Başlığı")
    sair = models.CharField(max_length=100, verbose_name="Şair")
    siir_metni = RichTextUploadingField(verbose_name="Şiir Metni")
    
    resim = ProcessedImageField(
        upload_to='siir_resimleri/',
        processors=[ResizeToFit(600, 600)],
        format='JPEG',
        options={'quality': 60},
        verbose_name="Şiir Görseli",
        blank=True
    )
    
    gunun_siiri_mi = models.BooleanField(default=False, verbose_name="Günün Şiiri Olarak Ayarla")
    
    yayin_tarihi = models.DateTimeField(default=timezone.now, verbose_name="Eklenme Tarihi")
    aktif_mi = models.BooleanField(default=True, verbose_name="Yayında mı?")

    def __str__(self): return self.baslik
    class Meta: verbose_name_plural = "Şiir Köşesi"; ordering = ['-yayin_tarihi']

    def save(self, *args, **kwargs):
        if self.gunun_siiri_mi:
            Siir.objects.filter(gunun_siiri_mi=True).exclude(id=self.id).update(gunun_siiri_mi=False)
        super().save(*args, **kwargs)

class EczaneLinki(models.Model):
    ilce_adi = models.CharField(max_length=50, verbose_name="İlçe Adı (Örn: Hopa)")
    url = models.URLField(verbose_name="Eczane Listesi Linki")
    sira = models.PositiveIntegerField(default=0)
    def __str__(self): return self.ilce_adi
    class Meta: verbose_name_plural = "Nöbetçi Eczane Linkleri"; ordering = ['sira']

class Yorum(models.Model):
    haber = models.ForeignKey(Haber, on_delete=models.CASCADE, related_name='yorumlar', null=True, blank=True)
    kose_yazisi = models.ForeignKey(KoseYazisi, on_delete=models.CASCADE, related_name='yorumlar', null=True, blank=True)
    siir = models.ForeignKey(Siir, on_delete=models.CASCADE, related_name='yorumlar', null=True, blank=True)
    isim = models.CharField(max_length=80, verbose_name="Ad Soyad")
    email = models.EmailField(verbose_name="E-posta", blank=True)
    govde = models.TextField(verbose_name="Yorumunuz")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    aktif = models.BooleanField(default=False, verbose_name="Yayınlansın mı?")
    def __str__(self): return f"Yorum: {self.isim}"
    class Meta: ordering = ['-olusturulma_tarihi']

class Destekci(models.Model):
    PAKETLER = (('okur', 'Okur Destekçisi'), ('gonul', 'Gönül Dostu'), ('sponsor', 'Ana Sponsor'))
    isim = models.CharField(max_length=100, verbose_name="Destekçi Adı / Firma")
    email = models.EmailField(blank=True)
    paket = models.CharField(max_length=20, choices=PAKETLER, default='okur')
    baslangic_tarihi = models.DateTimeField(auto_now_add=True)
    bitis_tarihi = models.DateTimeField(null=True, blank=True, verbose_name="Destek Bitiş Tarihi")
    aktif_mi = models.BooleanField(default=False)
    def __str__(self): return self.isim
    class Meta: verbose_name_plural = "Aboneler ve Destekçiler"