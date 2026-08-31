from django.db import migrations, models

import count_admin_project.encrypted_fields


def encrypt_existing_links(apps, schema_editor):
    Count = apps.get_model("count", "Count")
    for item in Count.objects.exclude(link="").only("id", "link").iterator():
        item.save(update_fields=["link"])


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0002_encrypt_secrets_and_decimal_money"),
    ]

    operations = [
        migrations.AlterField(
            model_name="count",
            name="link",
            field=count_admin_project.encrypted_fields.EncryptedCharField(
                default="",
                max_length=2048,
                verbose_name="Link",
            ),
        ),
        migrations.AddField(
            model_name="sale",
            name="device_mac",
            field=models.CharField(
                blank=True,
                default="",
                max_length=17,
                verbose_name="MAC address",
            ),
        ),
        migrations.AddField(
            model_name="sale",
            name="device_key",
            field=count_admin_project.encrypted_fields.EncryptedCharField(
                blank=True,
                default="",
                max_length=512,
                verbose_name="Clave del dispositivo",
            ),
        ),
        migrations.RunPython(encrypt_existing_links, migrations.RunPython.noop),
    ]
