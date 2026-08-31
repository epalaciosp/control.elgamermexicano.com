import json
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.utils.dateparse import parse_datetime

from multiplataforma.models import (
    ActionUser,
    Country,
    CountsPackage,
    ImagesCarrousel,
    Invoice,
    MoneysSaler,
    PercentCommission,
    Product,
    SubProduct,
    UserData,
)


BACKUP_DIR = Path("/root/myplataformadigital-clean-reset-20260831")


def load_fixture(name):
    return json.loads((BACKUP_DIR / name).read_text(encoding="utf-8"))


def datetime_or_none(value):
    return parse_datetime(value) if value else None


def create_user(fields, *, force_superuser=False):
    username = fields["username"]
    user = User(
        username=username,
        password=fields["password"],
        first_name=fields.get("first_name", ""),
        last_name=fields.get("last_name", ""),
        email=fields.get("email", ""),
        is_active=True,
        is_staff=force_superuser,
        is_superuser=force_superuser,
        last_login=datetime_or_none(fields.get("last_login")),
        date_joined=datetime_or_none(fields.get("date_joined")),
    )
    user.save(force_insert=True)
    return user


control_admin_fixture = load_fixture("epalacios10-control-user.json")
if len(control_admin_fixture) != 1:
    raise RuntimeError("No se encontró una identidad única para epalacios10 en Control.")

admin_fields = control_admin_fixture[0]["fields"]
admin_fields["username"] = "epalacios10"
admin = create_user(admin_fields, force_superuser=True)

legacy_users_fixture = load_fixture("retained-myplatform-users.json")
legacy_profiles_fixture = load_fixture("retained-myplatform-profiles.json")
countries_fixture = load_fixture("retained-countries.json")

expected_majoristas = {"Yehoshua", "arojas7"}
fixture_usernames = {item["fields"]["username"] for item in legacy_users_fixture}
if fixture_usernames != expected_majoristas:
    raise RuntimeError(
        f"Los usuarios a conservar no coinciden: {sorted(fixture_usernames)}"
    )

old_pk_to_username = {
    item["pk"]: item["fields"]["username"] for item in legacy_users_fixture
}
users_by_username = {admin.username: admin}
for item in legacy_users_fixture:
    user = create_user(item["fields"], force_superuser=False)
    users_by_username[user.username] = user

# Se conserva temporalmente el nombre técnico que entiende el portal anterior.
# La interfaz y la integración nueva lo presentarán como "Mayorista".
legacy_seller_group, _ = Group.objects.get_or_create(name="vendedor")
for username in expected_majoristas:
    users_by_username[username].groups.add(legacy_seller_group)

for item in countries_fixture:
    fields = item["fields"]
    Country.objects.update_or_create(
        pk=item["pk"],
        defaults={"country": fields["country"], "iso": fields["iso"]},
    )

for item in legacy_profiles_fixture:
    fields = dict(item["fields"])
    old_user_pk = fields.pop("user")
    country_pk = fields.pop("country")
    username = old_pk_to_username.get(old_user_pk)
    if username not in expected_majoristas:
        raise RuntimeError(f"Perfil inesperado para el usuario anterior {old_user_pk}.")
    UserData.objects.create(
        user=users_by_username[username],
        country=Country.objects.get(pk=country_pk),
        **fields,
    )

# El nuevo canal inicia sin saldos, inventario, ventas ni comisiones anteriores.
assert User.objects.count() == 3
assert set(User.objects.values_list("username", flat=True)) == {
    "epalacios10",
    "Yehoshua",
    "arojas7",
}
assert UserData.objects.count() == 2
assert MoneysSaler.objects.count() == 0
assert Product.objects.count() == 0
assert SubProduct.objects.count() == 0
assert CountsPackage.objects.count() == 0
assert Invoice.objects.count() == 0
assert PercentCommission.objects.count() == 0
assert ImagesCarrousel.objects.count() == 0
assert ActionUser.objects.count() == 0

print(
    "Portal limpio creado:",
    {
        "usuarios": list(User.objects.order_by("username").values_list("username", flat=True)),
        "perfiles_mayoristas": UserData.objects.count(),
        "saldo_movimientos": MoneysSaler.objects.count(),
        "inventario_anterior": CountsPackage.objects.count(),
    },
)
