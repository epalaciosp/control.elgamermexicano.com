from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0009_catalog_sale_prices"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="wholesaleslide",
            options={
                "ordering": ("sort_order", "-updated_at"),
                "permissions": (
                    ("manage_myplataforma", "Puede administrar MyPlataforma"),
                ),
                "verbose_name": "Anuncio de MyPlataforma",
                "verbose_name_plural": "Anuncios de MyPlataforma",
            },
        ),
    ]
