from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
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
# 🧹 0. BASİT SİLME BUTONU (LISTEDE ÇÖP TENEKESİ)
# =========================================================

class DeleteLinkMixin:
    actions = None

    def delete_link(self, obj):
        url = reverse(f"admin:{obj._meta.app_label}_{obj._meta.model_name}_delete", args=[obj.pk])
        return format_html('<a class="button" href="{}" title="Sil">🗑</a>', url)
    delete_link.short_description = "Sil"


class EditorGuideMixin:
    editor_guide_text = ""

    def editor_guide(self, obj):
        if not self.editor_guide_text:
            return ""
        return format_html(
            '<details style="padding-top:4px;">'
            '<summary style="cursor:pointer;font-weight:700;">Kisa Rehber</summary>'
            '<div style="margin-top:8px;">{}</div>'
            '</details>',
            format_html(self.editor_guide_text),
        )
    editor_guide.short_description = "Kullanim"

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
class HaberAdmin(DeleteLinkMixin, EditorGuideMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'kategori', 'yayin_tarihi', 'okunma_sayisi', 'aktif_mi', 'manset_mi', 'son_dakika', 'delete_link')
    list_editable = ('aktif_mi', 'manset_mi', 'son_dakika') 
    list_filter = ('aktif_mi', 'manset_mi', 'son_dakika', 'kategori')
    search_fields = ('baslik', 'ozet')
    date_hierarchy = 'yayin_tarihi'
    save_on_top = True
    fields = (
        'baslik',
        'resim',
        'foto_kaynak',
        'kategori',
        'ilce',
        'ozet',
        'icerik',
        'editor_guide',
        'aktif_mi',
        'yayin_tarihi',
        'son_dakika',
        'manset_mi',
        'ulusal_mi',
        'roportaj_mi',
    )
    readonly_fields = ('editor_guide',)
    editor_guide_text = (
        '<ul style="margin:0 0 0 18px;">'
        '<li>Haber resmini "Haber Resmi" alanindan yukleyin.</li>'
        '<li>Foto kaynagi: AA, IHA gibi kisa kaynak yazin.</li>'
        '<li>Hedef icerik uzunlugu: 300-800 kelime (ozgun metin).</li>'
        '<li>Ozet: 2-3 cumle ile haberin ozunu anlatin.</li>'
        '<li>Video eklemek icin YouTube yukleme sayfasina gidin: '
        '<a href="https://www.youtube.com/upload" target="_blank" rel="noopener">YouTube Video Yukle</a>.</li>'
        '<li>Yukledikten sonra video linkini kopyalayin ve icerige su sekilde ekleyin:</li>'
        '<li><strong>(video: https://www.youtube.com/watch?v=...)</strong></li>'
        '<li>Icerikteki butonlar: B=kalin, I=italik, zincir=link, resim=icerige gorsel ekler.</li>'
        '<li>Tam ekran icin editor ustundeki "Buyut" ikonunu kullanin.</li>'
        '<li>Yayinlamak icin "Yayinda mi" acik olsun; tarih asagida.</li>'
        '</ul>'
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
class GaleriAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    inlines = [GaleriResimInline]
    list_display = ('baslik', 'yayin_tarihi', 'delete_link')

# --- YAZARLAR VE YAZILARI (GERİ ALMA EKLENDİ) ---
@admin.register(KoseYazari)
class KoseYazariAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('ad_soyad', 'basyazar_mi', 'aktif_mi', 'delete_link')
    list_editable = ('basyazar_mi', 'aktif_mi')

@admin.register(KoseYazisi)
class KoseYazisiAdmin(DeleteLinkMixin, EditorGuideMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'yazar', 'yayin_tarihi', 'okunma_sayisi', 'aktif_mi', 'delete_link')
    list_filter = ('yazar', 'aktif_mi')
    search_fields = ('baslik',)
    save_on_top = True
    fields = (
        'baslik',
        'yazar',
        'manset_resmi',
        'foto_kaynak',
        'icerik',
        'editor_guide',
        'aktif_mi',
        'yayin_tarihi',
        'manset_mi',
    )
    readonly_fields = ('editor_guide',)
    editor_guide_text = (
        '<ul style="margin:0 0 0 18px;">'
        '<li>Manset resmi ve foto kaynagi yukleyin.</li>'
        '<li>Hedef icerik uzunlugu: 300-800 kelime (ozgun metin).</li>'
        '<li>Baslik kisa ve net olsun; ilk paragraf ozeti versin.</li>'
        '<li>Video eklemek icin YouTube yukleme sayfasina gidin: '
        '<a href="https://www.youtube.com/upload" target="_blank" rel="noopener">YouTube Video Yukle</a>.</li>'
        '<li>Yukledikten sonra video linkini kopyalayin ve icerige su sekilde ekleyin:</li>'
        '<li><strong>(video: https://www.youtube.com/watch?v=...)</strong></li>'
        '<li>Icerikteki butonlar: B=kalin, I=italik, zincir=link, resim=icerige gorsel ekler.</li>'
        '<li>Tam ekran icin editor ustundeki "Buyut" ikonunu kullanin.</li>'
        '<li>Yayinlamak icin "Yayinda mi" acik olsun.</li>'
        '</ul>'
    )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'icerik':
            formfield.help_text = 'Metin içi görsellere kaynak eklemek için img etiketine data-kaynak="AA" yazın.'
        return formfield

# --- YORUM YÖNETİMİ (GERİ ALMA EKLENDİ) ---
@admin.register(Yorum)
class YorumAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('isim', 'govde_kisalt', 'icerik_kaynagi', 'olusturulma_tarihi', 'durum_ikonu', 'delete_link')
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
class DestekciAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('isim', 'paket', 'bitis_tarihi', 'aktif_mi', 'delete_link')
    list_filter = ('paket', 'aktif_mi')
    search_fields = ('isim', 'email')

# --- ŞİİR KÖŞESİ (GERİ ALMA EKLENDİ) ---
@admin.register(Siir)
class SiirAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'yazar_adi', 'yayin_tarihi', 'okunma_sayisi', 'aktif_mi', 'delete_link')
    search_fields = ('baslik', 'sair', 'yazar__ad_soyad')
    list_filter = ('aktif_mi',)
    fields = (
        'baslik',
        'yazar',
        'siir_metni',
        'resim',
        'gunun_siiri_mi',
        'aktif_mi',
        'yayin_tarihi',
    )

    def yazar_adi(self, obj):
        return obj.yazar.ad_soyad if obj.yazar else obj.sair
    yazar_adi.short_description = "Yazar"

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
class OzelGunAdmin(DeleteLinkMixin, VersionAdmin): # VersionAdmin kullanıldı
    list_display = ('baslik', 'aktif_mi', 'anasayfada_goster', 'delete_link')
    list_editable = ('aktif_mi', 'anasayfada_goster')
    prepopulated_fields = {'slug': ('baslik',)} 
    inlines = [TebrikMesajiInline]

@admin.register(TebrikMesaji)
class TebrikMesajiAdmin(DeleteLinkMixin, VersionAdmin):
    list_display = ('ad_soyad', 'ozel_gun', 'sira', 'delete_link')
    list_filter = ('ozel_gun',)
    search_fields = ('ad_soyad', 'ozel_gun__baslik')

# --- BASİT KAYITLAR (GERİ ALMA ÖZELLİĞİ İÇİN SINIF HALİNE GETİRİLDİ) ---

@admin.register(TarihiYer)
class TarihiYerAdmin(DeleteLinkMixin, VersionAdmin):
    list_display = ('baslik', 'delete_link')

@admin.register(Kategori)
class KategoriAdmin(DeleteLinkMixin, VersionAdmin):
    list_display = ('isim', 'slug', 'delete_link')
    prepopulated_fields = {'slug': ('isim',)}

# İstenmeyen bölümleri panelden kaldır (örn. Nöbetçi Eczane)
for model in (EczaneLinki,):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass

@admin.register(Ilce)
class IlceAdmin(DeleteLinkMixin, VersionAdmin):
    list_display = ('isim', 'delete_link')


User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DeleteLinkMixin, DjangoUserAdmin):
    list_display = DjangoUserAdmin.list_display + ('delete_link',)
