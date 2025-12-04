from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
from django.utils.html import format_html
from django.utils import timezone
import os
import textwrap

# Resim işleme kütüphaneleri
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps 

# Modellerin Hepsini Çağırıyoruz
from .models import (
    Kategori, Haber, Galeri, GaleriResim, 
    HaftaninFotografi, Ilce, EczaneLinki, 
    KoseYazari, KoseYazisi, Yorum, Destekci
)

# =========================================================
# 📸 1. INSTAGRAM POST OLUŞTURMA MOTORU (BPT TARZI)
# =========================================================

def draw_text_left_aligned(draw, text, x_pos, y_pos, font, max_width, fill):
    """Metni sola yaslı şekilde satırlara böler ve yazar"""
    try: avg_char = font.getlength("A")
    except: avg_char = 20
    
    chars_per_line = int(max_width / avg_char)
    wrapper = textwrap.TextWrapper(width=chars_per_line, break_long_words=False)
    lines = wrapper.wrap(text)
    
    try: line_height = font.getbbox("Ay")[3] + 15
    except: line_height = 50
    
    current_y = y_pos
    for line in lines:
        draw.text((x_pos, current_y), line, font=font, fill=fill)
        current_y += line_height
    return current_y

@admin.action(description='📸 Seçili haber için PRO Instagram Postu oluştur')
def generate_instagram_post(modeladmin, request, queryset):
    haber = queryset.first()
    if not haber: return

    # Tuval Hazırlığı
    canvas_size = (1080, 1080)
    bg_color = (43, 27, 24)

    # Resmi Yükle
    bg_img = None
    if haber.resim:
        try:
            bg_img = Image.open(haber.resim.path).convert("RGBA")
        except:
            pass

    if bg_img:
        # Resmi ortala ve kırp
        bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.Resampling.LANCZOS)
        # Karanlık filtre (%25 parlaklık)
        enhancer = ImageEnhance.Brightness(bg_img)
        bg_img = enhancer.enhance(0.25)
    else:
        bg_img = Image.new('RGBA', canvas_size, color=bg_color)

    img = bg_img
    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)

    # Font Ayarları (Sistem fontlarını dener, bulamazsa default kullanır)
    try:
        font_baslik = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 75)
        font_ozet = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        font_handle = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
    except:
        font_baslik = ImageFont.load_default()
        font_ozet = ImageFont.load_default()
        font_handle = ImageFont.load_default()

    # Logo ve İkon Yerleşimi
    left_margin = 60
    current_y = 60
    
    # Logo
    logo_path = os.path.join(settings.BASE_DIR, 'logo.png') # Ana dizinde logo.png olmalı
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            wpercent = (250 / float(logo_img.size[0]))
            hsize = int((float(logo_img.size[1]) * float(wpercent)))
            logo_img = logo_img.resize((250, hsize), Image.Resampling.LANCZOS)
            img.paste(logo_img, (left_margin, current_y), logo_img)
        except: pass

    # Metin Yerleşimi
    text_x = 100
    text_y = 450
    text_width = 880

    # Başlık
    next_y = draw_text_left_aligned(draw, haber.baslik.upper(), text_x, text_y, font_baslik, text_width, text_color)
    
    # Özet
    if haber.ozet:
        ozet_metni = (haber.ozet[:130] + '...') if len(haber.ozet) > 130 else haber.ozet
        draw_text_left_aligned(draw, ozet_metni, text_x, next_y + 40, font_ozet, text_width, (220, 220, 220))

    # Alt Bilgi
    draw.text((100, 980), "Detaylar ve haberin devamı için link biyografide ->", font=font_handle, fill=(255, 215, 0))

    # Çıktı
    img = img.convert("RGB")
    response = HttpResponse(content_type="image/jpeg")
    response['Content-Disposition'] = f'attachment; filename=insta-post-{haber.pk}.jpg'
    img.save(response, "JPEG", quality=100)
    return response


# =========================================================
# 📰 2. HABER VE İÇERİK YÖNETİMİ
# =========================================================

@admin.register(Haber)
class HaberAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kategori', 'yayin_tarihi', 'aktif_mi', 'manset_mi')
    list_filter = ('aktif_mi', 'manset_mi', 'kategori')
    search_fields = ('baslik', 'ozet')
    date_hierarchy = 'yayin_tarihi'
    actions = [generate_instagram_post] # <-- Post oluşturucu burada aktif

# Galeri Ayarları
class GaleriResimInline(admin.TabularInline):
    model = GaleriResim
    extra = 3

@admin.register(Galeri)
class GaleriAdmin(admin.ModelAdmin):
    inlines = [GaleriResimInline]
    list_display = ('baslik', 'yayin_tarihi')

# Basit Kayıtlar
admin.site.register(Kategori)
admin.site.register(Ilce)
admin.site.register(HaftaninFotografi)

@admin.register(EczaneLinki)
class EczaneLinkiAdmin(admin.ModelAdmin):
    list_display = ('ilce_adi', 'url')
    list_editable = ('url',)


# =========================================================
# ✍️ 3. KÖŞE YAZARLARI
# =========================================================

@admin.register(KoseYazari)
class KoseYazariAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'aktif_mi')

@admin.register(KoseYazisi)
class KoseYazisiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'yazar', 'yayin_tarihi', 'aktif_mi')
    list_filter = ('yazar', 'aktif_mi')
    search_fields = ('baslik', 'icerik')


# =========================================================
# 💬 4. YORUM YÖNETİMİ (GELİŞMİŞ)
# =========================================================

@admin.register(Yorum)
class YorumAdmin(admin.ModelAdmin):
    list_display = ('isim', 'govde_kisalt', 'icerik_kaynagi', 'olusturulma_tarihi', 'durum_ikonu')
    list_filter = ('aktif', 'olusturulma_tarihi')
    search_fields = ('isim', 'email', 'govde')
    actions = ['yorumlari_onayla']

    def yorumlari_onayla(self, request, queryset):
        queryset.update(aktif=True)
    yorumlari_onayla.short_description = "Seçili yorumları onayla ve yayınla"

    def govde_kisalt(self, obj):
        return obj.govde[:50] + "..." if len(obj.govde) > 50 else obj.govde
    govde_kisalt.short_description = "Yorum İçeriği"

    # Yorumun habere mi yoksa köşe yazısına mı yapıldığını gösterir
    def icerik_kaynagi(self, obj):
        if obj.haber:
            return f"Haber: {obj.haber.baslik[:20]}..."
        elif obj.kose_yazisi:
            return f"Yazı: {obj.kose_yazisi.baslik[:20]}..."
        return "-"
    icerik_kaynagi.short_description = "İçerik"

    def durum_ikonu(self, obj):
        if obj.aktif:
            return format_html('<span style="color:green;">✔ Yayında</span>')
        return format_html('<span style="color:red;">⏳ Onay Bekliyor</span>')
    durum_ikonu.short_description = "Durum"


# =========================================================
# 💎 5. ABONELİK (DESTEKÇİ) YÖNETİMİ
# =========================================================

@admin.register(Destekci)
class DestekciAdmin(admin.ModelAdmin):
    list_display = ('isim', 'paket_renkli', 'bitis_tarihi', 'kalan_gun', 'aktif_mi')
    list_filter = ('paket', 'aktif_mi')
    search_fields = ('isim', 'email')
    
    # Kalan günü hesapla
    def kalan_gun(self, obj):
        if not obj.bitis_tarihi:
            return "-"
        fark = obj.bitis_tarihi - timezone.now()
        if fark.days > 0:
            return f"{fark.days} Gün Kaldı"
        return format_html('<span style="color:red; font-weight:bold;">SÜRESİ DOLDU</span>')
    kalan_gun.short_description = "Kalan Süre"

    # Paket ismini renkli göster
    def paket_renkli(self, obj):
        renkler = {
            'okur': 'blue',     # Okur Desteği (Mavi)
            'gonul': 'green',   # Gönül Dostu (Yeşil)
            'sponsor': 'orange' # Sponsor (Turuncu/Altın)
        }
        renk = renkler.get(obj.paket, 'black')
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', renk, obj.get_paket_display())
    paket_renkli.short_description = "Paket"