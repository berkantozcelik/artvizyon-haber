from io import BytesIO

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Kategori, KoseYazari


def make_test_image(name="test.jpg"):
    image = Image.new("RGB", (10, 10), "white")
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/jpeg")


class AnasayfaTests(TestCase):
    def test_anasayfa_ignores_yazar_without_son_yazisi(self):
        Kategori.objects.create(isim="Gundem")
        KoseYazari.objects.create(
            ad_soyad="Yazisi Olmayan Yazar",
            resim=make_test_image(),
            aktif_mi=True,
        )

        response = self.client.get(reverse("anasayfa"))

        self.assertEqual(response.status_code, 200)
