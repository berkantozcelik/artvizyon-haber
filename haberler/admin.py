from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
from django.utils.html import format_html
from django.utils import timezone
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps 

from .models import (
    Haber, Kategori, Ilce, KoseYazari, KoseYazisi, 
    Galeri, GaleriResim, HaftaninFotografi, Siir, 
    EczaneLinki, Yorum, Destekci
)

# =========================================================
# 📸 1. INSTAGRAM POST OLUŞTURMA MOTORU (MEVCUT KODUN)
# =========================================================

def draw_text_left_aligned(draw, text, x_pos, y_pos, font, max_width, fill):
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
    canvas_size = (1080, 1080)
    bg_color = (43, 27, 24)
    bg_img = None
    if haber.resim:
        try: bg_img = Image.open(haber.resim.path).convert("RGBA")
        except: pass
    if bg_img:
        bg_img = ImageOps.fit(bg_img, canvas_size, method=Image.Resampling.LANCZOS)
        enhancer = ImageEnhance.Brightness(bg_img)
        bg_img = enhancer.enhance(0.25)
    else:
        bg_img = Image.new('RGBA', canvas_size, color=bg_color)
    img = bg_img
    draw = ImageDraw.Draw(img)
    text_color = (255, 255, 255)
    try:
        # Font yolları sunucuda farklı olabilir, hata almamak için try-except var
        font_baslik = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        font_ozet = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        font_handle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font_baslik = ImageFont.load_default()
        font_ozet = ImageFont.load_default()
        font_handle = ImageFont.load_default()
        
    left_margin = 60
    current_y = 60
    logo_path = os.path.join(settings.BASE_DIR, 'logo.png') # Logo varsa ekler
    if os.path.exists(logo_path):
        try:
            logo_img = Image.open(logo_path).convert("RGBA")
            wpercent = (250 / float(logo_img.size[0]))
            hsize = int((float(logo_img.size[1]) * float(wpercent)))
            logo_img = logo_img.resize((250, hsize), Image.Resampling.LANCZOS)
            img.paste(logo_img, (left_margin, current_y), logo_img)
        except: pass
        
    text_x = 100
    text_y = 450
    text_width = 880
    next_y = draw_text_left_aligned(draw, haber.baslik.upper(), text_x, text_y, font_baslik, text_width, text_color)
    if haber.ozet:
        ozet_metni = (haber.ozet[:130] + '...') if len(haber.ozet) > 130 else haber.ozet
        draw_text_left_aligned(draw, ozet_metni, text_x, next_y + 40, font_ozet, text_width, (220, 220, 220))
    draw.text((100, 980), "Detaylar ve haberin devamı için link biyografide ->", font=font_handle, fill=(255, 215, 0))
    img = img.convert("RGB")
    response = HttpResponse(content_type="image/jpeg")
    response['Content-Disposition'] = f'attachment; filename=insta-post-{haber.pk}.jpg'
    img.save(response, "JPEG", quality=100)
    return response

# =========================================================
# 📝 2. MODELLERİN KAYDI
# =========================================================

# --- HABER YÖNETİMİ ---
@admin.register(Haber)
class HaberAdmin(admin.ModelAdmin):
    # Listede görünecek sütunlar (Son Dakika eklendi)
    list_display = ('baslik', 'kategori', 'yayin_tarihi', 'aktif_mi', 'manset_mi', 'son_dakika')
    # Listeden çıkmadan tik atıp değiştirebileceğin alanlar
    list_editable = ('aktif_mi', 'manset_mi', 'son_dakika') 
    list_filter = ('aktif_mi', 'manset_mi', 'son_dakika', 'kategori')
    search_fields = ('baslik', 'ozet')
    date_hierarchy = 'yayin_tarihi'
    actions = [generate_instagram_post] # Instagram butonu burada

# --- GALERİ YÖNETİMİ ---
class GaleriResimInline(admin.TabularInline):
    model = GaleriResim
    extra = 3

@admin.register(Galeri)
class GaleriAdmin(admin.ModelAdmin):
    inlines = [GaleriResimInline]
    list_display = ('baslik', 'yayin_tarihi')

# --- YAZARLAR VE YAZILARI ---
@admin.register(KoseYazari)
class KoseYazariAdmin(admin.ModelAdmin):
    list_display = ('ad_soyad', 'basyazar_mi', 'aktif_mi')
    list_editable = ('basyazar_mi', 'aktif_mi')

@admin.register(KoseYazisi)
class KoseYazisiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'yazar', 'yayin_tarihi', 'aktif_mi')
    list_filter = ('yazar', 'aktif_mi')
    search_fields = ('baslik',)

# --- YORUM YÖNETİMİ (GELİŞMİŞ) ---
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
    
    def icerik_kaynagi(self, obj):
        if obj.haber: return f"Haber: {obj.haber.baslik[:20]}..."
        elif obj.kose_yazisi: return f"Yazı: {obj.kose_yazisi.baslik[:20]}..."
        elif obj.siir: return f"Şiir: {obj.siir.baslik[:20]}..."
        return "-"
    
    def durum_ikonu(self, obj):
        return format_html('<span style="color:green;">✔ Yayında</span>') if obj.aktif else format_html('<span style="color:red;">⏳ Onay Bekliyor</span>')
    durum_ikonu.short_description = "Durum"

# --- ABONE / DESTEKÇİ YÖNETİMİ ---
@admin.register(Destekci)
class DestekciAdmin(admin.ModelAdmin):
    list_display = ('isim', 'paket_renkli', 'bitis_tarihi', 'kalan_gun', 'aktif_mi')
    list_filter = ('paket', 'aktif_mi')
    search_fields = ('isim', 'email')
    
    def kalan_gun(self, obj):
        if not obj.bitis_tarihi: return "-"
        fark = obj.bitis_tarihi - timezone.now()
        if fark.days > 0: return f"{fark.days} Gün Kaldı"
        return format_html('<span style="color:red; font-weight:bold;">SÜRESİ DOLDU</span>')
    
    def paket_renkli(self, obj):
        renkler = {'okur': 'blue', 'gonul': 'green', 'sponsor': 'orange'}
        renk = renkler.get(obj.paket, 'black')
        return format_html('<span style="color:{}; font-weight:bold;">{}</span>', renk, obj.get_paket_display())

# --- ŞİİR KÖŞESİ ---
@admin.register(Siir)
class SiirAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'sair', 'yayin_tarihi', 'aktif_mi')
    search_fields = ('baslik', 'sair')
    list_filter = ('aktif_mi',)

# --- ECZANE LİNKLERİ ---
@admin.register(EczaneLinki)
class EczaneLinkiAdmin(admin.ModelAdmin):
    list_display = ('ilce_adi', 'url', 'sira')
    list_editable = ('url', 'sira')

# --- DİĞER BASİT KAYITLAR ---
admin.site.register(Kategori)
admin.site.register(Ilce)
admin.site.register(HaftaninFotografi)