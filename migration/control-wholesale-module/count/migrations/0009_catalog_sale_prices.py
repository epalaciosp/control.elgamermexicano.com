from decimal import Decimal

from django.db import migrations


# Monthly public prices taken from the 2026 El Gamer MX Canva catalog.
# Products with multiple catalog variants (for example MAX Estándar/Platino)
# are intentionally excluded until their plans can be distinguished in Control.
PUBLIC_PRICES = {
    "AMAZON MUSIC": {1: "80.00"},
    "APPLE MUSIC": {1: "60.00"},
    "CALIENTE tv": {1: "80.00"},
    "CANVA PRO": {1: "50.00"},
    "CHATGPT PLUS": {1: "130.00"},
    "CRUNCHYROLL": {1: "75.00", 2: "85.00", 3: "95.00"},
    "DEZZER": {1: "60.00"},
    "DIRECTV GO": {1: "100.00", 2: "130.00", 3: "150.00"},
    "DISNEY PLUS": {1: "100.00", 2: "150.00", 3: "180.00", 4: "200.00"},
    "NETFLIX": {1: "160.00", 5: "310.00"},
    "PARAMOUNT +": {1: "50.00", 2: "60.00", 3: "70.00"},
    "PLEX": {1: "60.00", 2: "70.00", 3: "90.00", 4: "120.00"},
    "PORN HUB": {1: "80.00", 2: "90.00", 3: "100.00"},
    # Prime Video was corrected by the owner: 2 devices $75, 3 devices $85.
    "PRIME VIDEO": {1: "55.00", 2: "75.00", 3: "85.00"},
    "SPOTIFY": {1: "85.00"},
    "SPOTIFY PLUS": {1: "85.00"},
    "VIX PLUS": {1: "50.00", 2: "60.00", 3: "70.00"},
    "YOUTUBE": {1: "85.00"},
    "YOUTUBE PLUS": {1: "85.00"},
}

PLAN_PRICES = {
    ("NETFLIX", "TV VIP"): "139.00",
    ("NETFLIX", "Global"): "160.00",
    ("NETFLIX", "Premium"): "310.00",
    ("CHATGPT PLUS", "1 PERFIL"): "130.00",
}


def load_catalog_sale_prices(apps, schema_editor):
    Platform = apps.get_model("count", "Platform")
    Plan = apps.get_model("count", "Plan")
    Count = apps.get_model("count", "Count")
    Profile = apps.get_model("count", "Profile")
    Price = apps.get_model("count", "Price")

    platforms = {
        platform.name: platform
        for platform in Platform.objects.filter(name__in=PUBLIC_PRICES)
    }

    for platform_name, prices in PUBLIC_PRICES.items():
        platform = platforms.get(platform_name)
        if not platform:
            continue
        for quantity, raw_price in prices.items():
            price = Decimal(raw_price)
            existing = Price.objects.filter(
                platform_id=platform.id,
                num_profiles=quantity,
            )
            if existing.exists():
                existing.update(price=price)
            else:
                Price.objects.create(
                    platform_id=platform.id,
                    num_profiles=quantity,
                    price=price,
                )

    for (platform_name, plan_name), raw_price in PLAN_PRICES.items():
        Plan.objects.filter(
            platform__name=platform_name,
            name__iexact=plan_name,
        ).update(sale_price=Decimal(raw_price))

    plan_prices = dict(
        Plan.objects.filter(sale_price__gt=0).values_list("id", "sale_price")
    )
    for account in Count.objects.select_related("platform"):
        price = plan_prices.get(account.plan_id)
        if price is None:
            profile_count = Profile.objects.filter(count_id=account.id).count()
            raw_price = PUBLIC_PRICES.get(account.platform.name, {}).get(profile_count)
            price = Decimal(raw_price) if raw_price is not None else None
        if price is not None:
            Count.objects.filter(pk=account.pk).update(sale_price=price)


class Migration(migrations.Migration):
    dependencies = [
        ("count", "0008_wholesale_catalog_prices"),
    ]

    operations = [
        migrations.RunPython(
            load_catalog_sale_prices,
            migrations.RunPython.noop,
        ),
    ]
