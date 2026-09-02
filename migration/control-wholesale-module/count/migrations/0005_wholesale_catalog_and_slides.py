from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

import count.validators


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0004_wholesale_inventory"),
    ]

    operations = [
        migrations.AddField(
            model_name="wholesalepublication",
            name="catalog_title",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Si se deja vacío se usa el nombre de la plataforma.",
                max_length=150,
                verbose_name="Título en catálogo",
            ),
        ),
        migrations.AddField(
            model_name="wholesalepublication",
            name="catalog_description",
            field=models.CharField(
                blank=True,
                default="",
                max_length=300,
                verbose_name="Descripción en catálogo",
            ),
        ),
        migrations.AddField(
            model_name="wholesalepublication",
            name="catalog_image",
            field=models.ImageField(
                blank=True,
                help_text="Si se deja vacía se usa el logo de la plataforma.",
                null=True,
                upload_to="wholesale/catalog/",
                validators=[count.validators.valid_image_extension],
                verbose_name="Imagen del catálogo",
            ),
        ),
        migrations.AddField(
            model_name="wholesalepublication",
            name="featured",
            field=models.BooleanField(default=False, verbose_name="Destacado"),
        ),
        migrations.AddField(
            model_name="wholesalepublication",
            name="sort_order",
            field=models.PositiveIntegerField(default=0, verbose_name="Orden"),
        ),
        migrations.CreateModel(
            name="WholesaleSlide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=150, verbose_name="Título")),
                ("subtitle", models.CharField(blank=True, default="", max_length=300, verbose_name="Descripción")),
                ("image", models.ImageField(upload_to="wholesale/slides/", validators=[count.validators.valid_image_extension], verbose_name="Imagen")),
                ("button_text", models.CharField(blank=True, default="", max_length=60, verbose_name="Texto del botón")),
                ("button_url", models.URLField(blank=True, default="", max_length=500, verbose_name="Enlace del botón")),
                ("active", models.BooleanField(default=True, verbose_name="Publicado")),
                ("sort_order", models.PositiveIntegerField(default=0, verbose_name="Orden")),
                ("starts_at", models.DateTimeField(blank=True, null=True, verbose_name="Publicar desde")),
                ("ends_at", models.DateTimeField(blank=True, null=True, verbose_name="Publicar hasta")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="wholesale_slides_created", to=settings.AUTH_USER_MODEL, verbose_name="Creado por")),
            ],
            options={
                "verbose_name": "Anuncio de MyPlataforma",
                "verbose_name_plural": "Anuncios de MyPlataforma",
                "ordering": ("sort_order", "-updated_at"),
            },
        ),
    ]
