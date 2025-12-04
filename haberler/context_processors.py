from .models import Kategori, Ilce

def kategoriler(request):
    return {
        'global_kategoriler': Kategori.objects.all(),
        'global_ilceler': Ilce.objects.all() # <--- İlçeleri de gönderdik
    }