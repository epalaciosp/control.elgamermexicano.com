from django.shortcuts import render, redirect, get_object_or_404
from django.views import View  # PARA VISTAS GENERICAS
from django.utils.decorators import method_decorator
from django.utils import timezone as django_timezone
from django.contrib.auth.decorators import login_required
from .decorators import permissions_in_view, my_permissions
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from .forms import *
from .models import (
    Profile,
    Count,
    Platform,
    Plan,
    Country,
    Promotion,
    PromotionPlatform,
    Price,
    Bill,
    Sale,
    PromotionSale,
    WholesalePartner,
    WholesalePublication,
    WholesalePurchase,
    WholesaleSlide,
    PartnerMediaPrice,
)
from .partner_media import get_partner_media_markets, partner_api_configured
from user.models import Customer, Action
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
from .libraries import (
    getDifference,
    is_chatgpt_plus_platform,
    is_plus_code_platform,
    normalize_ibo_device_identifier,
)
import datetime, json
import logging
import secrets
from decimal import Decimal, InvalidOperation
from pathlib import Path
from django.contrib import messages
from count.libraries import CalculateDateLimit
from user.whatsapp_api import (
    WHATSAPP_SEND_ERROR,
    message_sale,
    message_plan_sale,
    message_renew,
    message_expired,
    message_plan_VIP,
)
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UserPassesTestMixin,
)
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Q, Count as Count_, Sum, Exists, OuterRef
from django.db import transaction
from django.urls import reverse_lazy
from django.http import Http404
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

#class GetValidSalesView(View):
#    def get(self, request, customer_id):
#        # Filtramos las cuentas asociadas al cliente con id = customer_id
#        counts = Count.objects.filter(platform__customer_id=customer_id)
#	#counts = Sale.objects.filter(bill__customer__id=customer_id, date_limit__gte=timezone.now(), renovated=False)
#
#        # Creamos una lista de diccionarios con los correos de las cuentas
#        emails_data = []
#        for count in counts:
#            emails_data.append({
#                "email": count.email,  # Obtenemos el correo de la cuenta asociada
#                #"link": count.link,  # Puedes agregar otros campos si es necesario
#                #"date_limit": count.date_limit,  # Fecha de vencimiento de la cuenta
#            })
#
#        # Devolvemos la respuesta en formato JSON
#        return JsonResponse({"customer_emails": emails_data}, safe=False)

@method_decorator(login_required, name='dispatch')
class GetValidSalesView(View):
    def get(self, request, customer_id):
        # Filtramos las ventas cuyo customer_id en la factura coincida y que no estén vencidas
        sales = Sale.objects.filter(bill__customer_id=customer_id, date_limit__gte=django_timezone.now())

        # Creamos una lista de diccionarios con los correos de las cuentas asociadas a cada venta
        emails_data = []
        for sale in sales:
            # Obtenemos el profile_id de la venta
            profile = sale.profile
            # Usamos el profile_id para obtener el Count asociado
            count = Count.objects.filter(profile=profile).first()
            if count:
                emails_data.append({
                    "email": count.email,  # Obtenemos el correo de la cuenta asociada
                    # Si necesitas más datos, puedes agregarlos aquí
                    #"link": count.link,  # Por ejemplo, el link de la cuenta
                    #"date_limit": sale.date_limit,  # Si quieres incluir la fecha de la venta
                })

        # Devolvemos la respuesta en formato JSON
        return JsonResponse({"valid_sales_emails": emails_data}, safe=False)

@method_decorator(login_required, name='dispatch')
class DashboardView(View):

    def get(self, request, *args, **kwargs):
        now = django_timezone.now()
        today = django_timezone.localdate()
        current_timezone = django_timezone.get_current_timezone()
        day_start = django_timezone.make_aware(
            datetime.datetime.combine(today, datetime.time.min),
            current_timezone,
        )
        tomorrow_start = day_start + datetime.timedelta(days=1)
        month_start = day_start.replace(day=1)
        if month_start.month == 12:
            next_month_start = month_start.replace(
                year=month_start.year + 1,
                month=1,
            )
        else:
            next_month_start = month_start.replace(month=month_start.month + 1)
        next_week = now + datetime.timedelta(days=7)

        wholesale_customer_ids = WholesalePartner.objects.values("customer_id")
        active_sales = Sale.objects.filter(
            renovated=False,
            cutted=False,
            date_limit__gte=now,
        ).exclude(bill__customer_id__in=wholesale_customer_ids)
        active_customer_count = active_sales.values(
            "bill__customer_id"
        ).distinct().count()
        total_customers = Customer.objects.exclude(
            id__in=wholesale_customer_ids,
        ).count()

        month_bills = Bill.objects.filter(
            date__gte=month_start,
            date__lt=next_month_start,
            sale__isnull=False,
        ).distinct()
        today_bills = Bill.objects.filter(
            date__gte=day_start,
            date__lt=tomorrow_start,
            sale__isnull=False,
        ).distinct()

        active_accounts = Count.objects.filter(date_limit__gte=now).count()
        total_accounts = Count.objects.count()
        upcoming_sales = active_sales.filter(date_limit__lt=next_week)

        platform_activity = list(
            active_sales.values("profile__count__platform__name")
            .annotate(total=Count_("id"))
            .order_by("-total", "profile__count__platform__name")[:6]
        )
        max_platform_sales = max(
            (item["total"] for item in platform_activity),
            default=0,
        )
        for item in platform_activity:
            item["percentage"] = round(
                (item["total"] / max_platform_sales) * 100
            ) if max_platform_sales else 0

        context = {
            "total_customers": total_customers,
            "active_customers": active_customer_count,
            "inactive_customers": max(total_customers - active_customer_count, 0),
            "sales_today": today_bills.count(),
            "sales_month": month_bills.count(),
            "revenue_month": month_bills.aggregate(total=Sum("total"))["total"] or 0,
            "active_accounts": active_accounts,
            "inactive_accounts": max(total_accounts - active_accounts, 0),
            "active_services": active_sales.count(),
            "customers_expiring": upcoming_sales.values(
                "bill__customer_id"
            ).distinct().count(),
            "expired_services": Sale.objects.filter(
                renovated=False,
                cutted=False,
                date_limit__lt=now,
            ).count(),
            "available_profiles": Profile.objects.filter(
                saled=False,
                count__date_limit__gte=now,
            ).count(),
            "accounts_expiring": Count.objects.filter(
                date_limit__gte=now,
                date_limit__lt=next_week,
            ).count(),
            "upcoming_sales": upcoming_sales.select_related(
                "bill__customer",
                "profile__count__platform",
            ).order_by("date_limit")[:8],
            "platform_activity": platform_activity,
            "dashboard_updated_at": django_timezone.localtime(now),
        }
        return render(request, "dashboard.html", context)



@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CreatePlan(View):

    template_name = "plan/create.html"
    form_class = PlanForm

    def dispatch(self, request, *args, **kwargs):

        platform = Platform.objects.filter(name=kwargs.get('platform')).first()
        if platform :
            self.platform = platform
        else:
            raise Http404("La plataforma no existe")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, platform, *args, **kwargs):


        if self.platform:
            form = self.form_class(self.platform)
            return render(request, self.template_name, {'form': form, 'platform': self.platform})
        else:
            return redirect("platform-list")

    def post(self, request, *args, **kwargs):
        form = self.form_class(self.platform, request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.platform = self.platform
            plan.save()
            return redirect('update-platform', self.platform.id)
        return render(request, self.template_name, {'form': form, 'platform': self.platform})

@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UpdatePlanView(UpdateView):

    model = Plan
    fields = [
        "name",
        "num_profiles",
        "sale_price",
        "wholesale_price",
        "active",
        "have_link",
        "description",
    ]
    template_name = "plan/update.html"


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.object
        context['platform_name'] = plan.platform.name
        return context

    def get_success_url(self):

        plan = self.get_object()
        success_url = "/count/plan/list/list/"+plan.platform.name
        return success_url

@method_decorator(login_required, name='dispatch')
class PlanListView(ListView):

    model = Plan

    def get_queryset(self):

        plans = self.model.objects.filter(platform__name=self.kwargs['platform'], active=True)
        return plans

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['platform_name'] = self.kwargs['platform']
        return context

    def get_template_names(self):

        template_name = self.kwargs.get('template_name')
        if template_name:
            return [f'plan/{template_name}.html']
        else:
            raise Http404("Template no encontrado")







@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CreateCount(View):

    template_name = "count/create.html"
    form_class = CountForm

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name, {'form': self.form_class})

    def post(self, request, *args, **kwargs):

        plan_id = request.POST['plan'] if 'plan' in request.POST else None
        platform = Platform.objects.filter(id=request.POST['platform']).first()
        if not platform:
            return HttpResponse("La plataforma no existe", status=400)
        is_ibo_player = (
            platform.name.strip().casefold() == "iptv ibo pro player"
        )
        is_plus_code = is_plus_code_platform(platform.name)
        try:
            sale_price = Decimal(request.POST.get("sale_price") or "0")
            profile_sale_price = Decimal(
                request.POST.get("profile_sale_price") or "0"
            )
            wholesale_price = Decimal(request.POST.get("wholesale_price") or "0")
        except InvalidOperation:
            return HttpResponse("Los precios no son válidos.", status=400)
        if sale_price < 0 or profile_sale_price < 0 or wholesale_price < 0:
            return HttpResponse("Los precios no pueden ser negativos.", status=400)
        if is_plus_code:
            plus_code = request.POST.get("password", "").strip()
            expiration = request.POST.get("date_limit", "").strip()
            if not plus_code or not expiration:
                return HttpResponse(
                    "Ingresa el Código Plus y su vencimiento.",
                    status=400,
                )
            if any(
                existing.password == plus_code
                for existing in Count.objects.filter(platform=platform).only("password")
            ):
                return HttpResponse(
                    "Este Código Plus ya está registrado.",
                    status=409,
                )
            country = (
                Country.objects.filter(country__iexact="México").first()
                or Country.objects.first()
            )
            new_count = Count.objects.create(
                platform=platform,
                email="Código Plus",
                country=country,
                password=plus_code,
                email_password="",
                link="",
                date_limit=expiration,
                sale_price=sale_price,
                profile_sale_price=profile_sale_price,
                wholesale_price=wholesale_price,
            )
            new_count.email = "Código Plus #" + str(new_count.id)
            new_count.save(update_fields=["email"])
            Profile.objects.create(
                count=new_count,
                profile="Código",
                pin="0",
                saled=False,
            )
            return redirect("count-list")

        if is_chatgpt_plus_platform(platform.name):
            email = request.POST.get("email", "").strip()
            expiration = request.POST.get("date_limit", "").strip()
            plan = Plan.objects.filter(
                id=plan_id,
                platform=platform,
                num_profiles=6,
                active=True,
            ).first()
            if not email or not expiration or not plan:
                return HttpResponse(
                    "Selecciona Cuenta completa 6 perfiles e ingresa correo y vencimiento.",
                    status=400,
                )
            if Count.objects.filter(
                platform=platform,
                email__iexact=email,
            ).exists():
                return HttpResponse(
                    "Este correo de ChatGPT Plus ya está registrado.",
                    status=409,
                )
            country = (
                Country.objects.filter(country__iexact="México").first()
                or Country.objects.first()
            )
            new_count = Count.objects.create(
                platform=platform,
                plan=plan,
                email=email,
                country=country,
                password="",
                email_password="",
                link="",
                date_limit=expiration,
                sale_price=sale_price,
                profile_sale_price=profile_sale_price,
                wholesale_price=wholesale_price,
            )
            for profile_number in range(1, 7):
                Profile.objects.create(
                    count=new_count,
                    profile=str(profile_number),
                    pin="0",
                    saled=False,
                )
            return redirect("count-list")

        if is_ibo_player:
            plan = Plan.objects.filter(id=plan_id, platform=platform, num_profiles=4).first()
            playlist = request.POST.get('link', '').strip()
            if not plan or not playlist:
                return HttpResponse(
                    "Selecciona el plan de 4 perfiles e ingresa la lista de reproducción.",
                    status=400,
                )
            country = Country.objects.filter(country__iexact="México").first() or Country.objects.first()
            new_count = Count.objects.create(
                platform=platform,
                plan=plan,
                email="Lista IBO",
                country=country,
                link=playlist,
                password="",
                email_password="",
                date_limit=request.POST['date_limit'],
                sale_price=sale_price,
                profile_sale_price=profile_sale_price,
                wholesale_price=wholesale_price,
            )
            new_count.email = "Lista IBO #" + str(new_count.id)
            new_count.save(update_fields=["email"])
            for profile_number in range(1, 5):
                Profile.objects.create(
                    count=new_count,
                    profile=str(profile_number),
                    pin="0",
                    saled=False,
                )
            return redirect("count-list")

        new_count = Count.objects.create(platform_id = request.POST['platform'],
                                         plan_id = plan_id,
                                         email = request.POST['email'],
                                         country_id=request.POST['country'],
                                         link=request.POST['link'] if 'link' in request.POST else "",
                                         password = request.POST['password'],
                                         email_password="" if is_ibo_player else request.POST['email_password'],
                                         date_limit = request.POST['date_limit'],
                                         sale_price=sale_price,
                                         profile_sale_price=profile_sale_price,
                                         wholesale_price=wholesale_price,
                                         )

        for item in request.POST:
            if item.isnumeric():
                if "profile" in request.POST:
                    Profile.objects.create(count=new_count, profile=request.POST["profile" ], pin=request.POST[item], saled=0)
                else:
                    Profile.objects.create(count=new_count, profile = item, pin=request.POST[item], saled=0)
        return redirect("count-list")



@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UpdateCount(UpdateView):

    template_name = "count/update.html"
    form_class = CountUpdateForm

    def get(self, request, id, *args, **kwargs):
        is_tv_vip = False
        is_ibo_player = False
        is_plus_code = False
        is_chatgpt_plus = False
        count= Count.objects.filter(id=id).first()
        if is_plus_code_platform(count.platform.name):
            is_plus_code = True
        if count.platform.name.strip().casefold() == "iptv ibo pro player":
            is_ibo_player = True
        if is_chatgpt_plus_platform(count.platform.name):
            is_chatgpt_plus = True
        if count.plan:
            if count.plan.name ==  "TV VIP":
                is_tv_vip = True
        profiles= Profile.objects.filter(count=count)
        form = self.form_class(instance=count)
        return render(request, self.template_name, {'form': form, 'is_tv_vip':is_tv_vip, 'is_ibo_player':is_ibo_player, 'is_plus_code':is_plus_code, 'is_chatgpt_plus':is_chatgpt_plus, 'count':count, 'profiles':profiles, 'platform': count.plan.platform if count.plan else count.platform})

    def post(self, request, id, *args, **kwargs):

        count = Count.objects.filter(id=id).first()
        try:
            count.sale_price = Decimal(request.POST.get("sale_price") or "0")
            count.profile_sale_price = Decimal(
                request.POST.get("profile_sale_price") or "0"
            )
            count.wholesale_price = Decimal(request.POST.get("wholesale_price") or "0")
        except InvalidOperation:
            return HttpResponse("Los precios no son válidos.", status=400)
        if (
            count.sale_price < 0
            or count.profile_sale_price < 0
            or count.wholesale_price < 0
        ):
            return HttpResponse("Los precios no pueden ser negativos.", status=400)
        if is_chatgpt_plus_platform(count.platform.name):
            email = request.POST.get("email", "").strip()
            expiration = request.POST.get("date_limit", "").strip()
            if not email or not expiration:
                return HttpResponse(
                    "Ingresa el correo y su vencimiento.",
                    status=400,
                )
            if Count.objects.filter(
                platform=count.platform,
                email__iexact=email,
            ).exclude(pk=count.pk).exists():
                return HttpResponse(
                    "Este correo de ChatGPT Plus ya está registrado.",
                    status=409,
                )
            count.email = email
            count.date_limit = expiration
            count.save(update_fields=[
                "email",
                "date_limit",
                "sale_price",
                "profile_sale_price",
                "wholesale_price",
            ])
            return redirect("count-list")

        if is_plus_code_platform(count.platform.name):
            plus_code = request.POST.get("plus_code", "").strip()
            expiration = request.POST.get("date_limit", "").strip()
            if not plus_code or not expiration:
                return HttpResponse(
                    "Ingresa el Código Plus y su vencimiento.",
                    status=400,
                )
            if any(
                existing.password == plus_code
                for existing in Count.objects.filter(
                    platform=count.platform,
                ).exclude(pk=count.pk).only("password")
            ):
                return HttpResponse(
                    "Este Código Plus ya está registrado.",
                    status=409,
                )
            count.password = plus_code
            count.date_limit = expiration
            count.save(update_fields=[
                "password",
                "date_limit",
                "sale_price",
                "profile_sale_price",
                "wholesale_price",
            ])
            return redirect("count-list")

        if count.platform.name.strip().casefold() == "iptv ibo pro player":
            playlist = request.POST.get('link', '').strip()
            if not playlist:
                return HttpResponse("Ingresa la lista de reproducción.", status=400)
            count.link = playlist
            count.date_limit = request.POST['date_limit']
            count.save(update_fields=[
                "link",
                "date_limit",
                "sale_price",
                "profile_sale_price",
                "wholesale_price",
            ])
            existing_numbers = set(
                Profile.objects.filter(count=count).values_list('profile', flat=True)
            )
            for profile_number in range(1, 5):
                if str(profile_number) not in existing_numbers:
                    Profile.objects.create(
                        count=count,
                        profile=str(profile_number),
                        pin="0",
                        saled=False,
                    )
            return redirect("count-list")

        country = Country.objects.filter(id=request.POST['country']).first()
        count.email = request.POST['email']
        if "link" in request.POST:
            count.link = request.POST['link']
        count.country = country
        count.date_limit = request.POST['date_limit']
        selected_plan_id = request.POST.get("plan")
        if selected_plan_id:
            selected_plan = Plan.objects.filter(
                pk=selected_plan_id,
                platform=count.platform,
                active=True,
            ).first()
            if selected_plan:
                count.plan = selected_plan
        count.save()
        for item in request.POST:
            if item.isnumeric():
                if count.plan:
                    if count.plan.name == "TV VIP":
                        profile = Profile.objects.filter(count=count).first()
                        profile.profile = request.POST["profile"]
                else:
                    profile = Profile.objects.filter(count=count, profile = item).first()
                profile.pin=request.POST[item]
                profile.save()
        return redirect("count-list")


@method_decorator(login_required, name='dispatch')
class SelectPlan(View):

    template_name = "count/select-plan-by-platform.html"
    form_class = CountPlanForm

    def get(self, request, platform_id,  *args, **kwargs):

        form = self.form_class(platform_id, purpose=request.GET.get("purpose"))

        return render(request, self.template_name, {'form': form })


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AddPlatformView(CreateView):
    form_class = CreatePlatformForm
    template_name = "platform/add_v2.html"

    def form_valid(self, form):
        platform = form.save()
        for profile_quantity in range(1, platform.num_profiles + 1):
            submitted_price = self.request.POST.get(str(profile_quantity), 0) or 0
            Price.objects.update_or_create(
                platform=platform,
                num_profiles=profile_quantity,
                defaults={"price": submitted_price},
            )
        Action.action_register(
            self.request.user,
            "Creó plataforma id = " + str(platform.id) + ": " + platform.name,
        )
        messages.success(self.request, "La plataforma se creó correctamente.")
        return redirect('platform-list')


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UpdatePlatformView(UpdateView):

    model = Platform
    form_class = CreatePlatformForm
    template_name = "platform/update_v2.html"
    success_url = "/count/platform/list"

    def form_valid(self, form):
        platform = form.save()
        for profile_quantity in range(1, platform.num_profiles + 1):
            Price.objects.get_or_create(
                platform=platform,
                num_profiles=profile_quantity,
                defaults={"price": 0},
            )
        Action.action_register(
            self.request.user,
            "Editó plataforma id = " + str(platform.id) + ": " + platform.name,
        )
        messages.success(self.request, "Los datos de la plataforma se actualizaron.")
        return redirect('platform-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        platform = self.get_object()
        context['platform_name'] = platform.name
        return context



@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class SetPricesOfQuantityProfilesView(View):


    template_name = "profiles/set_prices.html"

    def get(self, request, *args, **kwargs):

        num_profiles = list(range(1, int(kwargs['quantity'])+1))
        return render(request, self.template_name, {'num_profiles': num_profiles})




@method_decorator(login_required, name='dispatch')
class PlatformListView(ListView):

    model = Platform
    template_name = "platform/list_v2.html"

    def get_queryset(self, *args, **kwargs):
        status = self.request.GET.get("status", "all")
        platforms = self.model.objects.annotate(
            accounts_total=Count_("count", distinct=True),
            plans_total=Count_("plan", distinct=True),
        ).order_by("name")
        if status == "active":
            platforms = platforms.filter(active=True)
        elif status == "inactive":
            platforms = platforms.filter(active=False)
        return platforms

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_status"] = self.request.GET.get("status", "all")
        context["platforms_total"] = Platform.objects.count()
        context["platforms_active"] = Platform.objects.filter(active=True).count()
        context["platforms_inactive"] = Platform.objects.filter(active=False).count()
        return context


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class TogglePlatformStatusView(View):

    def post(self, request, pk, *args, **kwargs):
        platform = get_object_or_404(Platform, pk=pk)
        platform.active = not platform.active
        platform.save(update_fields=["active"])
        status_label = "activó" if platform.active else "desactivó"
        Action.action_register(
            request.user,
            status_label.capitalize() + " plataforma id = " + str(platform.id)
            + ": " + platform.name,
        )
        messages.success(
            request,
            "La plataforma se " + status_label + " correctamente.",
        )
        return redirect('platform-list')


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class DeletePlatformView(View):

    def post(self, request, pk, *args, **kwargs):
        platform = get_object_or_404(Platform, pk=pk)
        dependencies = []
        accounts_total = platform.count_set.count()
        plans_total = platform.plan_set.count()
        promotions_total = platform.promotionplatform_set.count()
        if accounts_total:
            dependencies.append(str(accounts_total) + " cuenta(s)")
        if plans_total:
            dependencies.append(str(plans_total) + " plan(es)")
        if promotions_total:
            dependencies.append(str(promotions_total) + " promoción(es)")

        if dependencies:
            messages.error(
                request,
                "No se puede eliminar " + platform.name + " porque tiene "
                + ", ".join(dependencies)
                + ". Desactívala para conservar el historial.",
            )
            return redirect('platform-list')

        platform_id = platform.id
        platform_name = platform.name
        platform.delete()
        Action.action_register(
            request.user,
            "Eliminó plataforma sin uso id = " + str(platform_id) + ": " + platform_name,
        )
        messages.success(request, "La plataforma sin uso se eliminó correctamente.")
        return redirect('platform-list')



@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CreatePinsProfiles(View):

    template_name = "count/num_profiles.html"
    model_class_platform = Platform
    model_class_plan = Plan

    def get(self, request, *args, **kwargs):
        profiles = []
        have_link = is_tv_vip = is_ibo_player = is_plus_code = False
        if kwargs['type'] == "platform":
            model = self.model_class_platform
            platform = Platform.objects.filter(id=kwargs['id']).first()
            is_plus_code = bool(
                platform and is_plus_code_platform(platform.name)
            )
            is_chatgpt_plus = bool(
                platform and is_chatgpt_plus_platform(platform.name)
            )
            if is_plus_code:
                return render(
                    request,
                    self.template_name,
                    {'profiles': [], 'is_plus_code': True},
                )
            plans = Plan.objects.filter(platform_id=kwargs['id'])
            if plans:
                return render(request, self.template_name, {'profiles': None})
        elif kwargs['type'] == "plan":
            plan = Plan.objects.filter(id=kwargs['id']).first()
            if plan.name == "TV VIP":
                is_tv_vip = True
            if is_chatgpt_plus_platform(plan.platform.name):
                return render(
                    request,
                    self.template_name,
                    {
                        'profiles': [],
                        'have_link': False,
                        'is_tv_vip': False,
                        'is_chatgpt_plus': True,
                    },
                )
            if plan.platform.name.strip().casefold() == "iptv ibo pro player":
                return render(
                    request,
                    self.template_name,
                    {
                        'profiles': [],
                        'have_link': True,
                        'is_tv_vip': False,
                        'is_ibo_player': True,
                    },
                )
            have_link = plan.have_link
            model = self.model_class_plan
        num_profiles = model.get_num_of_profiles(kwargs['id'])
        for num in range(num_profiles):
            profiles.append(num)

        return render(
            request,
            self.template_name,
            {
                'profiles': profiles,
                'have_link': have_link,
                'is_tv_vip': is_tv_vip,
                'is_ibo_player': is_ibo_player,
            },
        )


@method_decorator(login_required, name='dispatch')
class CountsListView(ListView):

    model = Count
    template_name = "count/list.html"

    def get_queryset(self,  *args, **kwargs):
        return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.request.GET.get("status", "all").strip().lower()
        if status not in ("all", "active", "inactive", "expiring", "expired"):
            status = "all"
        days = self.request.GET.get("days", "3").strip()
        if days not in ("0", "1", "2", "3"):
            days = "3"
        platform_id = self.request.GET.get("platform", "").strip()
        selected_platform = Platform.objects.filter(
            pk=platform_id,
        ).first() if platform_id.isdigit() else None
        titles = {
            "all": "Todas las cuentas",
            "active": "Cuentas activas",
            "inactive": "Cuentas inactivas",
            "expiring": "Cuentas próximas a vencer",
            "expired": "Cuentas vencidas",
        }
        context.update({
            "account_status": status,
            "account_days": days,
            "selected_platform": selected_platform,
            "platforms": Platform.objects.filter(active=True).order_by("name"),
            "list_title": (
                "Cuentas de " + selected_platform.name
                if selected_platform and status == "all"
                else titles[status]
            ),
        })
        return context


@method_decorator(login_required, name='dispatch')
class CountModulesView(View):
    template_name = "count/modules.html"

    def get(self, request, *args, **kwargs):
        today = django_timezone.localdate()
        third_day = today + datetime.timedelta(days=3)
        accounts = Count.objects.all()
        stats = {
            "total": accounts.count(),
            "active": accounts.filter(active=True).filter(
                Q(date_limit__isnull=True) | Q(date_limit__date__gte=today)
            ).count(),
            "inactive": accounts.filter(active=False).count(),
            "expiring": accounts.filter(
                active=True,
                date_limit__date__gte=today,
                date_limit__date__lte=third_day,
            ).count(),
            "expired": accounts.filter(date_limit__date__lt=today).count(),
        }
        platforms = Platform.objects.annotate(
            account_total=Count_("count"),
            account_active=Count_(
                "count",
                filter=Q(count__active=True) & (
                    Q(count__date_limit__isnull=True)
                    | Q(count__date_limit__date__gte=today)
                ),
            ),
        ).filter(account_total__gt=0).order_by("name")
        return render(
            request,
            self.template_name,
            {"stats": stats, "platforms": platforms},
        )


@method_decorator(login_required, name='dispatch')
class CountListAjax(BaseDatatableView):

    columns = ['Plataforma', 'Plan', 'Correo', 'Perfiles', 'Disponibles', 'Contraseña de cuenta', 'Contraseña de correo', 'pais', 'Vence', 'Estado', 'Precio cuenta', 'Precio perfil', 'Precio mayoreo', 'link']
    order_columns = ['platform__name', 'plan__name', 'email', '', '', '', '', 'country__country', 'date_limit', 'active', 'sale_price', 'profile_sale_price', 'wholesale_price', '']
    model = Count
    #max_display_length = 500

    def get_initial_queryset(self):
        qs = self.model.objects.select_related(
            "platform",
            "plan",
            "country",
        ).annotate(
            total_profiles=Count_("profile"),
            available_profiles=Count_("profile", filter=Q(profile__saled=False)),
        )
        status = self.request.GET.get("status", "all").strip().lower()
        platform_id = self.request.GET.get("platform", "").strip()
        days = self.request.GET.get("days", "3").strip()
        today = django_timezone.localdate()

        if platform_id.isdigit():
            qs = qs.filter(platform_id=int(platform_id))
        if status == "active":
            qs = qs.filter(active=True).filter(
                Q(date_limit__isnull=True) | Q(date_limit__date__gte=today)
            )
        elif status == "inactive":
            qs = qs.filter(active=False)
        elif status == "expired":
            qs = qs.filter(date_limit__date__lt=today)
        elif status == "expiring":
            day_number = int(days) if days in ("0", "1", "2", "3") else 3
            target_date = today + datetime.timedelta(days=day_number)
            qs = qs.filter(active=True, date_limit__date=target_date)
        return qs

    def render_column(self, row, column):
        return super().render_column(row, column)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            q = (
                Q(email__icontains=search)
                | Q(platform__name__icontains=search)
                | Q(plan__name__icontains=search)
                | Q(country__country__icontains=search)
            )
            qs = qs.filter(q)

        return qs

    def prepare_results(self, qs):

        json_data = []
        permissions = my_permissions(self.request.user)
        can_change = 'change_count' in permissions or '*' in permissions
        can_delete = 'delete_count' in permissions or '*' in permissions
        for item in qs:
            today = django_timezone.localdate()
            rest_days = "Indeterminado"
            len_profiles = item.total_profiles
            profiles_available = item.available_profiles
            link_change_password = ''
            link_change_password_email = ''
            link_change_date = ''
            link_update = ''
            link_delete = ''
            if item.date_limit:
                expiration_date = django_timezone.localtime(item.date_limit).date()
                rest_days = (expiration_date - today).days
                if rest_days < 0:
                    rest_days = "Vencida"
                else:
                    rest_days = str(rest_days) + " dia(s)"
            if can_change:
                link_change_password = f'<button type="button" id_count="{ item.id }" class="btn btn-warning change-password">Cuenta</button>'
                link_change_password_email = f'<button type="button" id_count="{ item.id }" class="btn btn-info change-password-email">Correo</button>'
                link_change_date = f'<button type="button" id_count="{item.id}" class="btn btn-primary btn-icon-text change-date-limit">Fecha</button>'
                link_update = f'<a href="/count/update/{item.id}" type="button"  class="btn btn-success btn-icon-text"><i class="mdi mdi-grease-pencil"></i>Editar</a>'
            else:
                link_change_password = ''
                link_change_password_email = ''
                link_change_date = ''
            if can_delete:
                link_delete= f'<button type="button" id_count="{ item.id }" class="btn btn-danger delete-count">Eliminar</button>'
            is_expired = bool(
                item.date_limit
                and django_timezone.localtime(item.date_limit).date() < today
            )
            state_class = (
                "badge-danger" if is_expired
                else "badge-success" if item.active
                else "badge-secondary"
            )
            state_label = (
                "Vencida" if is_expired
                else "Activa" if item.active
                else "Inactiva"
            )
            if is_expired:
                state_html = f'<span class="badge {state_class}">{state_label}</span>'
            elif can_change:
                state_html = (
                    f'<button type="button" class="badge {state_class} toggle-count-status" '
                    f'data-url="/count/toggle-status/{item.id}" title="Cambiar estado">{state_label}</button>'
                )
            else:
                state_html = f'<span class="badge {state_class}">{state_label}</span>'

            if item.plan:
                json_data.append([
                    item.platform.name,
                    item.plan.name,
                    item.email,
                    len_profiles,
                    profiles_available,
                    item.password,
                    item.email_password,
                    item.country.country,
                    rest_days,
                    state_html,
                    str(item.sale_price),
                    str(item.profile_sale_price),
                    str(item.wholesale_price),
                    item.link,
                    link_change_password,
                    link_change_password_email,
                    link_change_date,
                    link_update,
                    link_delete
                ])
            else:
                json_data.append([
                    item.platform.name,
                    "",
                    item.email,
                    len_profiles,
                    profiles_available,
                    item.password,
                    item.email_password,
                    item.country.country,
                    rest_days,
                    state_html,
                    str(item.sale_price),
                    str(item.profile_sale_price),
                    str(item.wholesale_price),
                    item.link,
                    link_change_password,
                    link_change_password_email,
                    link_change_date,
                    link_update,
                    link_delete
                ])
        return json_data


@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class CountToggleStatusView(View):
    permission_required = 'count.change_count'

    def post(self, request, *args, **kwargs):
        account = get_object_or_404(Count, pk=kwargs["pk"])
        account.active = not account.active
        account.save(update_fields=["active"])
        state = "activó" if account.active else "desactivó"
        Action.action_register(
            request.user,
            state.capitalize() + " cuenta id = " + str(account.id),
        )
        return JsonResponse({
            "ok": True,
            "active": account.active,
            "label": "Activa" if account.active else "Inactiva",
        })

@method_decorator(login_required, name='dispatch')
class CountNextExpiredView(View):

    def get(self, request, *args, **kwargs):
        days = request.GET.get("days", "3")
        if days not in ("0", "1", "2", "3"):
            days = "3"
        return redirect("/count/list?status=expiring&days=" + days)


@method_decorator(login_required, name='dispatch')
class CountExpiredView(View):

    def get(self, request, *args, **kwargs):
        return redirect("/count/list?status=expired")


@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class ChangeDateLimitView(View):

    model = Count
    form_class = ChangeDateLimitForm
    template_name = 'count/change_date_limit.html'
    permission_required = 'count.change_count'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name,  {'form': self.form_class, 'id':kwargs['id'] })
    def post(self, request, *args, **kwargs):
        raw_date = request.POST.get('date_limit', '').strip()
        try:
            selected_date = datetime.date.fromisoformat(raw_date)
        except ValueError:
            return HttpResponse("Selecciona una fecha válida.", status=400)

        today = django_timezone.localdate()
        if selected_date < today:
            return HttpResponse(
                "La fecha registrada no puede ser anterior al día de hoy.",
                status=400,
            )

        count = get_object_or_404(self.model, id=kwargs['id'])
        expiration = datetime.datetime.combine(selected_date, datetime.time.max)
        if django_timezone.is_aware(django_timezone.now()):
            expiration = django_timezone.make_aware(
                expiration,
                django_timezone.get_current_timezone(),
            )
        count.date_limit = expiration
        count.save(update_fields=["date_limit"])
        Action.action_register(
            request.user,
            "Cambió vencimiento de cuenta id = " + str(count.id)
            + " a " + selected_date.isoformat(),
        )
        return HttpResponse("Fecha de finalización cambiada con éxito")

@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class EditCountDataView(View):

    model = Profile
    form_class = ChangeCountDataForm
    template_name = 'count/change_password.html'
    permission_required = 'count.change_count'

    def get(self, request, *args, **kwargs):

        return render(request, self.template_name,  {'form': self.form_class, 'id':kwargs['id'], 'type': kwargs['type'] })
    def post(self, request, *args, **kwargs):

        change_password = change_pin = False
        profile = self.model.objects.filter(id=kwargs['id']).first()
        count = Count.objects.filter(id=profile.count.id).first()
        if not request.POST['password'] == "":
            count.password = request.POST['password']
            change_password =True
        if not request.POST['pin'] == "":
            profile.pin = request.POST['pin']
            change_pin =True
        profile.save()
        if change_password:
            Profile.change_password_to_perfile_message(count, None, django_timezone.now())
        elif change_pin:
            Profile.change_password_to_perfile_message(count, profile, django_timezone.now())
        count.save()

        return HttpResponse("Cuenta Actualizados")


@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class EditSaleDataView(View):

    model = Sale

    template_name = 'count/change_sale.html'
    permission_required = 'count.change_sale'

    def get(self, request, *args, **kwargs):
        form_class = ChangeSaleDataForm(kwargs['id'])
        return render(
            request,
            self.template_name,
            {
                'form': form_class,
                'id': kwargs['id'],
                'is_ibo_player': form_class.is_ibo_player,
            },
        )

    def post(self, request, *args, **kwargs):

        sale = get_object_or_404(self.model, id=kwargs['id'])
        form = ChangeSaleDataForm(kwargs['id'], request.POST)
        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {
                    'form': form,
                    'id': kwargs['id'],
                    'is_ibo_player': form.is_ibo_player,
                },
            )

        sale.date = form.cleaned_data['date']
        sale.date_limit = form.cleaned_data['date_limit']
        update_fields = ['date', 'date_limit']
        if form.is_ibo_player:
            sale.device_mac = form.cleaned_data['device_mac']
            sale.device_key = form.cleaned_data['device_key']
            update_fields.extend(['device_mac', 'device_key'])
        sale.save(update_fields=update_fields)
        Action.action_register(
            request.user,
            "Servicio actualizado: venta id = " + str(sale.id),
        )
        return HttpResponse("Servicio actualizado correctamente")



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class CutProfileView(View):

    def post(self, request, *args, **kwargs):
        try:
            sale = Sale.objects.select_related("bill", "profile__count").filter(
                id=kwargs['sale_id'],
                profile_id=kwargs['id'],
            ).first()
            if not sale:
                return HttpResponse('No existe o hubo un error, contacte al administrador del sistema')

            updated_count, profile_released = sale.cut_customer_profile_history()
            Action.action_register(
                request.user,
                "Corte completo de servicio: venta id = " + str(sale.id)
                + ", cliente id = " + str(sale.bill.customer_id)
                + ", perfil id = " + str(sale.profile_id)
                + ", registros cortados = " + str(updated_count),
            )
            if profile_released:
                return HttpResponse(
                    "Corte completo realizado. Se limpiaron "
                    + str(updated_count)
                    + " registros del historial y el perfil quedó disponible."
                )
            return HttpResponse(
                "Corte completo realizado. Se limpiaron "
                + str(updated_count)
                + " registros del historial; el perfil sigue ocupado por otro cliente."
            )
        except Exception:
            return HttpResponse('Hubo un error, contacte al administrador del sistema')



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class OwnerProfileView(View):

    def post(self, request, *args, **kwargs):

        try:
            sales = Sale.objects.filter( profile_id= kwargs['id'] ).exclude(id = kwargs['sale_id'])
            for sale in sales:
                sale.cutted = True
                sale.save()
            return HttpResponse("Se cortaron los perfiles adicionales")
        except:
            return HttpResponse('Hubo un error, contacte al administrador del sistema')



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class AddSaleView(View):

    form_class = SaleForm
    template_name = "sale/add.html"

    def get(self, request, *args, **kwargs):

        customer = Customer.objects.filter(id= kwargs['id']).first()
        if customer:
            promotions = Promotion.get_promotions_actives()
            return render(request, self.template_name, { 'form': self.form_class,  'customer':customer, 'promotions':promotions })
        else:
            return redirect('index')


    @transaction.atomic
    def post(self, request, *args, **kwargs):


        profiles = []
        profiles_json = {}
        form = self.form_class (request.POST)
        customer = Customer.objects.filter(id= kwargs['id']).first()
        if customer and form.is_valid():
            date_limit = CalculateDateLimit(django_timezone.now(), int(request.POST['months']))
            selected_ids = [
                int(item)
                for item in request.POST
                if item.isnumeric() and request.POST[item] == 'on'
            ]
            num_profiles = len(selected_ids)
            platform = Platform.objects.filter(id=request.POST['platform']).first()
            plan_object = Plan.objects.filter(
                id=request.POST.get('plan'),
                platform=platform,
                active=True,
            ).first()
            is_ibo_player = (
                platform
                and platform.name.strip().casefold() == "iptv ibo pro player"
            )
            is_plus_code = bool(
                platform and is_plus_code_platform(platform.name)
            )
            is_chatgpt_plus = bool(
                platform and is_chatgpt_plus_platform(platform.name)
            )
            if not selected_ids:
                return HttpResponse(
                    "Selecciona al menos un perfil disponible.",
                    status=400,
                )

            # Lock and validate every profile submitted by the browser.  The
            # availability table can become stale while a seller has it open,
            # and historical data may contain a false ``saled`` flag.  A sale
            # must never be created while another current, uncut sale exists.
            selected_profiles = list(
                Profile.objects.select_for_update().filter(
                    id__in=selected_ids,
                    count__platform=platform,
                ).select_related("count")
            )
            if (
                len(selected_profiles) != num_profiles
                or any(profile.saled for profile in selected_profiles)
            ):
                return HttpResponse(
                    "Uno de los perfiles ya no está disponible.",
                    status=409,
                )

            ibo_credentials = {}

            if is_ibo_player:
                if not plan_object or num_profiles > plan_object.num_profiles:
                    return HttpResponse(
                        "Para este plan debes seleccionar entre 1 y "
                        + str(plan_object.num_profiles if plan_object else 0)
                        + " dispositivo(s) de la misma lista.",
                        status=400,
                    )
                if len({p.count_id for p in selected_profiles}) != 1:
                    return HttpResponse(
                        "Los dispositivos deben pertenecer a una misma lista IBO.",
                        status=400,
                    )
                if num_profiles < plan_object.num_profiles:
                    pending_profiles = list(
                        Profile.objects.select_for_update().filter(
                            count_id=selected_profiles[0].count_id,
                            saled=False,
                        ).exclude(
                            id__in=selected_ids,
                        ).select_related("count").order_by("id")[
                            :plan_object.num_profiles - num_profiles
                        ]
                    )
                    selected_profiles.extend(pending_profiles)
                    if len(selected_profiles) != plan_object.num_profiles:
                        return HttpResponse(
                            "La lista IBO ya no tiene los dispositivos suficientes para vender la cuenta completa.",
                            status=409,
                        )
                    selected_ids = [profile.id for profile in selected_profiles]
                    num_profiles = len(selected_ids)
                for selected_profile in selected_profiles:
                    raw_mac = request.POST.get(
                        "device_mac_" + str(selected_profile.id),
                        "",
                    ).strip()
                    device_mac = normalize_ibo_device_identifier(raw_mac) or ""
                    device_key = request.POST.get(
                        "device_key_" + str(selected_profile.id),
                        "",
                    ).strip()
                    if raw_mac and not device_mac:
                        return HttpResponse(
                            "La MAC o Device ID del perfil "
                            + str(selected_profile.profile)
                            + " no es válido.",
                            status=400,
                        )
                    if bool(device_mac) != bool(device_key):
                        return HttpResponse(
                            "Ingresa la MAC y la clave juntas para el perfil "
                            + str(selected_profile.profile)
                            + ", o deja ambas pendientes.",
                            status=400,
                        )
                    ibo_credentials[selected_profile.id] = (
                        device_mac,
                        device_key,
                    )

            if is_plus_code:
                if (
                    num_profiles != 1
                    or not selected_profiles[0].count.date_limit
                    or (
                        selected_profiles[0].count.date_limit.date()
                        < django_timezone.localdate()
                    )
                ):
                    return HttpResponse(
                        "Selecciona exactamente un Código Plus vigente.",
                        status=400,
                    )

            if is_chatgpt_plus:
                if not plan_object or num_profiles != plan_object.num_profiles:
                    return HttpResponse(
                        "Para este plan debes seleccionar exactamente "
                        + str(plan_object.num_profiles if plan_object else 0)
                        + " perfil(es).",
                        status=400,
                    )
                if any(
                    not profile.count.date_limit
                    or (
                        profile.count.date_limit.date()
                        < django_timezone.localdate()
                    )
                    for profile in selected_profiles
                ):
                    return HttpResponse(
                        "Uno de los perfiles ya no está disponible.",
                        status=409,
                    )
                if num_profiles == 6 and len({p.count_id for p in selected_profiles}) != 1:
                    return HttpResponse(
                        "La cuenta completa debe usar los 6 perfiles de una misma cuenta.",
                        status=400,
                    )

            if plan_object and not (
                is_ibo_player or is_plus_code or is_chatgpt_plus
            ):
                if any(
                    profile.count.plan_id != plan_object.id
                    for profile in selected_profiles
                ):
                    return HttpResponse(
                        "Uno de los perfiles no pertenece al plan seleccionado.",
                        status=400,
                    )

            open_sale_profile_ids = set(
                Sale.objects.select_for_update().filter(
                    profile_id__in=selected_ids,
                    renovated=False,
                    cutted=False,
                ).values_list("profile_id", flat=True)
            )
            if open_sale_profile_ids:
                # Repair stale availability flags while refusing the duplicate
                # sale. This keeps the profile hidden until its real service is
                # explicitly cut or renewed.
                Profile.objects.filter(
                    id__in=open_sale_profile_ids,
                ).update(saled=True)
                return HttpResponse(
                    "Uno de los perfiles ya está asignado a otro cliente.",
                    status=409,
                )

            plan = plan_object.name if plan_object else ""
            configured_price = None
            if is_ibo_player and selected_profiles:
                ibo_count = selected_profiles[0].count
                account_profile_count = Profile.objects.filter(
                    count=ibo_count,
                ).count()
                if num_profiles == account_profile_count and ibo_count.sale_price > 0:
                    configured_price = ibo_count.sale_price
                elif ibo_count.profile_sale_price > 0:
                    configured_price = ibo_count.profile_sale_price * num_profiles
            if configured_price is None:
                configured_price = (
                    plan_object.sale_price
                    if plan_object and plan_object.sale_price > 0
                    else None
                )
            if configured_price is None:
                total = Price.objects.filter(
                    platform=platform,
                    num_profiles=num_profiles,
                ).first()
                configured_price = total.price if total else None
            if configured_price is None:
                return HttpResponse("No existe un precio configurado para esta venta.", status=400)
            bill = Bill.objects.create(
                customer=customer,
                saler=request.user,
                total=configured_price,
            )
            ibo_devices = []
            i=0
            for profile_id in selected_ids:
                template = 'sale/sale_post.html'
                if plan_object:
                    template = 'sale/sale_plan_post.html'
                profile = Profile.objects.filter(id=profile_id).first()
                if profile:
                    device_mac, device_key = ibo_credentials.get(
                        profile.id,
                        ("", ""),
                    )
                    access_identifier = (
                        device_mac or "Pendiente"
                        if is_ibo_player
                        else profile.count.email
                    )
                    access_password = (
                        device_key or "Pendiente"
                        if is_ibo_player
                        else profile.count.password
                    )
                    if is_chatgpt_plus:
                        access_password = ""
                    profile_json = {"platform": profile.count.platform.name,
                                    "plan":plan,
                                    "email":access_identifier,
                                    "password":access_password,
                                    "phone":str(customer.phone),
                                    "date_limit":str(date_limit.strftime('%d/%m/%Y')),
                                    "profile":"" if is_chatgpt_plus else profile.profile,
                                    "link":"" if is_chatgpt_plus else profile.count.link,
                                    "plus_code":profile.count.password if is_plus_code else "",
                                    "pin":"" if is_chatgpt_plus else profile.pin}
                    profiles_json[i] = profile_json
                    profile.save()
                    profiles.append(profile)
                    if is_ibo_player:
                        ibo_devices.append({
                            "profile": profile.profile,
                            "device_mac": device_mac or "Pendiente",
                            "device_key": device_key or "Pendiente",
                        })
                    i+=1
                    request.user.sale_profile(
                        profile,
                        int(request.POST['months']),
                        date_limit,
                        bill,
                        device_mac=device_mac if is_ibo_player else "",
                        device_key=device_key if is_ibo_player else "",
                    )
            return render(request, template,
                          {
                              'profiles': profiles,
                              'profiles_json': json.dumps(profiles_json),
                              'ibo_devices': ibo_devices,
                              'is_ibo_player': is_ibo_player,
                              'is_plus_code': is_plus_code,
                              'is_chatgpt_plus': is_chatgpt_plus,
                              'date_limit': date_limit.strftime('%d/%m/%Y'),
                          })

        return render(request, self.template_name, {'form': self.form_class })


@method_decorator(login_required, name='dispatch')
class SendMessageWhatsapp(View):

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            if isinstance(data, str):
                data = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return HttpResponse("Los datos del mensaje no son válidos.", status=400)

        results = []
        if isinstance(data, dict) and "platform" in data:
            if data.get('plan') == "TV VIP":
                results.append(message_plan_VIP(data))
            else:
                results.append(message_sale(data))
        elif isinstance(data, dict) and data:
            first_profile = next(iter(data.values()))
            if isinstance(first_profile, dict) and 'plan' in first_profile:
                results.append(message_plan_sale(data))
            else:
                results.extend(message_sale(item) for item in data.values())
        else:
            return HttpResponse("Los datos del mensaje no son válidos.", status=400)

        if WHATSAPP_SEND_ERROR in results:
            return HttpResponse(WHATSAPP_SEND_ERROR, status=502)
        return HttpResponse("Mensaje enviado")

@method_decorator(login_required, name='dispatch')
class SendPlanMessageWhatsapp(View):
    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
        except (json.JSONDecodeError, TypeError):
            return HttpResponse("Los datos del mensaje no son válidos.", status=400)

        result = message_plan_sale(json_data)
        if result == WHATSAPP_SEND_ERROR:
            return HttpResponse(WHATSAPP_SEND_ERROR, status=502)
        return HttpResponse("Mensaje enviado")


class SendMessageWhatsappExpired(SendMessageWhatsapp):
    def post(self, request, *args, **kwargs):
        try:
            json_data = json.loads(request.body)
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
            return HttpResponse("Los datos del mensaje no son válidos.", status=400)

        required = ("platform", "phone", "profile_id")
        if not isinstance(json_data, dict) or any(not json_data.get(key) for key in required):
            return HttpResponse("Los datos del mensaje están incompletos.", status=400)

        try:
            result = message_expired(json_data)
        except (KeyError, TypeError, ValueError):
            return HttpResponse("No fue posible preparar el recordatorio.", status=400)

        if result == WHATSAPP_SEND_ERROR:
            return HttpResponse(WHATSAPP_SEND_ERROR, status=502)
        return HttpResponse(str(json_data["profile_id"]))


@method_decorator(login_required, name='dispatch')
class GetProfilesAvailableView(ListView):

    model = Profile
    template_name = "profiles/list_avaliables.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        if 'platform' in self.kwargs:
            profiles = self.model.search_profiles_no_saled(self.kwargs['platform'])
            platform = Platform.objects.filter(id=self.kwargs['platform']).first()
            context['is_plus_code'] = bool(
                platform and is_plus_code_platform(platform.name)
            )
            if context['is_plus_code']:
                profiles = profiles.filter(
                    count__date_limit__date__gte=django_timezone.localdate(),
                )
        if 'plan' in self.kwargs:
            profiles, num_profiles  = self.model.search_profiles_no_saled_by_plan(self.kwargs['plan'])
            context['num_profiles'] = num_profiles
            plan = Plan.objects.filter(id=self.kwargs['plan']).select_related('platform').first()
            context['is_ibo_player'] = bool(
                plan
                and plan.platform.name.strip().casefold() == "iptv ibo pro player"
            )
            context['is_chatgpt_plus'] = bool(
                plan and is_chatgpt_plus_platform(plan.platform.name)
            )
            if context['is_chatgpt_plus']:
                profiles = profiles.filter(
                    count__date_limit__date__gte=django_timezone.localdate(),
                )
        context['profiles'] = profiles

        return context



@method_decorator(login_required, name='dispatch')
class CancelSaleView(View):

    model = Sale
    def post(self, request, *args, **kwargs):
        sale = self.model.objects.select_related("bill", "profile__count").filter(
            id=self.kwargs['id'],
        ).first()
        if not sale:
            return HttpResponse(
                "No existe o hubo un error, contacte al administrador del sistema",
                status=404,
            )

        updated_count, profile_released = sale.cancel_sale()
        Action.action_register(
            request.user,
            "Cancelación completa del servicio: venta id = " + str(sale.id)
            + ", factura id = " + str(sale.bill_id)
            + ", cliente id = " + str(sale.bill.customer_id)
            + ", perfil id = " + str(sale.profile_id)
            + ", registros cortados = " + str(updated_count),
        )

        if profile_released:
            return HttpResponse(
                "Servicio cortado completamente. Se limpiaron "
                + str(updated_count)
                + " registros del historial y el perfil quedó disponible."
            )
        return HttpResponse(
            "Servicio cortado completamente. Se limpiaron "
            + str(updated_count)
            + " registros del historial; el perfil sigue ocupado por otro cliente."
        )



@method_decorator(login_required, name='dispatch')
class SearchSaleView(View):

    model = Sale
    template_name = "count/search.html"
    form_class = SearchCountForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name,  {'form': self.form_class })


    def post(self, request, *args, **kwargs):

        sales = self.model.objects.filter(profile__saled=True, cutted=False, renovated=False,  profile__count__email=request.POST['email'].strip(), profile__count__platform=request.POST['platform']).order_by('date_limit')
        have_avaliable, availables, repeats = Profile.get_profiles_avaliable(sales, request.POST['platform'])
        for sale in sales:
            rest_days = getDifference(django_timezone.now(), sale.date_limit, 'days')
            if  sale.profile.profile in repeats:
                sale.buttom_owner = True
            sale.rest_days = rest_days
        return render(request, "count/search_list.html", { 'sales':sales, 'email': request.POST['email'], 'have_avaliable':have_avaliable })

@method_decorator(login_required, name='dispatch')
class ChangeProfileSaleView(View):

    model = Sale
    template_name = "count/change_profile_sale.html"

    def get(self, request, *args, **kwargs):

        sale = self.model.objects.filter(id=kwargs['pk']).first()
        sales = self.model.objects.filter(profile__saled=True, cutted=False, profile__count__email=sale.profile.count.email.strip()).order_by('date_limit')
        have_avaliable, availables, repeats = get_profiles_avaliable(sales)
        profiles = Profile.objects.filter(count=sale.profile.count, profile__in=availables )
        return render(request, self.template_name,  {'profiles': profiles, 'id':kwargs['pk'] })

    def post(self, request, *args, **kwargs):

        sale = self.model.objects.filter(id=kwargs['pk']).first()
        if sale:
            sale.profile_id = request.POST['profile']
            sale.save()
            profile = Profile.objects.filter(id = request.POST['profile'] ).first()
            profile.saled=True
            profile.save()
            return redirect('search-sale')




@method_decorator(login_required, name='dispatch')
class ChangeTypePasswordView(View):

    model = Count
    template_name = "count/change_password.html"
    form_class_count = ChangePaswordForm
    form_class_email = ChangePaswordEmailForm
    def get(self, request, *args, **kwargs):

        form_class = self.form_class_count if kwargs['type'] == "count"  else self.form_class_email

        return render(request, self.template_name,  {'form': form_class, 'id':kwargs['id'], 'type': kwargs['type'] })

    def post(self, request, *args, **kwargs):

        count = self.model.objects.filter(id=self.kwargs['id']).first()

        if  kwargs['type'] == "count":
            Action.action_register(request.user, "Cambio password de cuenta id = "+ str(count.id) + " del dia " + str(count.date) )
            count.change_count_password(request.POST['password'])
            Profile.change_password_to_perfile_message(count, None, django_timezone.now())

        elif kwargs['type'] == "email":
            Action.action_register(request.user,
                                   "Cambio password de correo id = " + str(count.id) + " del dia " + str(count.date))
            count.change_email_password(request.POST['email_password'])

        return HttpResponse("Contraseña editada conrrectamente")




@method_decorator(login_required, name='dispatch')
class BillListView(ListView):

    model = Bill
    template_name = "bill/list.html"

    def get_queryset(self,  *args, **kwargs):

        bills = self.model.objects.filter(saler=self.request.user).order_by('-date')
        return bills


@method_decorator(login_required, name='dispatch')
class SalesListView(ListView):
    model = Sale
    template_name = "sale/list.html"

    def get_queryset(self, *args, **kwargs):

        sales = self.model.objects.filter(bill=self.kwargs['id'], bill__saler=self.request.user)
        for sale in sales:
            rest_days = getDifference(django_timezone.now(), sale.date_limit, 'days')
            if rest_days < 0:
                sale.rest_days = "Vencida"
            else:
                sale.rest_days = rest_days
        return sales

    def post(self, request, *args, **kwargs):

        total = 0
        counts = {}
        bill = Bill.objects.create(customer_id=kwargs['id'], saler=request.user, total=0)
        for item in request.POST:
            if item.isnumeric():
                if request.POST[item] == 'on':
                    sales = Sale.objects.filter(id=item)
                    last_sale = sales.last()
                    sales.update(renovated=True)
                    profile = Profile.objects.filter(id=last_sale.profile_id).first()
                    if not profile.count.id in counts:
                        counts[last_sale.profile.count.id] = { "amount": 1 }
                    else:
                        counts[last_sale.profile.count.id]['amount'] = counts[profile.count.id]['amount'] + 1
                    counts[last_sale.profile.count.id]["platform"] = profile.count.platform.id
                    date_limit = CalculateDateLimit(last_sale.date_limit, int(request.POST['months']))
                    renewed_sale = request.user.sale_profile(
                        last_sale.profile,
                        int(request.POST['months']),
                        date_limit,
                        bill,
                        device_mac=last_sale.device_mac,
                        device_key=last_sale.device_key,
                    )
                    message_renew(last_sale.profile, last_sale.bill.customer.phone, date_limit, renewed_sale)

        for key in counts:
            subtotal = Price.objects.filter(platform_id=counts[key]['platform'], num_profiles=counts[key]['amount'] ).first()
            total = total + subtotal.price
        bill.total = total
        bill.save()
        return redirect('bill-list')


@method_decorator(login_required, name='dispatch')
class InterdatesSalesView(ListView):

    model = Bill
    template_name = "sale/list-no-layout.html"

    def get_queryset(self, *args, **kwargs):

        if 'user' in kwargs:
            user = User.objects.filter(username = kwargs['user'])
        else:
            user = self.request.user

        bills = self.model.GetInterdatesBills(user, self.kwargs['initial_date'],
                                                  self.kwargs['final_date'] )
        return bills


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class CreatePromotionView(View):

    model = Promotion
    template_name = "promotion/create.html"

    def get(self, request, *args, **kwargs):
        counts = []
        platforms =  Platform.objects.filter(active=True)
        for platform in platforms:
            list = []
            for profile in range(platform.num_profiles):
                list.append(profile)
                counts.append(( platform.name+'_'+ str(profile), platform.name))
            platform.list = list
        form = CreatePromotionForm()
        form_platform = PlatformForm()
        form_platform.fields['platforms'].choices = counts
        return render(request, self.template_name, { 'form':form, 'platforms': platforms, 'form_platform':form_platform })

    def post(self, request, *args, **kwargs):

        form = CreatePromotionForm(request.POST, request.FILES)
        if form.is_valid():
            promotion = form.save(commit=False)
            promotion.creater = request.user
            promotion.date_init = request.POST['date_init'] + " 00:00:01.850566"
            promotion.date_finish = request.POST['date_finish'] + " 23:59:59.850566"
            promotion.save()
            for platform_name_profle in request.POST.getlist('platforms'):
                platform_name_list = platform_name_profle.split("_")
                platform = Platform.objects.filter(name=platform_name_list[0]).first()
                PromotionPlatform.objects.create(promotion=promotion, platform= platform)
            return redirect('index')
        return render(request, self.template_name, {'form': form})

@method_decorator(login_required, name='dispatch')
class ListPromotionView(ListView):

    model = Promotion
    template_name = "promotion/list.html"

    def get_queryset(self, *args, **kwargs):
        promotions = self.model.objects.filter(active=True).order_by('-date_finish')
        return promotions


class SalePromotionView(View):


    model = Promotion
    template_name = "promotion/sale.html"

    def post(self, request, *args, **kwargs):

        profiles = []
        customer = Customer.objects.filter(id=kwargs['user_id']).first()
        promotion = Promotion.objects.filter(id=kwargs['promotion_id']).first()
        promotion_platforms = PromotionPlatform.objects.filter(promotion_id=kwargs['promotion_id'])
        bill = Bill.objects.create(customer=customer, saler=request.user, total=promotion.price)
        for promotion_platform in promotion_platforms:
            profile = Profile.search_profiles_no_saled(promotion_platform.platform_id)[0]
            date_limit = CalculateDateLimit(django_timezone.now(), int(request.POST['months_promo']))
            profiles.append(profile)
            request.user.sale_profile(profile, int(request.POST['months_promo']), date_limit, bill)
            message_sale(profile, customer, date_limit)
        PromotionSale.objects.create(promotion=promotion, customer=customer )

        return render(request, 'sale/sale_post.html', {'profiles': profiles})


class CronWhatsappView(ListView):
    pass


@method_decorator(login_required, name='dispatch')
class InterDatesView(View):

    def get(self, request, *args, **kwargs):

        ctx = {}
        form = GetInterDatesForm()
        ctx['form'] = form
        ctx['titles'] = settings.TITLES_INTER_DATES[kwargs['model']]
        if 'user' in kwargs:
            ctx['username'] = kwargs['user']

        return render(request, 'inter-dates.html', ctx)



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class CountDeleteView(View):

    model = Count

    def post(self, request, *args, **kwargs):
        count = get_object_or_404(self.model, id=kwargs['pk'])
        count_id = count.id
        count_email = count.email
        count.delete()
        Action.action_register(
            request.user,
            "Cuenta eliminada permanentemente: id = " + str(count_id)
            + ", cuenta = " + count_email,
        )
        return HttpResponse("La cuenta y sus perfiles fueron eliminados permanentemente.")


class WholesalePermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow superusers and collaborators authorized for a module."""

    raise_exception = False
    permission_names = ()

    def test_func(self):
        return (
            self.request.user.is_superuser
            or any(
                self.request.user.has_perm(permission_name)
                for permission_name in self.permission_names
            )
        )


class WholesaleModulesView(WholesalePermissionMixin, View):
    """Landing page for every Control feature connected to MyPlataforma."""

    template_name = "wholesale/modules.html"
    permission_names = (
        "count.manage_wholesale_customers",
        "count.manage_wholesale_slides",
        "count.manage_partner_media_prices",
    )

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


def _sync_partner_media_prices():
    """Refresh private provider costs without overwriting our sale prices."""
    plans, provider, error = get_partner_media_markets()
    if error:
        return 0, provider, error

    synchronized = 0
    with transaction.atomic():
        for source in plans:
            external_plan_id = source.get("plan_id", source.get("id"))
            if external_plan_id in (None, ""):
                continue
            try:
                provider_cost = Decimal(str(source.get("price") or 0)).quantize(
                    Decimal("0.01")
                )
            except (InvalidOperation, TypeError, ValueError):
                continue
            time_value = source.get("time")
            time_unit = str(source.get("unity_time") or "").strip()
            duration = "{} {}".format(time_value, time_unit).strip()
            PartnerMediaPrice.objects.update_or_create(
                service=source["service"],
                external_plan_id=str(external_plan_id),
                with_tv=bool(source.get("with_tv")),
                defaults={
                    "name": str(source.get("name") or source.get("plan") or "Plan"),
                    "connections": max(int(source.get("connections") or 1), 1),
                    "duration": duration,
                    "currency_prefix": str(
                        provider.get("currency_prefix") or "MXN"
                    )[:12],
                    "provider_cost": provider_cost,
                },
            )
            synchronized += 1
    return synchronized, provider, None


def partner_media_prices_context():
    prices = list(PartnerMediaPrice.objects.all())
    published = sum(1 for item in prices if item.active and item.sale_price > 0)
    profitable = [item for item in prices if item.sale_price > item.provider_cost]
    return {
        "prices": prices,
        "partner_api_configured": partner_api_configured(),
        "stats": {
            "plans": len(prices),
            "published": published,
            "pending": len(prices) - published,
            "average_margin": (
                sum((item.margin_percent for item in profitable), Decimal("0"))
                / len(profitable)
                if profitable
                else Decimal("0")
            ),
        },
    }


class WholesaleMediaPricesView(WholesalePermissionMixin, View):
    template_name = "wholesale/media_prices.html"
    permission_names = ("count.manage_partner_media_prices",)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, partner_media_prices_context())

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "").strip()
        if action == "sync":
            synchronized, provider, error = _sync_partner_media_prices()
            if error:
                messages.error(request, error)
            else:
                messages.success(
                    request,
                    "Se actualizaron {} planes y sus costos privados. Saldo proveedor: {} {}.".format(
                        synchronized,
                        provider.get("currency_prefix") or "MXN",
                        provider.get("balance") or 0,
                    ),
                )
                Action.action_register(
                    request.user,
                    "Costos API de MyPlataforma sincronizados: {} planes".format(
                        synchronized
                    ),
                )
            return redirect("wholesale-media-prices")

        if action != "save":
            messages.error(request, "Acción de precios no válida.")
            return redirect("wholesale-media-prices")

        price_row = get_object_or_404(
            PartnerMediaPrice,
            pk=request.POST.get("price_id"),
        )
        try:
            sale_price = Decimal(
                str(request.POST.get("sale_price", "0")).strip()
            ).quantize(Decimal("0.01"))
        except (InvalidOperation, TypeError, ValueError):
            messages.error(request, "Ingresa un precio de venta válido.")
            return redirect("wholesale-media-prices")

        publish = request.POST.get("active") == "on"
        if sale_price < 0:
            messages.error(request, "El precio de venta no puede ser negativo.")
            return redirect("wholesale-media-prices")
        if sale_price and sale_price <= price_row.provider_cost:
            messages.error(
                request,
                "El precio de venta debe ser mayor al costo para generar utilidad.",
            )
            return redirect("wholesale-media-prices")
        if publish and not sale_price:
            messages.error(
                request,
                "Configura un precio de venta antes de publicar el plan.",
            )
            return redirect("wholesale-media-prices")

        price_row.sale_price = sale_price
        price_row.active = publish
        price_row.save(update_fields=("sale_price", "active", "updated_at"))
        Action.action_register(
            request.user,
            "Precio API actualizado: {} · {} · venta {}".format(
                price_row.get_service_display(),
                price_row.name,
                sale_price,
            ),
        )
        messages.success(request, "Precio y estado guardados correctamente.")
        return redirect("wholesale-media-prices")


def _sync_default_wholesale_publications(created_by=None):
    """Publish complete-account plans that already have a configured price."""
    created = 0
    partners = list(WholesalePartner.objects.filter(active=True))
    if not partners:
        return created

    plans = Plan.objects.filter(
        active=True,
        platform__active=True,
        count__active=True,
    ).select_related("platform").distinct()
    for plan in plans:
        if not WholesalePublication.complete_accounts_for_plan(plan).exists():
            continue
        configured_price = Price.objects.filter(
            platform=plan.platform,
            num_profiles=plan.num_profiles,
            price__gt=0,
        ).order_by("id").first()
        if not configured_price:
            continue
        for partner in partners:
            _, was_created = WholesalePublication.objects.get_or_create(
                partner=partner,
                plan=plan,
                defaults={
                    "wholesale_price": configured_price.price,
                    "catalog_title": plan.platform.name + " · Cuenta completa",
                    "catalog_description": (
                        "Cuenta completa con " + str(plan.num_profiles)
                        + " perfil(es) disponibles."
                    ),
                    "created_by": created_by,
                    "active": True,
                },
            )
            created += int(was_created)
    return created


def wholesale_inventory_context(request, form=None, editing_publication=None):
    _sync_default_wholesale_publications(
        request.user if request.user.is_superuser else None
    )
    all_publications = WholesalePublication.objects.select_related(
        "partner",
        "partner__customer",
        "plan",
        "plan__platform",
        "created_by",
    )
    publications = all_publications

    partner_filter = request.GET.get("partner", "").strip()
    status_filter = request.GET.get("status", "").strip()
    search = request.GET.get("q", "").strip()

    if partner_filter.isdigit():
        publications = publications.filter(partner_id=int(partner_filter))
    if status_filter in ("active", "inactive"):
        publications = publications.filter(active=(status_filter == "active"))
    if search:
        publications = publications.filter(
            Q(partner__username__icontains=search)
            | Q(partner__customer__name__icontains=search)
            | Q(plan__platform__name__icontains=search)
            | Q(plan__name__icontains=search)
        )

    publication_rows = list(publications)
    complete_accounts_count = Count.complete_available().count()
    available_plan_rows = []
    for plan in Plan.objects.filter(
        active=True,
        platform__active=True,
    ).select_related("platform"):
        units = _available_profiles_for_plan(plan).count() // max(plan.num_profiles, 1)
        if units:
            available_plan_rows.append((plan, units))

    return {
        "form": form or WholesalePublicationForm(),
        "editing_publication": editing_publication,
        "publications": publication_rows,
        "recent_purchases": WholesalePurchase.objects.select_related(
            "partner",
            "partner__customer",
            "publication__plan__platform",
            "account__platform",
            "account__plan",
            "plan__platform",
            "bill",
        )[:50],
        "partners": WholesalePartner.objects.select_related("customer").order_by(
            "username"
        ),
        "selected_partner": partner_filter,
        "selected_status": status_filter,
        "search_query": search,
        "stats": {
            "partners": WholesalePartner.objects.filter(active=True).count(),
            "complete_accounts": complete_accounts_count,
            "plans": len(available_plan_rows),
            "available": complete_accounts_count + sum(
                units for _, units in available_plan_rows
            ),
            "purchases": WholesalePurchase.objects.count(),
        },
    }


class WholesaleInventoryView(WholesalePermissionMixin, View):
    template_name = "wholesale/inventory.html"
    permission_names = ("count.manage_wholesale_customers",)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, wholesale_inventory_context(request))

    def post(self, request, *args, **kwargs):
        form = WholesalePublicationForm(request.POST, request.FILES)
        if form.is_valid():
            publication = form.save(commit=False)
            publication.created_by = request.user
            publication.save()
            Action.action_register(
                request.user,
                "Inventario mayorista publicado: " + str(publication),
            )
            messages.success(request, "El plan quedó publicado para el mayorista.")
            return redirect("wholesale-inventory")

        messages.error(request, "Revisa los datos marcados antes de guardar.")
        return render(
            request,
            self.template_name,
            wholesale_inventory_context(request, form=form),
        )


class WholesalePublicationEditView(WholesalePermissionMixin, View):
    template_name = "wholesale/inventory.html"
    permission_names = ("count.manage_wholesale_customers",)

    def get(self, request, *args, **kwargs):
        publication = get_object_or_404(WholesalePublication, pk=kwargs["pk"])
        form = WholesalePublicationForm(instance=publication)
        return render(
            request,
            self.template_name,
            wholesale_inventory_context(
                request,
                form=form,
                editing_publication=publication,
            ),
        )

    def post(self, request, *args, **kwargs):
        publication = get_object_or_404(WholesalePublication, pk=kwargs["pk"])
        form = WholesalePublicationForm(
            request.POST,
            request.FILES,
            instance=publication,
        )
        if form.is_valid():
            publication = form.save()
            Action.action_register(
                request.user,
                "Inventario mayorista actualizado: " + str(publication),
            )
            messages.success(request, "La publicación mayorista fue actualizada.")
            return redirect("wholesale-inventory")

        messages.error(request, "Revisa los datos marcados antes de guardar.")
        return render(
            request,
            self.template_name,
            wholesale_inventory_context(
                request,
                form=form,
                editing_publication=publication,
            ),
        )


class WholesalePublicationToggleView(WholesalePermissionMixin, View):
    permission_names = ("count.manage_wholesale_customers",)

    def post(self, request, *args, **kwargs):
        publication = get_object_or_404(WholesalePublication, pk=kwargs["pk"])
        publication.active = not publication.active
        publication.save(update_fields=["active", "updated_at"])
        state = "publicado" if publication.active else "ocultado"
        Action.action_register(
            request.user,
            "Inventario mayorista " + state + ": " + str(publication),
        )
        messages.success(request, "El plan fue " + state + " correctamente.")
        return redirect("wholesale-inventory")


def wholesale_slides_context(form=None, editing_slide=None):
    return {
        "form": form or WholesaleSlideForm(),
        "editing_slide": editing_slide,
        "slides": WholesaleSlide.objects.select_related("created_by").all(),
        "active_slides": WholesaleSlide.objects.filter(active=True).count(),
    }


class WholesaleSlidesView(WholesalePermissionMixin, View):
    template_name = "wholesale/slides.html"
    permission_names = ("count.manage_wholesale_slides",)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, wholesale_slides_context())

    def post(self, request, *args, **kwargs):
        form = WholesaleSlideForm(request.POST, request.FILES)
        if form.is_valid():
            slide = form.save(commit=False)
            slide.created_by = request.user
            try:
                slide.save()
            except OSError:
                logger.exception("No se pudo guardar la imagen del anuncio mayorista")
                form.add_error(
                    "image",
                    "No se pudo guardar la imagen. Inténtalo nuevamente o contacta al administrador.",
                )
                messages.error(request, "No fue posible publicar el anuncio.")
                return render(
                    request,
                    self.template_name,
                    wholesale_slides_context(form=form),
                    status=503,
                )
            Action.action_register(
                request.user,
                "Anuncio de MyPlataforma publicado: " + slide.title,
            )
            messages.success(request, "El anuncio ya está disponible en MyPlataforma.")
            return redirect("wholesale-slides")
        messages.error(request, "Revisa los datos del anuncio antes de guardar.")
        return render(request, self.template_name, wholesale_slides_context(form=form))


class WholesaleSlideEditView(WholesalePermissionMixin, View):
    template_name = "wholesale/slides.html"
    permission_names = ("count.manage_wholesale_slides",)

    def get(self, request, *args, **kwargs):
        slide = get_object_or_404(WholesaleSlide, pk=kwargs["pk"])
        return render(
            request,
            self.template_name,
            wholesale_slides_context(
                form=WholesaleSlideForm(instance=slide),
                editing_slide=slide,
            ),
        )

    def post(self, request, *args, **kwargs):
        slide = get_object_or_404(WholesaleSlide, pk=kwargs["pk"])
        form = WholesaleSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            try:
                slide = form.save()
            except OSError:
                logger.exception("No se pudo actualizar la imagen del anuncio mayorista")
                form.add_error(
                    "image",
                    "No se pudo guardar la imagen. Inténtalo nuevamente o contacta al administrador.",
                )
                messages.error(request, "No fue posible actualizar el anuncio.")
                return render(
                    request,
                    self.template_name,
                    wholesale_slides_context(form=form, editing_slide=slide),
                    status=503,
                )
            Action.action_register(
                request.user,
                "Anuncio de MyPlataforma actualizado: " + slide.title,
            )
            messages.success(request, "El anuncio fue actualizado.")
            return redirect("wholesale-slides")
        messages.error(request, "Revisa los datos del anuncio antes de guardar.")
        return render(
            request,
            self.template_name,
            wholesale_slides_context(form=form, editing_slide=slide),
        )


class WholesaleSlideToggleView(WholesalePermissionMixin, View):
    permission_names = ("count.manage_wholesale_slides",)

    def post(self, request, *args, **kwargs):
        slide = get_object_or_404(WholesaleSlide, pk=kwargs["pk"])
        slide.active = not slide.active
        slide.save(update_fields=["active", "updated_at"])
        state = "publicado" if slide.active else "ocultado"
        Action.action_register(
            request.user,
            "Anuncio de MyPlataforma " + state + ": " + slide.title,
        )
        messages.success(request, "El anuncio fue " + state + ".")
        return redirect("wholesale-slides")


class WholesaleSlideDeleteView(WholesalePermissionMixin, View):
    permission_names = ("count.manage_wholesale_slides",)

    def post(self, request, *args, **kwargs):
        slide = get_object_or_404(WholesaleSlide, pk=kwargs["pk"])
        title = slide.title
        image_name = slide.image.name
        image_storage = slide.image.storage

        with transaction.atomic():
            slide.delete()
            Action.action_register(
                request.user,
                "Anuncio de MyPlataforma eliminado: " + title,
            )

        if image_name:
            try:
                image_storage.delete(image_name)
            except OSError:
                logger.exception(
                    "El anuncio fue eliminado, pero no se pudo retirar su imagen: %s",
                    image_name,
                )

        messages.success(request, "El anuncio fue eliminado definitivamente.")
        return redirect("wholesale-slides")


def _wholesale_api_authorized(request):
    try:
        expected_token = WholesaleServicesApiView.token_file.read_text(
            encoding="utf-8"
        ).strip()
    except OSError:
        return False, JsonResponse(
            {"error": "Integración no configurada"},
            status=503,
        )
    authorization = request.META.get("HTTP_AUTHORIZATION", "")
    supplied_token = (
        authorization[7:].strip()
        if authorization.lower().startswith("bearer ")
        else ""
    )
    authorized = bool(expected_token) and secrets.compare_digest(
        supplied_token,
        expected_token,
    )
    return authorized, None if authorized else JsonResponse(
        {"error": "No autorizado"},
        status=401,
    )


def _public_media_url(field):
    if not field:
        return ""
    try:
        url = field.url
    except (ValueError, AttributeError):
        return ""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "https://control.elgamermexicano.com" + url


def _available_profiles_for_plan(plan, now=None):
    """Live, unassigned profiles eligible for one plan purchase."""
    now = now or django_timezone.now()
    profiles, _ = Profile.search_profiles_no_saled_by_plan(plan.id)
    active_sale = Sale.objects.filter(
        profile_id=OuterRef("pk"),
        renovated=False,
        cutted=False,
        date_limit__gte=now,
    )
    return profiles.filter(
        count__active=True,
        count__platform__active=True,
        count__date_limit__gte=now,
    ).annotate(
        has_active_sale=Exists(active_sale),
    ).filter(
        has_active_sale=False,
    ).select_related(
        "count",
        "count__platform",
        "count__plan",
    ).order_by("-count__date_limit", "id")


class WholesalePortalApiView(View):
    """Catálogo, anuncios y métricas que MyPlataforma consume desde Control."""

    def get(self, request, *args, **kwargs):
        authorized, error_response = _wholesale_api_authorized(request)
        if not authorized:
            return error_response

        partner = get_object_or_404(
            WholesalePartner.objects.select_related("customer"),
            username__iexact=kwargs["username"],
            active=True,
        )
        catalog = []
        today = django_timezone.localdate()

        # Every completely free account is published as its own whole-account
        # offer. Credentials are never exposed until the purchase succeeds.
        complete_accounts = Count.complete_available().select_related(
            "platform",
            "plan",
        )
        for account in complete_accounts:
            profiles_count = int(account.total_profiles or 0)
            catalog.append({
                "offer_key": "account-" + str(account.id),
                "offer_type": "account",
                "platform_id": account.platform_id,
                "platform": account.platform.name,
                "plan_id": account.plan_id,
                "plan": account.plan.name if account.plan_id else "Cuenta completa",
                "title": account.platform.name + " · Cuenta completa",
                "description": "Cuenta completa con {} perfil(es) disponibles.".format(profiles_count),
                "price": str(account.wholesale_price),
                "available_units": 1,
                "profiles_per_account": profiles_count,
                "next_account_days": max((account.date_limit.date() - today).days, 0),
                "image_url": _public_media_url(account.platform.logo),
                "featured": False,
                "sort_order": 0,
            })

        # Plans are separate offers. A one-profile plan allows the wholesaler
        # to buy only one profile; larger plans preserve their configured size.
        plans = Plan.objects.filter(
            active=True,
            platform__active=True,
        ).select_related("platform").order_by("platform__name", "num_profiles", "name")
        overrides = {
            publication.plan_id: publication
            for publication in WholesalePublication.objects.filter(
                partner=partner,
            ).select_related("plan", "plan__platform")
        }
        now = django_timezone.now()
        for plan in plans:
            profiles = _available_profiles_for_plan(plan, now)
            available_units = profiles.count() // max(plan.num_profiles, 1)
            if available_units <= 0:
                continue
            first_profile = profiles.first()
            override = overrides.get(plan.id)
            if override and not override.active:
                continue
            image = (
                override.catalog_image
                if override and override.catalog_image
                else plan.platform.logo
            )
            catalog.append({
                "offer_key": "plan-" + str(plan.id),
                "offer_type": "plan",
                "platform_id": plan.platform_id,
                "platform": plan.platform.name,
                "plan_id": plan.id,
                "plan": plan.name,
                "title": override.display_title if override else plan.platform.name + " · " + plan.name,
                "description": override.display_description if override else (
                    "Plan mayorista de {} perfil(es).".format(plan.num_profiles)
                ),
                "price": str(
                    override.wholesale_price if override else plan.wholesale_price
                ),
                "available_units": available_units,
                "profiles_per_account": plan.num_profiles,
                "next_account_days": max(
                    (first_profile.count.date_limit.date() - today).days,
                    0,
                ),
                "image_url": _public_media_url(image),
                "featured": bool(override and override.featured),
                "sort_order": override.sort_order if override else 10,
            })

        catalog.sort(key=lambda item: (
            item["sort_order"],
            item["platform"].casefold(),
            item["offer_type"],
            item["title"].casefold(),
        ))

        now = django_timezone.now()
        slides = WholesaleSlide.objects.filter(active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        )
        slide_rows = [{
            "id": slide.id,
            "title": slide.title,
            "subtitle": slide.subtitle,
            "image_url": _public_media_url(slide.image),
            "button_text": slide.button_text,
            "button_url": slide.button_url,
        } for slide in slides]

        sales = Sale.objects.filter(bill__customer_id=partner.customer_id)
        active_sales = sales.filter(
            renovated=False,
            cutted=False,
            date_limit__gte=now,
        )
        today = django_timezone.localdate()
        last_30 = now - datetime.timedelta(days=30)
        in_48_hours = now + datetime.timedelta(hours=48)
        metrics = {
            "catalog_products": len(catalog),
            "available_units": sum(item["available_units"] for item in catalog),
            "active_accounts": active_sales.values(
                "profile__count_id"
            ).distinct().count(),
            "purchases_30_days": sales.filter(date__gte=last_30).values(
                "profile__count_id"
            ).distinct().count(),
            "purchases_today": sales.filter(date__date=today).values(
                "profile__count_id"
            ).distinct().count(),
            "expiring_48_hours": active_sales.filter(
                date_limit__lte=in_48_hours
            ).values("profile__count_id").distinct().count(),
        }
        return JsonResponse({
            "partner": {
                "username": partner.username,
                "customer_id": partner.customer_id,
                "customer_name": partner.customer.name,
            },
            "generated_at": now.isoformat(),
            "catalog": catalog,
            "slides": slide_rows,
            "metrics": metrics,
        })


def _wholesale_purchase_payload(purchase, idempotent=False):
    sales = list(Sale.objects.filter(bill=purchase.bill).select_related(
        "profile__count__platform",
        "profile__count__plan",
    ).order_by("id"))
    first_sale = sales[0] if sales else None
    account = purchase.account or (
        first_sale.profile.count if first_sale else None
    )
    plan = purchase.plan or (account.plan if account and account.plan_id else None)
    expires_at = min(
        (sale.date_limit for sale in sales if sale.date_limit),
        default=None,
    )
    return {
        "ok": True,
        "idempotent": idempotent,
        "purchase_id": purchase.id,
        "external_reference": purchase.external_reference,
        "purchase_type": purchase.purchase_type,
        "price": str(purchase.price),
        "account_id": account.id if account else None,
        "platform": account.platform.name if account else plan.platform.name,
        "plan": plan.name if plan else "Cuenta completa",
        "profiles_count": purchase.profiles_count,
        "expires_at": expires_at.isoformat() if expires_at else "",
    }


@method_decorator(csrf_exempt, name="dispatch")
class WholesalePurchaseApiView(View):
    """Atomically sell a complete account or a configured plan."""

    def post(self, request, *args, **kwargs):
        authorized, error_response = _wholesale_api_authorized(request)
        if not authorized:
            return error_response

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return JsonResponse({"error": "Solicitud inválida"}, status=400)

        reference = str(payload.get("reference", "")).strip()
        offer_key = str(payload.get("offer_key", "")).strip()
        if (
            not reference
            or len(reference) > 64
            or not reference.isalnum()
            or "-" not in offer_key
        ):
            return JsonResponse({"error": "Referencia de compra inválida"}, status=400)

        offer_type, offer_id = offer_key.split("-", 1)
        if offer_type not in {"account", "plan"} or not offer_id.isdigit():
            return JsonResponse({"error": "Producto mayorista inválido"}, status=400)

        try:
            expected_price = Decimal(str(payload.get("expected_price", "")))
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({"error": "Precio de compra inválido"}, status=400)

        with transaction.atomic():
            partner = get_object_or_404(
                WholesalePartner.objects.select_for_update(),
                username__iexact=kwargs["username"],
                active=True,
            )
            existing = WholesalePurchase.objects.select_related(
                "account__platform",
                "account__plan",
                "plan__platform",
            ).filter(
                partner=partner,
                external_reference=reference,
            ).first()
            if existing:
                return JsonResponse(_wholesale_purchase_payload(existing, True))

            now = django_timezone.now()
            selected_account = None
            selected_profiles = []
            selected_plan = None
            publication = None

            if offer_type == "account":
                account = Count.objects.select_for_update().filter(
                    pk=int(offer_id),
                    active=True,
                    platform__active=True,
                    date_limit__gte=now,
                ).select_related("platform", "plan").first()
                if not account:
                    return JsonResponse({"error": "La cuenta ya no está disponible"}, status=409)
                profiles = list(
                    Profile.objects.select_for_update().filter(
                        count=account,
                    ).order_by("id")
                )
                profile_ids = [profile.id for profile in profiles]
                occupied = (
                    not profiles
                    or any(profile.saled for profile in profiles)
                    or Sale.objects.filter(
                        profile_id__in=profile_ids,
                        renovated=False,
                        cutted=False,
                        date_limit__gte=now,
                    ).exists()
                )
                if occupied:
                    return JsonResponse({"error": "La cuenta acaba de venderse"}, status=409)
                actual_price = account.wholesale_price
                selected_account = account
                selected_plan = account.plan
                selected_profiles = profiles
                if account.plan_id:
                    publication = WholesalePublication.objects.filter(
                        partner=partner,
                        plan=account.plan,
                    ).first()
            else:
                selected_plan = Plan.objects.select_for_update().filter(
                    pk=int(offer_id),
                    active=True,
                    platform__active=True,
                ).select_related("platform").first()
                if not selected_plan:
                    return JsonResponse({"error": "El plan ya no está disponible"}, status=409)
                publication = WholesalePublication.objects.filter(
                    partner=partner,
                    plan=selected_plan,
                ).select_related("created_by").first()
                if publication and not publication.active:
                    return JsonResponse(
                        {"error": "Este plan está oculto para el mayorista"},
                        status=409,
                    )
                actual_price = (
                    publication.wholesale_price
                    if publication
                    else selected_plan.wholesale_price
                )
                required_profiles = max(selected_plan.num_profiles, 1)
                candidate_profile_ids = list(
                    _available_profiles_for_plan(selected_plan, now)
                    .values_list("id", flat=True)[:max(required_profiles * 20, 100)]
                )
                candidate_count_ids = list(Profile.objects.filter(
                    id__in=candidate_profile_ids,
                ).values_list("count_id", flat=True).distinct().order_by("count_id"))
                list(Count.objects.select_for_update().filter(
                    id__in=candidate_count_ids,
                ).order_by("id"))
                locked_profiles = list(Profile.objects.select_for_update().filter(
                    id__in=candidate_profile_ids,
                    saled=False,
                    count__active=True,
                    count__date_limit__gte=now,
                ).select_related("count", "count__platform").order_by(
                    "-count__date_limit",
                    "id",
                ))
                for profile in locked_profiles:
                    if Sale.objects.filter(
                        profile=profile,
                        renovated=False,
                        cutted=False,
                        date_limit__gte=now,
                    ).exists():
                        continue
                    selected_profiles.append(profile)
                    if len(selected_profiles) == required_profiles:
                        break
                if len(selected_profiles) != required_profiles:
                    return JsonResponse(
                        {"error": "La última existencia de este plan acaba de venderse"},
                        status=409,
                    )
                account_ids = {profile.count_id for profile in selected_profiles}
                if len(account_ids) == 1:
                    selected_account = selected_profiles[0].count

            if actual_price <= 0:
                return JsonResponse(
                    {"error": "El precio de mayoreo todavía no está configurado"},
                    status=422,
                )
            if actual_price != expected_price:
                return JsonResponse(
                    {"error": "El precio cambió; actualiza el catálogo antes de comprar"},
                    status=409,
                )

            saler = (publication.created_by if publication else None) or User.objects.filter(
                username__iexact="epalacios10",
                is_superuser=True,
            ).first() or User.objects.filter(is_superuser=True).order_by("id").first()
            if not saler:
                return JsonResponse(
                    {"error": "No hay un administrador disponible para registrar la venta"},
                    status=503,
                )

            bill = Bill.objects.create(
                customer=partner.customer,
                saler=saler,
                total=actual_price,
            )
            for profile in selected_profiles:
                remaining_days = max(
                    (profile.count.date_limit.date() - django_timezone.localdate()).days,
                    1,
                )
                months = max((remaining_days + 29) // 30, 1)
                saler.sale_profile(
                    profile,
                    months,
                    profile.count.date_limit,
                    bill,
                )

            purchase = WholesalePurchase.objects.create(
                partner=partner,
                publication=publication,
                account=selected_account,
                plan=selected_plan,
                bill=bill,
                external_reference=reference,
                price=actual_price,
                profiles_count=len(selected_profiles),
                purchase_type=offer_type,
            )
            Action.action_register(
                saler,
                "Compra mayorista #" + str(purchase.id)
                + ": " + partner.username
                + " adquirió " + offer_key,
            )
            response_payload = _wholesale_purchase_payload(purchase)

        return JsonResponse(response_payload, status=201)


class WholesaleServicesApiView(View):
    """Private server-to-server view of a wholesaler's active purchases."""

    token_file = Path("/etc/wholesale-integration.token")

    def get(self, request, *args, **kwargs):
        authorized, error_response = _wholesale_api_authorized(request)
        if not authorized:
            return error_response

        partner = get_object_or_404(
            WholesalePartner.objects.select_related("customer"),
            username__iexact=kwargs["username"],
            active=True,
        )
        now = django_timezone.now()
        sales = list(Sale.objects.filter(
            bill__customer_id=partner.customer_id,
            renovated=False,
            cutted=False,
            date_limit__gte=now,
        ).select_related(
            "profile",
            "profile__count",
            "profile__count__platform",
            "profile__count__plan",
            "bill",
        ).order_by("date_limit", "profile__count__platform__name", "id"))

        account_ids = {sale.profile.count_id for sale in sales}
        account_capacities = dict(
            Profile.objects.filter(count_id__in=account_ids)
            .values("count_id")
            .annotate(total=Count_("id"))
            .values_list("count_id", "total")
        )

        services = []
        for sale in sales:
            profile = sale.profile
            account = profile.count
            days_remaining = max((sale.date_limit.date() - now.date()).days, 0)
            services.append({
                "control_sale_id": sale.id,
                "account_id": account.id,
                "account_capacity": account_capacities.get(account.id, 0),
                "platform": account.platform.name,
                "plan": account.plan.name if account.plan_id else "",
                "email": account.email,
                "password": account.password,
                "email_password": account.email_password,
                "link": account.link,
                "profile": profile.profile,
                "pin": profile.pin,
                "access_identifier": sale.access_identifier,
                "access_password": sale.access_password,
                "months": sale.months,
                "purchase_date": sale.date.isoformat(),
                "purchase_date_label": django_timezone.localtime(sale.date).strftime("%d/%m/%Y"),
                "expires_at": sale.date_limit.isoformat(),
                "expires_label": django_timezone.localtime(sale.date_limit).strftime("%d/%m/%Y"),
                "days_remaining": days_remaining,
            })

        return JsonResponse({
            "partner": {
                "username": partner.username,
                "customer_id": partner.customer_id,
                "customer_name": partner.customer.name,
            },
            "total": len(services),
            "generated_at": now.isoformat(),
            "services": services,
        })
