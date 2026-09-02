from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0010_myplataforma_permission"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="wholesaleslide",
            options={
                "ordering": ("sort_order", "-updated_at"),
                "permissions": (
                    ("manage_myplataforma", "Puede administrar MyPlataforma"),
                    (
                        "manage_wholesale_customers",
                        "Puede administrar clientes mayoristas",
                    ),
                    (
                        "manage_wholesale_slides",
                        "Puede administrar anuncios de MyPlataforma",
                    ),
                ),
                "verbose_name": "Anuncio de MyPlataforma",
                "verbose_name_plural": "Anuncios de MyPlataforma",
            },
        ),
    ]
