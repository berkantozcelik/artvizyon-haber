from django.db import migrations, models


def copy_sair_to_yazar(apps, schema_editor):
    Siir = apps.get_model("haberler", "Siir")
    KoseYazari = apps.get_model("haberler", "KoseYazari")
    for siir in Siir.objects.exclude(sair__isnull=True).exclude(sair__exact=""):
        if siir.yazar_id:
            continue
        yazar = KoseYazari.objects.filter(ad_soyad__iexact=siir.sair.strip()).first()
        if yazar:
            siir.yazar = yazar
            siir.save(update_fields=["yazar"])


class Migration(migrations.Migration):

    dependencies = [
        ("haberler", "0019_delete_haftaninfotografi_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="koseyazari",
            options={"verbose_name": "Yazar", "verbose_name_plural": "Yazarlar"},
        ),
        migrations.AddField(
            model_name="siir",
            name="yazar",
            field=models.ForeignKey(
                null=True,
                on_delete=models.SET_NULL,
                to="haberler.koseyazari",
                verbose_name="Yazar",
            ),
        ),
        migrations.AlterField(
            model_name="siir",
            name="sair",
            field=models.CharField(blank=True, max_length=100, verbose_name="Şair"),
        ),
        migrations.RunPython(copy_sair_to_yazar, migrations.RunPython.noop),
    ]
