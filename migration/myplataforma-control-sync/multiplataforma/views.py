from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from .decorators import usertype_in_view
from .forms import  *
from .models import *
from .libraries import *
from django.core.mail import send_mail, BadHeaderError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views import View #PARA VISTAS GENERICAS
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
import json
import secrets
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from .plex_partner import get_plex_market, plex_api_configured



PERCENT_COMISSION = 4
CONTROL_SERVICES_URL = "http://127.0.0.1:8000/count/api/wholesale/services/"
CONTROL_PORTAL_URL = "http://127.0.0.1:8000/count/api/wholesale/portal/"
CONTROL_PURCHASE_URL = "http://127.0.0.1:8000/count/api/wholesale/purchase/"
CONTROL_TOKEN_FILE = Path("/etc/wholesale-integration.token")
# if PercentCommission and PercentCommission.objects.all():
#    PERCENT_COMISSION = PercentCommission.objects.all().first().percent


def get_control_services(username):
    """Read active wholesale services from Control without storing credentials here."""
    try:
        token = CONTROL_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return [], "La integración con Control todavía no está configurada."

    request = Request(
        CONTROL_SERVICES_URL + quote(username),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "User-Agent": "MyPlataforma-ControlSync/1.0",
            "Host": "control.elgamermexicano.com",
            "X-Forwarded-Proto": "https",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return [], "Control rechazó temporalmente la consulta ({}).".format(exc.code)
    except (URLError, TimeoutError, ValueError):
        return [], "No fue posible consultar Control en este momento."

    return payload.get("services", []), None


def get_control_portal(username):
    """Read the personalized catalog, slides and dashboard metrics from Control."""
    try:
        token = CONTROL_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return {}, "La integración con Control todavía no está configurada."

    request = Request(
        CONTROL_PORTAL_URL + quote(username),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "User-Agent": "MyPlataforma-ControlPortal/1.0",
            "Host": "control.elgamermexicano.com",
            "X-Forwarded-Proto": "https",
        },
    )
    try:
        with urlopen(request, timeout=8) as response:
            return json.loads(response.read().decode("utf-8")), None
    except HTTPError as exc:
        return {}, "Control rechazó temporalmente el catálogo ({}).".format(exc.code)
    except (URLError, TimeoutError, ValueError):
        return {}, "No fue posible consultar el catálogo de Control en este momento."


def purchase_control_account(username, publication_id, reference, expected_price):
    """Purchase one complete account through Control's idempotent private API."""
    try:
        token = CONTROL_TOKEN_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return {}, "La integración con Control todavía no está configurada."

    body = json.dumps({
        "publication_id": publication_id,
        "reference": reference,
        "expected_price": str(expected_price),
    }).encode("utf-8")
    request = Request(
        CONTROL_PURCHASE_URL + quote(username),
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "MyPlataforma-ControlPurchase/1.0",
            "Host": "control.elgamermexicano.com",
            "X-Forwarded-Proto": "https",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8")), None
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            detail = payload.get("error")
        except (ValueError, UnicodeDecodeError):
            detail = None
        return {}, detail or "Control rechazó la compra ({}).".format(exc.code)
    except (URLError, TimeoutError, ValueError):
        return {}, "No fue posible completar la compra en Control. Inténtalo nuevamente."


def group_control_services_by_account(services):
    """Group profile-level Control sales into complete wholesale accounts."""
    accounts = {}

    for service in services:
        account_id = service.get("account_id")
        fallback_key = "|".join([
            str(service.get("platform") or ""),
            str(service.get("email") or service.get("access_identifier") or ""),
            str(service.get("plan") or ""),
        ])
        account_key = str(account_id) if account_id is not None else fallback_key
        days_remaining = int(service.get("days_remaining") or 0)
        sale_id = service.get("control_sale_id")
        email = service.get("email") or service.get("access_identifier") or ""
        password = service.get("password") or service.get("access_password") or ""

        if account_key not in accounts:
            accounts[account_key] = {
                "account_id": account_id,
                "dom_id": account_id or sale_id,
                "platform": service.get("platform") or "Sin plataforma",
                "plan": service.get("plan") or "Plan general",
                "email": email,
                "password": password,
                "email_password": service.get("email_password") or "",
                "link": service.get("link") or "",
                "account_capacity": int(service.get("account_capacity") or 0),
                "purchase_date": service.get("purchase_date") or "",
                "purchase_date_label": service.get("purchase_date_label") or "—",
                "expires_at": service.get("expires_at") or "",
                "expires_label": service.get("expires_label") or "—",
                "days_remaining": days_remaining,
                "profiles": [],
            }

        account = accounts[account_key]
        account["account_capacity"] = max(
            account["account_capacity"],
            int(service.get("account_capacity") or 0),
        )

        if days_remaining < account["days_remaining"]:
            account["days_remaining"] = days_remaining
            account["expires_at"] = service.get("expires_at") or ""
            account["expires_label"] = service.get("expires_label") or "—"

        profile_access = service.get("access_identifier") or ""
        profile_password = service.get("access_password") or ""
        has_individual_access = bool(
            (profile_access and profile_access != email)
            or (profile_password and profile_password != password)
        )
        account["profiles"].append({
            "control_sale_id": sale_id,
            "profile": service.get("profile") or "—",
            "pin": service.get("pin") or "—",
            "months": service.get("months") or 0,
            "access_identifier": profile_access,
            "access_password": profile_password,
            "has_individual_access": has_individual_access,
            "purchase_date_label": service.get("purchase_date_label") or "—",
            "expires_label": service.get("expires_label") or "—",
            "days_remaining": days_remaining,
        })

    def profile_order(profile):
        value = str(profile.get("profile") or "")
        return (0, int(value)) if value.isdigit() else (1, value.casefold())

    grouped_accounts = list(accounts.values())
    for account in grouped_accounts:
        account["profiles"].sort(key=profile_order)
        account["profiles_count"] = len(account["profiles"])
        account["account_capacity"] = max(
            account["account_capacity"],
            account["profiles_count"],
        )

    grouped_accounts.sort(key=lambda account: (
        account["days_remaining"],
        str(account["platform"]).casefold(),
        str(account["email"]).casefold(),
    ))
    return grouped_accounts


@login_required
def check_user_type(request):
    if request.user.is_superuser:
        return "superuser"

    group = Group.objects.filter(user=request.user).order_by("id").first()
    return group.name if group else "sin_rol"


def context_app(request):

    user_type = check_user_type(request)
    carrousel_images = ImagesCarrousel.get_carrousel_images()
    stars = money = 0
    products_actives = None
    year =  date =datetime.date.today().strftime('%Y')
    month = datetime.date.today().strftime('%m')
    if user_type == 'vendedor':
        money = request.user.get_my_money()
        products_actives = request.user.get_mys_products_actives()
    context = {
        'year': year,
        'stars':stars,
        'month':month,
        'user_type': user_type,
        'products_actives': products_actives,
        'money': money,
        'carrousel_images':carrousel_images,
    }
    return context


class PasswordResetRequest(View):

    def get(self, request):

        form = PasswordResetForm()
        return render(request, 'registration/password_reset.html', {"form": form, 'error': None})

    def post(self, request):

        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Cambio de password Mymultiplataforma"
                    email_template_name = "registration/password_reset_email.txt"
                    mail_data = {
                        "email": user.email,
                        'domain': 'myplataformadigital.com',
                        # 'domain': ' 162.240.66.189',
                        'site_name': 'mymultiplataformadigital',
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token':  default_token_generator.make_token(user),
                        # 'protocol': 'http',
                        'protocol': 'https',
                    }
                    content = render_to_string(email_template_name, mail_data)
                    try:
                        mailing = Mail()

                        mailing.send(user.email, subject, content)
                        # send_mail(subject, email, 'admin@originstv.co' , [user.email], fail_silently=False)
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                    return redirect("password_reset_done_own")
            error = "Correo electrónico inexistente en nuestro sistema"
            return render(request, 'registration/password_reset.html', {"form": form, 'error': error})

def LoginCookieView(request, action, username):

    #userdata = cookies.SimpleCookie()
    response = HttpResponse()
    if action == "remember":
        response.set_cookie("username", username)

    else:
        response.delete_cookie('username')
    return response


@login_required
def IndexView(request):
    user_type = check_user_type(request)
    date = datetime.date.today()
    if user_type not in ("superuser", "vendedor"):
        raise PermissionDenied

    wholesalers = User.objects.filter(groups__name="vendedor").distinct()
    published_catalog = SubProduct.objects.filter(active=True, for_sale=True).count()
    sales_today = CountsPackage.objects.filter(saled=True, date_sale__date=date).count()

    context = {
        "portal_role": "Administrador" if user_type == "superuser" else "Mayorista",
        "published_catalog": published_catalog,
        "sales_today": sales_today,
        "integration_ready": False,
    }

    if user_type == "superuser":
        context.update({
            "wholesalers_total": wholesalers.count(),
            "wholesalers_active": wholesalers.filter(is_active=True).count(),
            "services_total": CountsPackage.objects.filter(saled=True).count(),
        })
    else:
        my_services, integration_error = get_control_services(request.user.username)
        portal_feed, portal_error = get_control_portal(request.user.username)
        my_accounts = group_control_services_by_account(my_services)
        portal_metrics = portal_feed.get("metrics", {})
        context.update({
            "my_services_total": len(my_accounts),
            "my_profiles_total": sum(
                account["profiles_count"] for account in my_accounts
            ),
            "my_renewals": sum(
                1 for account in my_accounts if account["days_remaining"] <= 7
            ),
            "my_balance": request.user.get_my_money(),
            "published_catalog": portal_metrics.get("catalog_products", 0),
            "available_units": portal_metrics.get("available_units", 0),
            "activity_30_days": portal_metrics.get("purchases_30_days", 0),
            "activity_today": portal_metrics.get("purchases_today", 0),
            "expiring_48_hours": portal_metrics.get("expiring_48_hours", 0),
            "portal_slides": portal_feed.get("slides", []),
            "integration_ready": integration_error is None and portal_error is None,
            "integration_error": integration_error or portal_error,
        })

    return render(request, "dashboard_portal.html", context)


@login_required
def PortalSectionView(request, section):
    """Zero-state sections for the new sales-only portal.

    Inventory will be supplied by Control through the private integration.  The
    old provider inventory is intentionally not exposed here.
    """
    user_type = check_user_type(request)
    common = {
        "catalog": {
            "title": "Catálogo",
            "eyebrow": "Inventario publicado desde Control",
            "description": "Aquí aparecerán únicamente los servicios disponibles que Control autorice para mayoristas.",
            "icon": "ti-shopping-cart-full",
        },
        "support": {
            "title": "Soporte",
            "eyebrow": "Ayuda y seguimiento",
            "description": "Los reportes y solicitudes de soporte quedarán vinculados a cada servicio vendido.",
            "icon": "ti-comment",
        },
        "plex": {
            "title": "Plex",
            "eyebrow": "Integración API Partner",
            "description": "Consulta los planes Plex disponibles mediante la conexión oficial de Multiplataforma.",
            "icon": "ti-video-camera",
        },
    }
    admin_sections = {
        "orders": {
            "title": "Ventas y órdenes",
            "eyebrow": "Operación mayorista",
            "description": "Consulta de compras, asignaciones y renovaciones generadas por los mayoristas.",
            "icon": "ti-receipt",
        },
        "balances": {
            "title": "Saldos",
            "eyebrow": "Control financiero",
            "description": "Los saldos iniciaron en cero y los movimientos nuevos quedarán registrados con auditoría.",
            "icon": "ti-wallet",
        },
        "integration": {
            "title": "Integración con Control",
            "eyebrow": "Fuente única de inventario",
            "description": "Control será el único lugar para cargar cuentas, perfiles, precios y disponibilidad.",
            "icon": "ti-link",
        },
        "audit": {
            "title": "Auditoría",
            "eyebrow": "Trazabilidad del sistema",
            "description": "Cada publicación, compra, asignación y cambio de saldo conservará usuario, fecha y resultado.",
            "icon": "ti-shield",
        },
    }
    wholesaler_sections = {
        "services": {
            "title": "Mis cuentas",
            "eyebrow": "Inventario mayorista adquirido",
            "description": "Aquí estarán las cuentas completas y sus perfiles asignados a tu usuario mayorista.",
            "icon": "ti-package",
        },
        "renewals": {
            "title": "Renovaciones",
            "eyebrow": "Vigencias y renovaciones",
            "description": "Próximamente podrás solicitar y consultar renovaciones desde esta sección.",
            "icon": "ti-reload",
        },
        "purchases": {
            "title": "Compras",
            "eyebrow": "Historial de operaciones",
            "description": "Las nuevas compras realizadas desde el catálogo aparecerán aquí.",
            "icon": "ti-shopping-cart",
        },
        "balance": {
            "title": "Saldo y movimientos",
            "eyebrow": "Cuenta mayorista",
            "description": "Consulta tu saldo disponible y cada movimiento con su concepto y fecha.",
            "icon": "ti-wallet",
        },
    }

    allowed = dict(common)
    allowed.update(admin_sections if user_type == "superuser" else wholesaler_sections)
    section_data = allowed.get(section)
    if section_data is None or user_type not in ("superuser", "vendedor"):
        raise PermissionDenied

    if user_type == "vendedor" and section in ("services", "purchases"):
        services, integration_error = get_control_services(request.user.username)
        accounts = group_control_services_by_account(services)
        expiring_accounts = sum(
            1 for account in accounts if account["days_remaining"] <= 7
        )
        return render(request, "wholesale_services.html", {
            "section": section,
            "section_data": section_data,
            "accounts": accounts,
            "accounts_total": len(accounts),
            "profiles_total": sum(
                account["profiles_count"] for account in accounts
            ),
            "services": services,
            "services_total": len(services),
            "platforms_total": len({
                account.get("platform") for account in accounts
                if account.get("platform")
            }),
            "platform_names": sorted({
                account.get("platform") for account in accounts
                if account.get("platform")
            }),
            "expiring_accounts": expiring_accounts,
            "expiring_services": expiring_accounts,
            "integration_error": integration_error,
            "balance": request.user.get_my_money(),
        })

    if user_type == "vendedor" and section == "catalog":
        portal_feed, integration_error = get_control_portal(request.user.username)
        balance = Decimal(str(request.user.get_my_money() or 0))
        catalog = []
        for source_item in portal_feed.get("catalog", []):
            item = dict(source_item)
            try:
                price = Decimal(str(item.get("price", "0")))
            except (InvalidOperation, TypeError, ValueError):
                price = Decimal("0")
            whole_peso_price = price == price.to_integral_value()
            item["purchase_reference"] = secrets.token_hex(20)
            item["can_purchase"] = bool(
                whole_peso_price
                and price > 0
                and int(item.get("available_units") or 0) > 0
                and balance >= price
            )
            if not whole_peso_price:
                item["purchase_disabled_reason"] = "Precio pendiente de ajuste"
            elif price <= 0 or int(item.get("available_units") or 0) <= 0:
                item["purchase_disabled_reason"] = "Sin disponibilidad"
            elif balance < price:
                item["purchase_disabled_reason"] = "Saldo insuficiente"
            catalog.append(item)
        return render(request, "wholesale_catalog.html", {
            "section": section,
            "section_data": section_data,
            "catalog": catalog,
            "catalog_total": len(catalog),
            "available_units": portal_feed.get("metrics", {}).get("available_units", 0),
            "platform_names": sorted({item.get("platform", "") for item in catalog if item.get("platform")}),
            "integration_error": integration_error,
            "balance": balance,
        })

    if user_type == "vendedor" and section == "plex":
        plans, plex_error = get_plex_market()
        return render(request, "plex_market.html", {
            "section": section,
            "section_data": section_data,
            "plex_plans": plans,
            "plex_error": plex_error,
            "plex_configured": plex_api_configured(),
            "balance": request.user.get_my_money(),
        })

    return render(request, "portal_section.html", {
        "section": section,
        "section_data": section_data,
        "balance": request.user.get_my_money() if user_type == "vendedor" else 0,
    })


@login_required
@require_POST
def WholesaleCatalogPurchaseView(request):
    """Charge MyPlataforma balance and assign one whole Control account."""
    if check_user_type(request) != "vendedor":
        raise PermissionDenied

    publication_id = str(request.POST.get("publication_id", "")).strip()
    reference = str(request.POST.get("reference", "")).strip()
    if (
        not publication_id.isdigit()
        or not reference.isalnum()
        or not reference
        or len(reference) > 64
    ):
        messages.error(request, "La solicitud de compra no es válida.")
        return redirect("portal-section", section="catalog")

    portal_feed, integration_error = get_control_portal(request.user.username)
    if integration_error:
        messages.error(request, integration_error)
        return redirect("portal-section", section="catalog")

    item = next(
        (
            catalog_item
            for catalog_item in portal_feed.get("catalog", [])
            if str(catalog_item.get("publication_id")) == publication_id
        ),
        None,
    )
    if not item:
        messages.error(request, "Esta cuenta ya no se encuentra disponible.")
        return redirect("portal-section", section="catalog")

    try:
        price = Decimal(str(item.get("price", "0")))
    except (InvalidOperation, TypeError, ValueError):
        price = Decimal("0")
    if price <= 0 or price != price.to_integral_value():
        messages.error(request, "El precio necesita ajustarse en Control antes de comprar.")
        return redirect("portal-section", section="catalog")

    amount = int(price)
    marker = "ref:" + reference
    with transaction.atomic():
        buyer = User.objects.select_for_update().get(pk=request.user.pk)
        previous = MoneysSaler.objects.filter(
            saler=buyer,
            detail__contains=marker,
        ).order_by("-id").first()
        if previous:
            messages.info(request, "Esta compra ya había sido procesada.")
            return redirect("portal-section", section="services")

        latest_movement = MoneysSaler.objects.select_for_update().filter(
            saler=buyer,
        ).order_by("-id").first()
        current_balance = int(latest_movement.money or 0) if latest_movement else 0
        if current_balance < amount:
            messages.error(
                request,
                "Saldo insuficiente. Necesitas ${} y tienes ${}.".format(
                    amount,
                    current_balance,
                ),
            )
            return redirect("portal-section", section="catalog")

        purchase, purchase_error = purchase_control_account(
            buyer.username,
            int(publication_id),
            reference,
            price,
        )
        if purchase_error:
            messages.error(request, purchase_error)
            return redirect("portal-section", section="catalog")

        if Decimal(str(purchase.get("price", "0"))) != price:
            messages.error(request, "Control devolvió un precio diferente; no se descontó saldo.")
            return redirect("portal-section", section="catalog")

        MoneysSaler.objects.create(
            saler=buyer,
            money=current_balance - amount,
            transaction_money=amount,
            detail=(
                "Compra mayorista #{} {}".format(
                    purchase.get("purchase_id"),
                    marker,
                )
            ),
        )

    messages.success(
        request,
        "Compra completada. La cuenta ya aparece en Mis cuentas.",
    )
    return redirect("portal-section", section="services")


@login_required
def WholesalePartnersView(request):
    if check_user_type(request) != "superuser":
        raise PermissionDenied

    wholesalers = User.objects.filter(groups__name="vendedor").distinct().order_by("username")
    return render(request, "wholesale_partners.html", {"wholesalers": wholesalers})




@usertype_in_view
@login_required
def ProductCreateView(request):

    form = ProductForm(request.POST or None)
    products = Product.objects.filter(active=True)
    if request.method == 'POST':
        if form.is_valid():
            product = form.save(commit=False)
            product.save()
            return redirect('add-product')

    return render(request, 'platforms/add_product.html', {'form': form, 'products': products})



#**************************staff********************************************


def RegisterStaffView(request):

    from django.utils.crypto import get_random_string
    form = SignUpForm()
    form2 = UserDataForm()
    if request.method == 'POST':
        form = SignUpForm(request.POST or None)
        form2 = UserDataForm(request.POST, request.FILES or None)
        if form.is_valid() and form2.is_valid():
            user = form.save(commit=False)
            user.is_active = 0
            user.save()
            UserData = form2.save(commit=False)
            UserData.user = user
            token = get_random_string(length=30)
            UserData.token_register = token
            UserData.save()
            group = Group.objects.get(name=request.POST['group'])
            user.groups.add(group)
            return redirect('email-validations-register', user.username)

    return render(request, 'users/add-staff.html', {'form': form , 'form2':form2 })



def EmailValidationRegisterView(request, username):

    from django.template.loader import render_to_string
    user = User.objects.get(username=username)
    userdata = UserData.objects.get(user=user)
    if userdata.token_register != "":
        subject = "Validación de correo mymultiplataforma.com"
        email_template_name = "mail/email-verification.txt"
        mail_data = {
            "email": user.email,
            'domain': 'myplataformadigital.com',
            #'domain': ' 162.240.66.189',
            'site_name': 'mymultiplataformadigital',
            "user": user,
            'token': userdata.token_register,
            #'protocol': 'http',
            'protocol': 'https',
        }
        content = render_to_string(email_template_name, mail_data)
        try:
            mailing = Mail()
            mailing.send(user.email, subject, content)
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
    else:
        return HttpResponse('Token no existe.')
    return render(request, 'users/email-validations-register.html',{ "user":user })

def EmailVerificationView(request, token):

    try:
        userdata = UserData.objects.get(token_register=token)
        if userdata:
            user = User.objects.get(id=userdata.user_id)
            userdata.token_register = ""
            userdata.email_verified = True
            userdata.save()
        else:
            return HttpResponse('Error. token invalido.')
    except:
        return HttpResponse('Error. token invalido.')
    return render(request, 'users/email-verified.html',{ "user":user })

@usertype_in_view
@login_required
@xframe_options_exempt
def ActivateStaffView(request, type,  pk):

    user =  User.objects.filter( id = pk)
    user_data = UserData.objects.filter(user = user.first()).first()
    extention = ""
    if user_data.image_document != "":
        extention= str(user_data.image_document).split('.')[1]
    products_actives = list(user.last().get_mys_products_actives().values_list('product_id', flat=True))
    products = Product.get_all_products()
    if request.method == 'POST':
        if user.last().is_active == 0:
            user.update(is_active=1)
            ActionUser.objects.create(user=request.user, action='Activó  usuario id: ' + str(pk))
        UserProduct.objects.filter(user=user_data.user).delete()
        for product in products:
            if str(product.id) in request.POST:
                UserProduct.objects.create(user=user_data.user, product=product)
        return redirect('staff-list', type, 1)
    return render(request, 'users/activate-staff.html', { 'user':user.last(), 'user_data':user_data ,'products':products,  'type': type, 'products_actives':products_actives, 'extention':extention})


@usertype_in_view
@login_required
def StaffListView(request, type, authorized):

    users = User.objects.filter(is_active=authorized).filter(groups__name = type)
    for user in users:
        userdata = UserData.objects.get(user=user)
        user.email_verified= userdata.email_verified
    return render(request, 'users/list.html', {'users': users, 'authorized':authorized, 'type':type})


@usertype_in_view
@login_required
def CheckUsernameAjaxView(request, username):

    username = User.objects.filter(username= username)
    if username:
        return HttpResponse("exits")
    else:
        return HttpResponse("not_exist")




@usertype_in_view
@login_required
def CreateSalerView(request):

    form = SignUpForm(request.POST or None)
    form2 = UserDataForm( request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            UserData = form2.save(commit=False)
            UserData.user = user
            UserData.save()
            group = Group.objects.get(name='vendedor')
            user.groups.add(group)
            SalerStaff.objects.create(saler=user, staff=request.user)
            return redirect('saler-list')

    return render(request, 'users/add-saler.html', {'form': form , 'form2':form2 })




@usertype_in_view
@login_required
def EditSalerView(request, pk):

    user = get_object_or_404(User, pk=pk)
    form = EditUserForm(instance=user)
    user_data = UserData.objects.filter( user_id=pk).first()
    form2 = UserDataForm(instance=user_data)
    if request.method == 'POST':
        data = {'first_name': request.POST['first_name'], 'last_name': request.POST['last_name'],
                'email': request.POST['email'], 'is_active': request.POST['is_active'], 'password1': user.password,
                'password2': user.password}
        form = EditUserForm(data, instance=user)
        if form.is_valid():
                user = form.save()
                UserData = form2.save(commit=False)
                UserData.user = user
                UserData.save()
                return redirect('saler-list')

    return render(request, 'users/edit-saler.html', {'form': form , 'form2':form2 })



@usertype_in_view
@login_required
def SalerListView(request):

    salers = User.objects.filter(is_active=1).filter(groups__name = 'vendedor')
    return render(request, 'users/saler_list.html', {'salers': salers})


@usertype_in_view
@login_required
def AddMoneySalerView(request, pk):


    saler = User.objects.filter(id = pk).filter(groups__name = 'vendedor').first()
    money = saler.get_my_money()
    form = AddMoneyForm(request.POST or None, money)
    if request.method == 'POST':
        if form.is_valid():
            saler.add_money_user(money, request.POST['money'], "Recarga de saldo", request.user.username)
            return redirect('staff-list','vendedor', 1)

    return render(request, 'money/add-money-saler.html', {'form': form, 'saler': saler, 'money':money })

@usertype_in_view
@login_required
def MoneySalerListView(request):

    money_saler = MoneysSaler.Get_mys_money_saler().order_by('date')
    return render(request, 'money/moneys-list.html', {'money_saler': money_saler})


#plataformas-staff

@usertype_in_view
@login_required
def PlatformListView(request):

    user = User.objects.get(id=request.user.id)
    products_actives = user.get_mys_products_actives()

    return render(request, 'platforms/platforms-list.html', {'products_actives': products_actives})


@usertype_in_view
@login_required
def SubProductCreateView(request, id):

    form = SubProductForm(request.POST or None)
    product = Product.objects.filter(id=id).first()
    subproducts = SubProduct.objects.filter(product_id=id, creater=request.user, active=True, for_sale=True)
    if request.method == 'POST':
        if form.is_valid():
            subproduct = form.save(commit=False)
            subproduct.owner = request.user
            subproduct.creater = request.user
            subproduct.product = product
            subproduct.save()
            return redirect('add-count-package', subproduct.id)

    return render(request, 'platforms/add_subproduct.html', {'form': form, 'product': product, 'subproducts': subproducts })

@usertype_in_view
@login_required
def CommissionsPendingView(request):

    sales = CountsPackage.SalesPendingCommission(request.user)
    user_data = UserData.objects.filter(user=request.user).first()
    if request.method == 'POST':
        invoice = Invoice.objects.create(due=request.user, payment_method= request.POST['payment'])
        for item in request.POST:
            if item.isnumeric():
                is_mine = sales.filter(id=item).first()
                if is_mine:
                    is_mine.commission_collect =True
                    is_mine.save()
                    CountPackageInvoice.objects.create(invoice=invoice, count_package= is_mine)
        return redirect('commission-collect')

    return render(request, 'sales/sales_collect.html',  {'sales': sales, 'user_data':user_data })


@usertype_in_view
@login_required
def RenewCountPackageListView(request):

    request_renewal = CountsPackage.RenewPending(request.user)

    return render(request, 'platforms/renew_sales_list.html',  {'sales': request_renewal })

@usertype_in_view
@login_required
def RenewCountPackageView(request, id):

    sale = CountsPackage.objects.filter(subproduct__creater=request.user, request_renewal=True, id= id).last()
    money_to_discount = sale.subproduct.price * sale.months_renew
    money_user = sale.owner.get_my_money()
    transaction = sale.owner.subtract_money(money_user, money_to_discount, "Renovar cuenta: " + str(sale.subproduct.name) + " a " + sale.owner.username + "por " + str(sale.months_renew) + " meses")
    if transaction:
        sale.resale_count(sale.months_renew )
        sale.request_renewal = 0
        sale.save()
        return HttpResponse(f"Cuenta renovada por { sale.months_renew } meses ")
    else:
        return HttpResponse(f"El usuario {sale.owner.username} NO cuenta con el dinero para esa transacción ")


@usertype_in_view
@login_required
def DenyRenewCountPackageView(request, id):

    sale = CountsPackage.objects.filter(subproduct__creater=request.user, request_renewal=True, id= id).last()
    if sale:
        form = DenyRenewForm(request.POST or None,instance=sale)
        if request.method == 'POST':
            if form.is_valid():
                deny = form.save(commit=False)
                deny.deny_renewal = True
                deny.save()
                return redirect('renew-count-package-list')
    else:
        return redirect('index')
    return render(request, 'platforms/deny_renew_sale.html', {'form': form , "sale": sale})


@usertype_in_view
@login_required
def CommissionsPayedView(request):

    template = 'sales/invoice_payed.html'
    invoices = Invoice.objects.filter(payed=True, due= request.user )
    total = commissions = 0
    if invoices:
        for invoice in invoices:
            count_package_invoice = CountPackageInvoice.objects.filter(invoice=invoice)
            price_buy = count_package_invoice.aggregate(total_invoice=Sum('count_package__price_buy'))
            total = total + price_buy['total_invoice']
            commissions = commissions + (price_buy['total_invoice'] * (PERCENT_COMISSION * 0.01))
            invoice.total = price_buy['total_invoice']
            invoice.commission = price_buy['total_invoice'] * (PERCENT_COMISSION * 0.01)
            invoice.saler = count_package_invoice[0].count_package.owner

        return render(request, template, {'invoices': invoices, 'total':total, 'commissions':commissions })


    sales = CountsPackage.objects.filter(subproduct__creater=request.user, commission_payed=True, commission_collect=True)
    for sale in sales:
         sale_invoice =  CountPackageInvoice.objects.filter(count_package = sale).first()
         if sale_invoice:
            invoice = sale_invoice.invoice
         else:
             invoice = ""
         sale.invoice = invoice
        #sale.save()
    return render(request, 'sales/sales_payed.html',  {'sales': sales })


@usertype_in_view
@login_required
def PackageEditView(request, id):

    subproduct = SubProduct.objects.filter(creater=request.user, id=id, active=True).select_related('product').first()
    if not subproduct:
        return redirect('index')
    form = SubProductForm(request.POST or None, instance=subproduct)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            ActionUser.objects.create(user=request.user, action="Edito subproducto: " + str(request.POST['name']))
            return redirect('add-subproduct', subproduct.product_id)

    return render(request, 'platforms/edit_subproduct.html', {'form': form, 'subproduct': subproduct })


@usertype_in_view
@login_required
def AddCountToPackageView(request, id):

    subproduct = SubProduct.objects.filter(creater=request.user, id=id, active=True).select_related('product').first()
    if not subproduct:
        return redirect('index')
    form = PlanProductForm(request.POST or None)
    plans = CountsPackage.objects.filter(subproduct_id=id, owner=request.user)
    if request.method == 'POST':
        if form.is_valid():
            plan = form.save(commit=False)
            plan.subproduct = subproduct
            plan.owner = request.user
            plan.save()
            #ActionUser.objects.create(user=request.user, action="Creo plan para subproducto: " + str(subproduct.name))
            return redirect('add-count-package', id)

    return render(request, 'platforms/add_plan.html', {'form': form,'subproduct': subproduct, 'plans': plans, 'id':id })


@usertype_in_view
@login_required
def SendPackageToMarketPlaceView(request, id):

    subproduct = SubProduct.objects.filter(creater=request.user, id=id, active=True, for_sale=0).first()
    if subproduct:
        subproduct.for_sale = 1
        subproduct.save()
        return HttpResponse("Paquete enviado a la tienda")
    else:
        return HttpResponse("Hubo un error")

#************************* vendedores ***************************************

@usertype_in_view
@login_required
def MarketPlaceView(request):
    context = context_app(request)
    if context['user_type'] == "vendedor":
        #my_money = context_app(request)['money']
        products_actives = request.user.get_mys_products_actives().values_list('product_id', flat=True)
        staff_actives = User.objects.filter(groups__name = 'staff', is_active= True).values_list('id', flat=True)
        packages_list = []
        packages = SubProduct.objects.filter(active=True, creater__in=staff_actives,
                                             for_sale=True).filter(product__in=products_actives).order_by('-date')
        #packages = SubProduct.objects.filter(active=True, price__lte=my_money, creater__in = staff_actives, for_sale=True).filter(product__in= products_actives ).order_by('-date')
        for package in packages:
            counts = CountsPackage.get_all_counts_package_no_sales(package)
            if len(counts) == 0:
                continue
            stars = package.creater.get_general_stars_saler()
            packages_list.append({ 'id': package.id, 'individual_sale': package.individual_sale, 'name': package.name, 'product': package.product ,
                                   'counts': len(counts) ,'price':package.price, 'creater_id':package.creater.id, 'creater': package.creater.first_name + " "+package.creater.last_name, 'stars':stars })
    else:
        packages_list = []
        packages = SubProduct.objects.filter(active=True, for_sale=True).filter(product__active=True).order_by('-date')
        for package in packages:
            counts = CountsPackage.get_all_counts_package_no_sales(package)
            if len(counts) == 0:
                continue
            stars = package.creater.get_general_stars_saler()
            mine = False
            if package.creater == request.user:
                mine = True
            packages_list.append(
                {'id': package.id, 'name': package.name, 'product': package.product, 'counts': len(counts), 'user_type':context['user_type'],
                 'price': package.price, 'creater_id': package.creater.id, 'creater': package.creater.first_name + " " + package.creater.last_name, 'mine':mine, 'stars':stars})

    return render(request, 'platforms/market_place.html', {'packages': packages_list})

@usertype_in_view
@login_required
def MyPackageMerketPlaceView(request):

    products_actives = list(request.user.get_mys_products_actives().values_list('product_id', flat=True))
    packages = SubProduct.objects.filter(active=True, creater=request.user,
                                         for_sale=True).filter(product_id__in=products_actives).order_by('-date')
    return render(request, 'platforms/packages_all_actives_list.html', {'packages': packages})



@usertype_in_view
@login_required
def SalePlatformsView(request, name):

    print(name)
    product = Product.objects.filter(name=name, active=True).first()
    my_subproducts = request.user.get_my_buy_subproducts_actives_by_product(product)
    print(my_subproducts)
    data = []
    for subproduct in my_subproducts:
        packages = CountsPackage.get_mys_counts_package_no_sales(subproduct, request.user)
        if packages:
            count_packages = len(packages)
            plan_saler_product = {'id': subproduct.id, 'name': subproduct.name, 'price_unity': packages.first().price_buy,  "coun_packages": count_packages, "product_name": subproduct.product.name}
            data.append(plan_saler_product)

    return render(request, 'platforms/packages_to_sale.html', {'packages': data,'product':product})


@usertype_in_view
@login_required
def BuyPackageView(request, id):

    subproduct = SubProduct.objects.filter(id=id, active=True).select_related('product').first()
    counts = CountsPackage.objects.filter(subproduct_id=subproduct.id, owner = subproduct.creater)
    if subproduct and len(counts) > 0:
        money_user = request.user.get_my_money()
        if money_user:
            if subproduct.price > money_user:
                return HttpResponse("No tienes suficiente saldo para esta transacción")
            else:
                date_finish = datetime.datetime.now() + datetime.timedelta(days=30)
                if subproduct.individual_sale:
                    count = counts.last()
                    count.owner = request.user
                    count.date_finish = date_finish
                    count.price_buy = subproduct.price
                    count.commission = int(subproduct.price ) * (PERCENT_COMISSION * 0.01)
                    count.date_buy = datetime.datetime.now()
                    count.save()
                else:
                    subproduct.for_sale = False
                    subproduct.save()
                    len_counts = len(CountsPackage.objects.filter(subproduct_id=subproduct.id))
                    individual_price = subproduct.price/len_counts
                    commission = int(individual_price) * (PERCENT_COMISSION * 0.01)
                    counts.update(owner=request.user, date_finish=date_finish, date_buy =datetime.datetime.now(),price_buy = individual_price, commission=commission)
                    count = None
                request.user.subtract_money(money_user, subproduct.price , "Compra: " + str(subproduct.name) + " a " + subproduct.creater.username)
                if subproduct.individual_sale:
                    return HttpResponse("Cuenta adquirida, ahora esta aparecerá en su inventario")
                    #return redirect('platforms', subproduct.name)
                    #return render(request, 'platforms/sale_plan.html',  { 'subproduct': subproduct, 'count':count })
                else:
                    return HttpResponse("Paquete adquirido, todo el paquete aparecerá a su nombre")

        return HttpResponse("No tienes suficiente saldo para esta transacción")
    else:
        return HttpResponse("Este plan no está disponible en este momento")

@usertype_in_view
@login_required
def SaleCountView(request, id):

    subproduct = SubProduct.objects.filter(id=id, active=True).first()
    last_count_package = CountsPackage.get_mys_counts_package_no_sales(subproduct, request.user).last()
    print(last_count_package.id)
    if request.method == 'POST':
        last_count_package.sale_count(request.POST['months'])
        return redirect('platforms', subproduct.product.name)
    return render(request, 'sales/sale_count_box.html',{ 'id':id, 'subproduct':subproduct, 'count':last_count_package})


@usertype_in_view
@login_required
def ResaleCountView(request, id):

    count_package = CountsPackage.objects.filter(id=id, owner=request.user).last()
    if not count_package.subproduct.renewable:
        return redirect('buys-inter-dates')
    money_user = request.user.get_my_money()

    if request.method == 'POST':
        count_package.request_renewal=True
        count_package.months_renew = int(request.POST['months'])
        count_package.save()
        #money_to_discount = float(count_package.subproduct.price) * int(request.POST['months'])
        #transaction = request.user.subtract_money(money_user, money_to_discount, "Renovar cuenta: " + str(count_package.subproduct.name) + " a " + count_package.subproduct.creater.username + "por " + request.POST['months'] + " meses")
        #if transaction:
        #    count_package.resale_count(request.POST['months'])
        return redirect('buys-inter-dates')
    return render(request, 'sales/resale_count_box.html',{ 'id':id, 'count':count_package, 'money_user':money_user})

@usertype_in_view
@login_required
def SalesMonthPlatformsView(request, year=None, month= None):

    context = context_app(request)
    if context['user_type'] == "staff":
        template = 'sales/sales_no_layout.html'
        sales_sum = comission = 0
        sales =  CountsPackage.SalesByStaffbyDate(request.user, year, month)
        if sales:
            sales_sum = sales.aggregate(total_sales=Sum('price_buy'))
            comission = int(sales_sum['total_sales']) * (PERCENT_COMISSION*0.01)
            return render(request, template, {'sales': sales, 'sales_sum': sales_sum, 'comission': comission, 'PERCENT_COMISSION':PERCENT_COMISSION})

    elif context['user_type'] == "superuser":
        template = 'sales/sales_staff.html'
        invoices = Invoice.InvoicesbyDatePay( year, month)
        total = commissions = 0
        if invoices:
            for invoice in invoices:
                count_package_invoice = CountPackageInvoice.objects.filter(invoice=invoice)
                price_buy = count_package_invoice.aggregate(total_invoice=Sum('count_package__price_buy'))
                total = total + price_buy['total_invoice']
                commissions = commissions + (price_buy['total_invoice'] * (PERCENT_COMISSION * 0.01))
                invoice.total = price_buy['total_invoice']
                invoice.commission = price_buy['total_invoice'] * (PERCENT_COMISSION * 0.01)
                invoice.saler = count_package_invoice[0].count_package.owner
            return render(request, template, {'invoices': invoices, 'total':total, 'commissions':commissions  })

    elif context['user_type'] == "vendedor":
        template = 'sales/sales_saler.html'
        sales = CountsPackage.all_counts_saled_in_dates(year, month, request)
        sales_sum =  0
        if sales:
            sales_sum = sales.aggregate(total_sales=Sum('price_sale'))
            buy_sum = sales.aggregate(total_buy=Sum('price_buy'))
            return render(request, template, {'sales': sales, 'sales_sum': sales_sum, 'buy_sum':buy_sum })

    return render(request, template)


@usertype_in_view
@login_required
def SeeSalePlatformsView(request, id):

    context = context_app(request)

    if context['user_type'] == "staff":
        count_package_invoices = CountPackageInvoice.objects.filter(invoice_id=id).filter(invoice__due=request.user)
    else:
        count_package_invoices = CountPackageInvoice.objects.filter(invoice_id=id)
    total_value = count_package_invoices.aggregate(total_invoice=Sum('count_package__price_buy'))

    return render(request, "sales/see_sale.html", {'count_package_invoices': count_package_invoices, 'total_value':total_value['total_invoice'] })


@usertype_in_view
@login_required
def GeneralSalesView(request):

    context = context_app(request)
    if context['user_type'] == "staff":
        mys_general_sales = request.user.get_my_general_sales()
        sales_sum = comission = 0
        if mys_general_sales:
            sales_sum = mys_general_sales.aggregate(total_sales=Sum('price_buy'))
            comission = int(sales_sum['total_sales']) * (PERCENT_COMISSION * 0.01)

        return render(request, 'sales/sales_generals.html', {'sales': mys_general_sales, 'sales_sum': sales_sum, 'comission': comission})

    elif context['user_type'] == "vendedor":

        sales = CountsPackage.objects.filter(saled=1).filter(owner = request.user)
        sales_sum = 0
        if sales:
            sales_sum = sales.aggregate(total_sales=Sum('price_sale'))
            total_buy = sales.aggregate(total_buy=Sum('price_buy'))
            #total_win =  float(sales_sum['total_sales'])-float(total_buy['total_buy'])
            buy_sum = sales.aggregate(total_buy=Sum('price_buy'))
        return render(request, 'sales/sales_saler.html', {'sales': sales, 'sales_sum': sales_sum,  'buy_sum':buy_sum })



@usertype_in_view
@login_required
def InterDatesSalesView(request):

    #context = context_app(request)
    form = GetInterDatesForm()
    return render(request, 'sales/inter-dates.html', {'form': form })


@usertype_in_view
@login_required
def BuysInterDatesView(request):

    form = GetInterDatesForm()
    return render(request, 'users/inter-dates.html', {'form': form })


@usertype_in_view
@login_required
def BuysMonthView(request, year=None, month= None):

    context = context_app(request)
    if context['user_type'] == "vendedor":
        buys = CountsPackage.all_counts_buy_in_dates(request.user, year, month)
        return render(request, 'users/buys_month.html', {'buys': buys })



@usertype_in_view
@login_required
def UserCommissionPendingView(request):

    users = Invoice.UserPendingInvoices()
    return render(request, 'users/pending-pays.html',  {'users': users })


@usertype_in_view
@login_required
def CommissionPendingView(request, username):

    user = User.objects.filter(username=username).first()
    invoices = user.get_mys_invoices_pendding()
    return render(request, 'sales/invoices_pendding.html', {
        'invoices': invoices, 'user':user } )
@csrf_exempt
@usertype_in_view
@login_required
def PayInvoicePenddingView(request, id):

    count_package_invoice = CountPackageInvoice.objects.filter(invoice=id).values_list('count_package_id', flat=True)
    print(count_package_invoice)
    print(count_package_invoice)
    sales = CountsPackage.objects.filter(id__in=count_package_invoice)
    print(sales)
    invoice = Invoice.objects.filter(id=id, payed=False).first()
    if not invoice:
        return redirect('sales-inter-dates')
    user_data = UserData.objects.filter(user=invoice.due).first()
    sales_sum = sales.aggregate(total_sales=Sum('price_buy'))
    print(sales_sum['total_sales'])
    print(type(sales_sum['total_sales']))
    comission = sales_sum['total_sales'] * PERCENT_COMISSION*0.01
    pay_in = eval("user_data."+ str(invoice.payment_method.lower()))
    pay = int(sales_sum['total_sales']) - comission
    if request.method == 'POST':
        try:
            invoice.payed=True
            invoice.date_pay = datetime.datetime.now()
            invoice.save()
            for sale in sales:
                sale.SetPayStaffSale()
            return HttpResponse("Pago registrado satisfactroriamente")
        except:
            return HttpResponse("Hubo un error al efectuar el pago")

    else:
        return render(request, 'sales/sales_comission_pending.html', {
            'invoice': invoice, 'user_data': user_data, 'sales': sales,
            'sales_sum': sales_sum, 'comission': comission, 'pay': pay
        })


@usertype_in_view
@login_required
def PayStaffSaleView(request, id):

    user = User.objects.filter(username=username).first()
    sales = CountsPackage.SalesPendingCommissionByPayment(user, payment)
    sales_sum = comission = 0
    if sales:
        sales_sum = sales.aggregate(total_sales=Sum('price_buy'))
        comission = int(sales_sum['total_sales']) * (PERCENT_COMISSION * 0.01)
        pay = int(sales_sum['total_sales']) - comission
        for sale in sales:
            sale.SetPayStaffSale()
        return render(request, 'platforms/pay_staff_sale.html',  {'user': user, 'user_data':user_data, 'pay': pay})
    else:

        return HttpResponse("Este pago ya fue generado anteriormente o no existe")


@usertype_in_view
@login_required
def ReportIssuePlatformView(request,  id):

    sale = CountsPackage.objects.filter(id=id).first()
    if sale.owner == request.user:
        form = ReportIssueForm(request.POST or None, request.FILES or None)
        if request.method == 'POST':
            print(request.POST)
            print(request.FILES)
            if form.is_valid():
                report = form.save(commit=False)
                report.user = request.user
                report.count = sale
                report.is_active = 1
                report.save()
                return redirect('reported-issues-platform')
        return render(request, 'reports/plataform.html', {"form": form, 'sale': sale})
    else:
        return redirect('index')


@usertype_in_view
@login_required
def QualifySalerListView(request):

   my_salers = request.user.get_my_salers()
   salers=[]
   for my_saler in my_salers:
       user_data = UserData.objects.filter(user = my_saler).first()
       stars = my_saler.get_stars_saler(request.user)
       salers.append({'id': my_saler.id, 'image':user_data.image.url, 'first_name':my_saler.first_name ,'last_name':my_saler.last_name, 'stars': stars})
   return render(request, 'users/qualify-saler-list.html', {'my_salers': salers })

@usertype_in_view
@login_required
def QualifySalerView(request, id, stars):

   saler_starts = UserStart.objects.filter(buyer=request.user, saler_id=id).first()
   if saler_starts:
       saler_starts.stars = stars
       saler_starts.save()
   else:
       UserStart.objects.create(buyer=request.user, saler_id=id, stars=stars)
   return HttpResponse("Tu calificación fue registrada")


@login_required
def ReportedIssuesView(request):

    context = context_app(request)
    if context['user_type']== "superuser":
        #reports = IssuesReport.objects.filter(state=0).order_by('state')
        reports = IssuesReport.objects.all().order_by('state')
    elif context['user_type']== "staff":
        reports = IssuesReport.get_reports_of_mys_counts_created(request.user)
    elif context['user_type'] == "vendedor":
        reports = IssuesReport.objects.filter(user=request.user).order_by('state')
    return render(request, 'reports/list.html', {"reports": reports })

@usertype_in_view
@login_required
def ReportedIssue(request, id):

    context = context_app(request)
    if context['user_type'] == "superuser" or context['user_type'] == "staff":
        report = get_object_or_404(IssuesReport, pk=id)
        form = ReportForm(instance=report)
        if request.method == 'POST':
            state = False
            if 'state' in request.POST and request.POST['state'] == "on":
                state = True
            IssuesReport.objects.filter(id=id).update(state=state, response=request.POST['response'])
            return redirect('reported-issues-platform')

    else:
        return redirect('reported-issues-platform')

    return render(request, 'reports/edit.html', {"report": report, "form": form})


#delete
@usertype_in_view
@login_required
def DeleteRegister(request, model, id):

    user_type = check_user_type(request)
    if user_type == "superuser":
        models = ["User", "Product","DeleteUser"]
    elif user_type == "staff":
        models = ["User", "CountsPackage", "SubProduct", "renew"]
    elif user_type == "vendedor" :
        models = ['IssuesReport']
    else:
        return redirect('index')
    if model in models:
        try:
            if model == "User":
                if user_type == "staff":
                    is_my_saler = SalerStaff.Is_my_saler(request.user.id, id)
                    if not is_my_saler:
                        return redirect('index')

                eval(model + ".objects.filter(id=" + id + ").update(is_active=0)")
                action = "Borrado de " + model + " con id: " + str(id)
                message = "Desactivado satisfactorio"

            elif model == "DeleteUser":
                if user_type == "staff":
                    is_my_saler = SalerStaff.Is_my_saler(request.user.id, id)
                    if not is_my_saler:
                        return redirect('index')
                user =  User.objects.get(id=id)
                UserData.objects.get(user= user).delete()
                user.delete()
                action = "ELiminacion total de " + model + " con id: " + str(id)
                message = "Eliminación total satisfactoria"
            else:
                if model == "SubProduct" or model == "Product":
                    exist_id = eval(model + ".objects.filter(id=" + id + ").first() ")
                elif model == "CountsPackage" or model == "renew":
                    exist_id = CountsPackage.objects.filter(id= id).select_related('subproduct').first()
                    if model == "renew":
                        exist_id.request_renewal = 0
                        exist_id.save()
                        return  HttpResponse("Desactivado satisfactorio")
                    if exist_id.subproduct.creater != request.user:
                        exist_id = None
                elif model == "PlanPlatformSales":
                    exist_id = eval(model + ".objects.filter(id=" + id + ", saler_id=request.user.id)")
                else:
                    exist_id = eval( model + ".objects.filter(id=" + id + ", user_id=" + str(request.user.id) + ").first() ")
                if exist_id is None:
                    action = "Intento de borrado de " + model + " con id: " + str(id)
                    message = "No tienes acceso, esta acción será reportada"
                if model == "CountsPackage" or model=="IssuesReport" :
                    eval(model + ".objects.filter(id=" + id + ").delete()")
                else:
                    eval(model + ".objects.filter(id=" + id + ").update(active=0)")
                action = "Borrado de " + model + " con id " + str(id)
                message = "Desactivado satisfactorio"
        except ValueError:
            return HttpResponse(ValueError)
    else:
        action = "Intento de borrado de " + model + " con id: " + str(id)
        return HttpResponse("No tienes acceso, esta acción será reportada")
    ActionUser.objects.create(user=request.user, action=action)
    return HttpResponse(message)
