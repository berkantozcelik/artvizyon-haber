from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps 

# Modellerin hepsini içeri alıyoruz
from .models import (
    Haber, Kategori, Ilce, KoseYazari, KoseYazisi, 
    Galeri, GaleriResim, Siir, 
    EczaneLinki, Yorum, Destekci,
    OzelGun, TebrikMesaji, TarihiYer 
)
# Geri alma (Undo) özelliği için gerekli kütüphane
from reversion.admin import VersionAdmin

# =========================================================
# 📸 1. INSTAGRAM POST OLUŞTURUCU FONKSİYONLAR
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
    
    # Yazı Ayarları
    try:
        # Font yolları (Linux sunucu uyumlu)
        font_baslik = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 75)
        font_ozet = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        font_handle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font_baslik = ImageFont.load_default()
        font_ozet = ImageFont.load_default()
        font_handle = ImageFont.load_default()
        
    text_x = 100
    text_y = 450
    text_width = 880
    
    # Başlık ve Özet Yazdır
    next_y = draw_text_left_aligned(draw, haber.baslik.upper(), text_x, text_y, font_baslik, text_width, (255, 255, 255))
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
# 📝 2. MODEL KAYITLARI (ADMİN PANELİ AYARLARI)
# =========================================================

# --- HABER YÖNETİMİ (GERİ ALMA EKLENDİ) ---
@admin.register(Haber)
class HaberAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'kategori', 'yayin_tarihi', 'aktif_mi', 'manset_mi', 'son_dakika')
    list_editable = ('aktif_mi', 'manset_mi', 'son_dakika') 
    list_filter = ('aktif_mi', 'manset_mi', 'son_dakika', 'kategori')
    search_fields = ('baslik', 'ozet')
    date_hierarchy = 'yayin_tarihi'
    actions = [generate_instagram_post]
    save_on_top = True
    fieldsets = (
        ('Temel Bilgiler (Gerekli)', {
            'fields': ('baslik', 'kategori', 'ilce', 'ozet', 'icerik'),
            'description': 'Başlık, kategori ve kısa özet yeterli. Metinde kullandığınız görsellere kaynak eklemek için img etiketine data-kaynak="AA" yazabilirsiniz.'
        }),
        ('Medya', {
            'fields': ('resim', 'foto_kaynak', 'video_link'),
            'description': 'Manşet görseli ve varsa YouTube linki.'
        }),
        ('Yayın Ayarları', {
            'fields': ('aktif_mi', 'yayin_tarihi', 'son_dakika', 'manset_mi', 'ulusal_mi', 'roportaj_mi'),
            'description': 'Sadece gerekli kutuları işaretleyin. Geri almak için sağ üstteki “Geçmiş” bağlantısını kullanabilirsiniz.'
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'icerik':
            formfield.help_text = 'İçerikteki görsellere kaynak etiketi eklemek için img etiketine data-kaynak="AA" yazın (örn: data-kaynak="AA").'
        return formfield

# --- GALERİ YÖNETİMİ (GERİ ALMA EKLENDİ) ---
class GaleriResimInline(admin.TabularInline):
    model = GaleriResim
    fields = ('resim', 'aciklama', 'haftanin_fotografi_mi')
    extra = 3
    verbose_name = "Fotoğraf"
    verbose_name_plural = "Fotoğraflar"

@admin.register(Galeri)
class GaleriAdmin(VersionAdmin): # VersionAdmin kullanıldı
    inlines = [GaleriResimInline]
    list_display = ('baslik', 'yayin_tarihi')

# --- YAZARLAR VE YAZILARI (GERİ ALMA EKLENDİ) ---
@admin.register(KoseYazari)
class KoseYazariAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('ad_soyad', 'basyazar_mi', 'aktif_mi')
    list_editable = ('basyazar_mi', 'aktif_mi')

@admin.register(KoseYazisi)
class KoseYazisiAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'yazar', 'yayin_tarihi', 'aktif_mi')
    list_filter = ('yazar', 'aktif_mi')
    search_fields = ('baslik',)
    save_on_top = True
    fieldsets = (
        ('Temel Bilgiler (Gerekli)', {
            'fields': ('baslik', 'yazar', 'icerik'),
            'description': 'Başlık ve içerik alanlarını doldurun. Metindeki görsellere kaynak vermek için img etiketine data-kaynak="AA" yazabilirsiniz.'
        }),
        ('Medya', {
            'fields': ('manset_resmi', 'foto_kaynak', 'video_link'),
        }),
        ('Yayın Ayarları', {
            'fields': ('aktif_mi', 'yayin_tarihi', 'manset_mi'),
            'description': 'Sadece gerekli kutuları işaretleyin. Geri almak için sağ üstteki “Geçmiş” bağlantısını kullanabilirsiniz.'
        }),
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'icerik':
            formfield.help_text = 'Metin içi görsellere kaynak eklemek için img etiketine data-kaynak="AA" yazın.'
        return formfield

# --- YORUM YÖNETİMİ (GERİ ALMA EKLENDİ) ---
@admin.register(Yorum)
class YorumAdmin(VersionAdmin): # VersionAdmin kullanıldı
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

# --- DESTEKÇİLER (GERİ ALMA EKLENDİ) ---
@admin.register(Destekci)
class DestekciAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('isim', 'paket', 'bitis_tarihi', 'aktif_mi')
    list_filter = ('paket', 'aktif_mi')
    search_fields = ('isim', 'email')

# --- ŞİİR KÖŞESİ (GERİ ALMA EKLENDİ) ---
@admin.register(Siir)
class SiirAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'sair', 'yayin_tarihi', 'aktif_mi')
    search_fields = ('baslik', 'sair')
    list_filter = ('aktif_mi',)

# --- ECZANE LİNKLERİ (GERİ ALMA EKLENDİ) ---
# --- ÖZEL GÜN VE INSTAGRAM İNDİRME BUTONU (GERİ ALMA EKLENDİ) ---
class TebrikMesajiInline(admin.TabularInline):
    model = TebrikMesaji
    extra = 1
    fields = ('sira', 'ad_soyad', 'unvan', 'mesaj_metni', 'resim', 'video_link', 'instagram_indir')
    readonly_fields = ('instagram_indir',) 

    def instagram_indir(self, obj):
        if obj.instagram_gorseli:
            return format_html(
                '''<a href="{}" target="_blank" 
                style="background-color:#E1306C; color:white; padding:6px 12px; border-radius:15px; text-decoration:none; font-weight:bold; font-size:12px;">
                📸 Instagram İndir
                </a>''',
                obj.instagram_gorseli.url
            )
        return "Görsel, kaydettikten sonra oluşur."
    instagram_indir.short_description = "Sosyal Medya"

@admin.register(OzelGun)
class OzelGunAdmin(VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'aktif_mi', 'anasayfada_goster')
    list_editable = ('aktif_mi', 'anasayfada_goster')
    prepopulated_fields = {'slug': ('baslik',)} 
    inlines = [TebrikMesajiInline]

# --- BASİT KAYITLAR (GERİ ALMA ÖZELLİĞİ İÇİN SINIF HALİNE GETİRİLDİ) ---

@admin.register(TarihiYer)
class TarihiYerAdmin(VersionAdmin):
    list_display = ('baslik',)

@admin.register(Kategori)
class KategoriAdmin(VersionAdmin):
    list_display = ('isim', 'slug')
    prepopulated_fields = {'slug': ('isim',)}

# İstenmeyen bölümleri panelden kaldır (örn. Nöbetçi Eczane)
for model in (EczaneLinki,):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

@admin.register(Ilce)
class IlceAdmin(VersionAdmin):
    list_display = ('isim',)
