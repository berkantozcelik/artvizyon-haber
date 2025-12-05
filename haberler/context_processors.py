from .models import Kategori, Ilce, Haber

def global_veriler(request):
    # Tüm sayfalarda geçerli veriler
    return {
        'global_kategoriler': Kategori.objects.all(),
        'global_ilceler': Ilce.objects.all(),
        # Son 5 haberi "Son Dakika" olarak çekiyoruz
        'son_dakika': Haber.objects.filter(aktif_mi=True).order_by('-yayin_tarihi')[:5] 
    }