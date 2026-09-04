from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views import View #PARA VISTAS GENERICAS
from django.utils.decorators import method_decorator
from django.utils import timezone as django_timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import CreateView, ListView, UpdateView, DeleteView, TemplateView
from .models import Action, Customer, UserTwoFactorAuthData
from count.models import Sale, Bill, Profile, Price, WholesalePartner
from .forms import (
    CollaboratorUpdateForm,
    CustomerForm,
    PERMISSION_LABELS,
    PROTECTED_SUPERUSER_USERNAMES,
    UserForm,
)
from count.decorators import permissions_in_view, my_permissions
from django.contrib.auth.models import User
from .whatsapp_api import WHATSAPP_SEND_ERROR, send_document, send_message
from .ticket_pdf import build_customer_ticket_pdf, customer_ticket_filename
import datetime
from count.libraries import getDifference
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.db.models import Count as DbCount, Exists, OuterRef, Q
from django.db import transaction
from django.urls import reverse_lazy
from count.libraries import CalculateDateLimit
from user.whatsapp_api import message_renew
from .libraries import user_two_factor_auth_data_create
from django.core.exceptions import PermissionDenied, ValidationError
from django.contrib.auth import authenticate, views as auth_views
from custom_admin.forms import OTPForm
from django.contrib.auth import login, authenticate
from django.conf import settings
from .whatsapp_api import  message_expired


VIP_PURCHASE_WINDOW_DAYS = 90
VIP_MIN_PURCHASES = 4


def user_can_manage_wholesale_customers(user):
    return user.is_authenticated and (
        user.is_superuser or user.has_perm("count.manage_wholesale_customers")
    )


def normalize_customer_segment(segment):
    segment = (segment or "all").strip().casefold()
    allowed = {"all", "active", "inactive", "vip", "never", "wholesale"}
    return segment if segment in allowed else "all"


def active_customer_ids_queryset(now):
    return Sale.objects.filter(
        renovated=False,
        cutted=False,
        date_limit__gte=now,
    ).values("bill__customer_id")


def vip_customer_ids_queryset(now):
    vip_since = now - datetime.timedelta(days=VIP_PURCHASE_WINDOW_DAYS)
    return Bill.objects.filter(
        date__gte=vip_since,
        sale__isnull=False,
    ).values("customer_id").annotate(
        purchase_count=DbCount("id", distinct=True),
    ).filter(
        purchase_count__gte=VIP_MIN_PURCHASES,
    ).values("customer_id")


def customer_queryset_for_segment(segment, now=None):
    """Return only the selected customer segment without annotating every row."""
    now = now or django_timezone.now()
    segment = normalize_customer_segment(segment)
    customers = Customer.objects.all()
    # A disabled portal account is still a wholesale customer. Keep the
    # classification even when access to MyPlataforma is temporarily paused.
    wholesale_customer_ids = WholesalePartner.objects.values("customer_id")

    if segment == "wholesale":
        return customers.filter(id__in=wholesale_customer_ids)

    # Mayoristas are a separate category and do not count as normal or VIP.
    customers = customers.exclude(id__in=wholesale_customer_ids)

    if segment == "active":
        return customers.filter(
            active=True,
            id__in=active_customer_ids_queryset(now),
        )
    if segment == "inactive":
        active_customer_ids = active_customer_ids_queryset(now)
        return customers.filter(
            Q(active=False) | ~Q(id__in=active_customer_ids)
        )
    if segment == "vip":
        return customers.filter(id__in=vip_customer_ids_queryset(now))
    if segment == "never":
        customers_with_sales = Bill.objects.filter(
            sale__isnull=False,
        ).values("customer_id")
        return customers.exclude(id__in=customers_with_sales)
    return customers


def context_app(request):
    permissions = my_permissions(request.user)
    context = {}
    if request.user.is_authenticated:
            context['otp_active'] = settings.OPT_ACTIVE
            context['permissions'] = permissions
    return context


class MyLoginView(auth_views.LoginView):

    tamplate_name = 'user/login.html'
    def get(self, request):

        return render(self.request, self.tamplate_name)
    def post(self, request):

        user = authenticate(request=self.request, username=self.request.POST['username'],
                            password=self.request.POST['password'])
        if user :
            if user.is_active:

                two_factor_auth_data = UserTwoFactorAuthData.objects.filter(user__username=request.POST.get('username')).first()
                self.request.session['username'] = str(user.username)
                if two_factor_auth_data:
                    return redirect('confirm-2fa')
                else:
                    return redirect('setup-2fa')

        return render(self.request, self.tamplate_name)



class SetupTwoFactorAuthView(TemplateView):

    template_name = "2fa/setup_2fa.html"

    def post(self, request):

        username = self.request.session['username']
        user = User.objects.get(username= username)
        context = {}
        try:
            two_factor_auth_data = user_two_factor_auth_data_create(user=user)
            context["otp_secret"] = two_factor_auth_data.otp_secret
            context["qr_code"] = two_factor_auth_data.generate_qr_code(name=user.username)
        except ValidationError as exc:
            context["form_errors"] = exc.messages

        return self.render_to_response(context)


class ConfirmTwoFactorAuthView(View):

    template_name = "2fa/confirm_2fa.html"
    success_url = reverse_lazy("index")
    form_class = OTPForm

    def get(self, request, *args, **kwargs):

        form = self.form_class
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):

        username = self.request.session['username']
        user = User.objects.get(username= username)
        form = OTPForm(request.POST)
        form.user = user
        if form.is_valid():
            form.two_factor_auth_data.rotate_session_identifier()
            self.request.session['2fa_token'] = str(form.two_factor_auth_data.session_identifier)
            login(self.request, user, backend = 'django.contrib.auth.backends.ModelBackend')
            return redirect("index")
        return render(request, self.template_name, {"form": form})



@method_decorator(login_required, name='dispatch')
class IndexView(View):

    def get(self, request, *args, **kwargs):
        return redirect('dashboard')

@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class AddCustomerView(CreateView):

    form_class = CustomerForm
    template_name = "user/add.html"

    def form_valid(self, form):

        user = form.save()
        return redirect('sale-count', user.id)


@method_decorator(permissions_in_view, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UpdateCustomerView(UpdateView):

    model = Customer
    fields = ["name", "phone",  "active"]
    template_name = "user/update_customer.html"
    success_url = "/user/list-customer"

    def post(self, request, *args, **kwargs):
        # A service modal must never be interpreted as a customer edit. If a
        # browser falls back to a native date-form submit, keep the customer
        # untouched and reload its existing data.
        if 'name' not in request.POST or 'phone' not in request.POST:
            return redirect(request.path)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UpdateCustomerView, self).get_context_data(**kwargs)
        current_sales = Sale.objects.filter(
            bill__customer_id=self.kwargs['pk'],
            cutted=False,
        ).select_related(
            "bill__customer",
            "profile__count__platform",
            "profile__count__plan",
        ).order_by("-id")

        # Keep only the newest non-cut sale for each profile. This preserves the
        # current behavior while avoiding one additional query per profile.
        seen_profiles = set()
        sales = []
        for sale in current_sales:
            if sale.profile_id in seen_profiles:
                continue
            seen_profiles.add(sale.profile_id)
            sales.append(sale)

        now = django_timezone.now()
        for sale in sales:
            if sale.date_limit:
                rest_days = getDifference(now, sale.date_limit, 'days')
                if rest_days < 0:
                    sale.rest_days = "Vencida"
                else:
                    sale.rest_days = rest_days
            else:
                sale.rest_days = "Sin fecha"

        sales.sort(key=lambda sale: (
            sale.profile.count.platform.name.casefold(),
            sale.profile.count.plan.name.casefold() if sale.profile.count.plan else "",
            sale.profile.profile,
        ))
        ctx['sales'] = sales
        ctx['service_count'] = len(sales)
        ctx['pk'] = self.kwargs['pk']
        return ctx


@method_decorator(login_required, name='dispatch')
class CustomerHistoryView(ListView):

    model = Sale
    template_name = "user/customer_history.html"
    context_object_name = "sales"

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.filter(
            bill__customer=self.customer,
        ).select_related(
            "bill__saler",
            "profile__count__platform",
        ).order_by("-date", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = django_timezone.now()
        sales = context["sales"]

        for sale in sales:
            if sale.cutted:
                sale.history_status = "Cortado"
                sale.history_status_class = "danger"
            elif sale.renovated:
                sale.history_status = "Renovado"
                sale.history_status_class = "info"
            elif sale.date_limit and sale.date_limit < now:
                sale.history_status = "Vencido"
                sale.history_status_class = "warning"
            else:
                sale.history_status = "Activo"
                sale.history_status_class = "success"

        first_sale = self.model.objects.filter(
            bill__customer=self.customer,
        ).order_by("date").first()
        context["customer"] = self.customer
        context["customer_since"] = first_sale.date if first_sale else None
        context["purchase_count"] = Bill.objects.filter(
            customer=self.customer,
            sale__isnull=False,
        ).values("id").distinct().count()
        context["service_count"] = len(sales)
        context["active_count"] = sum(
            1 for sale in sales if sale.history_status == "Activo"
        )
        return context


def customer_ticket_services(customer):
    """Return current services with their original customer contract date."""
    services = list(
        Sale.objects.filter(
            bill__customer=customer,
            renovated=False,
            cutted=False,
            date_limit__gte=django_timezone.now(),
        ).select_related(
            "bill__customer",
            "profile__count__platform",
            "profile__count__plan",
        ).order_by("date_limit", "profile__count__platform__name", "profile__profile")
    )
    for service in services:
        service.contract_date = Sale.objects.filter(
            bill__customer=customer,
            profile_id=service.profile_id,
        ).order_by("date", "id").values_list("date", flat=True).first()
    return services


def customer_ticket_message(customer, services):
    lines = [
        "🎫 *EL GAMER MX*",
        "_LA REVOLUCIÓN DEL ENTRETENIMIENTO_",
        "",
        f"Hola, {customer.name}.",
        "Este es tu resumen de servicios contratados:",
        "",
    ]
    for index, service in enumerate(services, start=1):
        plan = service.profile.count.plan
        plan_name = plan.name if plan else "Servicio individual"
        lines.extend([
            f"{index}. *{service.profile.count.platform.name}*",
            f"Plan: {plan_name}",
            f"Perfil: {service.profile.profile}",
            f"Contratado: {django_timezone.localtime(service.contract_date).strftime('%d/%m/%Y')}",
            f"Vencimiento: {django_timezone.localtime(service.date_limit).strftime('%d/%m/%Y')}",
            "",
        ])
    lines.extend([
        "Este ticket es informativo y no contiene contraseñas ni claves de acceso.",
        "Gracias por tu preferencia.",
    ])
    return "\n".join(lines)


def customer_ticket_context(customer):
    services = customer_ticket_services(customer)
    first_contract = Sale.objects.filter(
        bill__customer=customer,
    ).order_by("date", "id").values_list("date", flat=True).first()
    issued_at = django_timezone.localtime()
    return {
        "customer": customer,
        "services": services,
        "first_contract": first_contract,
        "issued_at": issued_at,
        "ticket_folio": f"EGM-{customer.pk:05d}-{issued_at:%Y%m%d}",
    }


@method_decorator(login_required, name='dispatch')
class CustomerTicketView(View):

    def get(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=pk)
        return render(
            request,
            "user/customer_ticket.html",
            customer_ticket_context(customer),
        )


@method_decorator(login_required, name='dispatch')
class CustomerTicketPdfView(View):

    def get(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=pk)
        context = customer_ticket_context(customer)
        pdf = build_customer_ticket_pdf(**context)
        filename = customer_ticket_filename(customer, context["issued_at"])
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


@method_decorator(login_required, name='dispatch')
class SendCustomerTicketView(View):

    def post(self, request, pk, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=pk)
        services = customer_ticket_services(customer)
        context = customer_ticket_context(customer)
        pdf = build_customer_ticket_pdf(**context)
        filename = customer_ticket_filename(customer, context["issued_at"])
        result = send_document(
            customer.phone.as_e164,
            pdf,
            filename,
            "Tu ticket de servicios contratados con El Gamer MX.",
        )
        if result == WHATSAPP_SEND_ERROR:
            return HttpResponse(WHATSAPP_SEND_ERROR, status=502)
        return HttpResponse("Ticket PDF enviado correctamente por WhatsApp.")


@method_decorator(login_required, name='dispatch')
class CustomerModulesView(TemplateView):

    template_name = "user/customer_modules.html"


@method_decorator(login_required, name='dispatch')
class CustomerListView(ListView):

    model = Customer
    template_name = "user/list.html"

    def get_queryset(self, *args, **kwargs):
        # DataTables loads the rows over AJAX. Avoid querying all customers
        # while rendering the page shell.
        return self.model.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        segment = normalize_customer_segment(self.request.GET.get("segment"))
        if segment == "wholesale" and not user_can_manage_wholesale_customers(self.request.user):
            raise PermissionDenied
        segment_copy = {
            "all": (
                "Todos los clientes",
                "Clientes registrados en el sistema.",
            ),
            "active": (
                "Clientes activos",
                "Tienen al menos un servicio vigente y sin cortar.",
            ),
            "inactive": (
                "Clientes inactivos",
                "No tienen servicios vigentes.",
            ),
            "vip": (
                "Clientes VIP",
                f"Realizaron {VIP_MIN_PURCHASES} o más compras en los últimos {VIP_PURCHASE_WINDOW_DAYS} días.",
            ),
            "never": (
                "Clientes sin compras",
                "Están registrados sin ninguna venta y forman parte de los inactivos.",
            ),
            "wholesale": (
                "Clientes mayoristas",
                "Compran cuentas o planes para dividirlos y venderlos a sus propios clientes.",
            ),
        }
        segment_label, segment_description = segment_copy[segment]

        context.update({
            "customer_segment": segment,
            "customer_segment_label": segment_label,
            "customer_segment_description": segment_description,
        })
        return context



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class AddUserView(CreateView):

    form_class = UserForm
    template_name = 'user/add_user.html'

    def form_valid(self, form):
        collaborator = form.save()
        Action.action_register(
            self.request.user,
            'Colaborador creado: usuario = ' + collaborator.username,
        )
        return redirect('list-user')

    def get_context_data(self, **kwargs):

        ctx = super(AddUserView, self).get_context_data(**kwargs)
        ctx['form'] = self.form_class(self.request.POST or None)
        return ctx



@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class UserListView(ListView):

    model = User
    template_name = "user/user_list.html"

    def get_queryset(self, *args, **kwargs):
        segment = (
            self.request.GET.get('segment')
            or self.request.GET.get('status')
            or 'all'
        ).strip().casefold()
        if segment not in {'all', 'superadmins', 'active', 'inactive'}:
            segment = 'all'
        users = self.model.objects.prefetch_related('user_permissions').order_by('username')
        if segment == 'superadmins':
            users = users.filter(is_superuser=True)
        elif segment == 'active':
            users = users.filter(is_active=True)
        elif segment == 'inactive':
            users = users.filter(is_active=False)
        self.collaborator_segment = segment
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_users = self.model.objects.all()
        for collaborator in context['object_list']:
            collaborator.permission_labels = [
                PERMISSION_LABELS.get(permission.codename, permission.name)
                for permission in collaborator.user_permissions.all()
            ]
            collaborator.permission_count = len(collaborator.permission_labels)
            collaborator.is_protected_superuser = (
                collaborator.username.casefold() in PROTECTED_SUPERUSER_USERNAMES
            )
        context.update({
            'collaborator_segment': getattr(self, 'collaborator_segment', 'all'),
            'users_total': all_users.count(),
            'users_active': all_users.filter(is_active=True).count(),
            'users_inactive': all_users.filter(is_active=False).count(),
            'users_superadmins': all_users.filter(is_superuser=True).count(),
            'protected_superuser_usernames': PROTECTED_SUPERUSER_USERNAMES,
        })
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class UpdateUserView(UpdateView):

    model = User
    form_class = CollaboratorUpdateForm
    template_name = 'user/update_user.html'
    success_url = reverse_lazy('list-user')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.username.casefold() in PROTECTED_SUPERUSER_USERNAMES:
            self.object.is_superuser = True
            self.object.is_staff = True
            self.object.is_active = True
            self.object.save(update_fields=['is_superuser', 'is_staff', 'is_active'])
        Action.action_register(
            self.request.user,
            'Colaborador actualizado: usuario = ' + self.object.username,
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['protected_account'] = (
            self.object.username.casefold() in PROTECTED_SUPERUSER_USERNAMES
        )
        context['protected_account_username'] = self.object.username
        return context


@method_decorator(login_required, name='dispatch')
@method_decorator(permissions_in_view, name='dispatch')
class ToggleUserStatusView(View):

    def post(self, request, *args, **kwargs):
        collaborator = get_object_or_404(User, pk=kwargs['pk'])
        if collaborator.username.casefold() in PROTECTED_SUPERUSER_USERNAMES:
            raise PermissionDenied

        collaborator.is_active = not collaborator.is_active
        collaborator.save(update_fields=['is_active'])
        status_label = 'reactivado' if collaborator.is_active else 'dado de baja'
        Action.action_register(
            request.user,
            'Colaborador ' + status_label + ': usuario = ' + collaborator.username,
        )
        return redirect('list-user')


class CustomerJson(BaseDatatableView):

    columns = ['id', 'name', 'phone', 'status', 'actions']
    order_columns = ['id', 'name', 'phone', '', '']
    model = Customer
    #max_display_length = 500

    def get_initial_queryset(self):
        segment = normalize_customer_segment(self.request.GET.get("segment"))
        if segment == "wholesale" and not user_can_manage_wholesale_customers(self.request.user):
            raise PermissionDenied
        return customer_queryset_for_segment(segment)


    def render_column(self, row, column):
        return super(CustomerJson, self).render_column(row, column)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            q = Q(phone__icontains=search) | Q(name__icontains=search)
            qs = qs.filter(q)

        return qs

    def prepare_results(self, qs):

        permissions = my_permissions(self.request.user)
        json_data = []
        can_change = '*' in permissions or 'change_customer' in permissions
        can_delete = '*' in permissions or 'delete_customer' in permissions

        # Only calculate badges for the rows displayed on this DataTables page.
        # This keeps the list fast even with thousands of registered customers.
        customers = list(qs)
        customer_ids = [customer.id for customer in customers]
        now = django_timezone.now()
        vip_since = now - datetime.timedelta(days=VIP_PURCHASE_WINDOW_DAYS)
        active_customer_ids = set(Sale.objects.filter(
            bill__customer_id__in=customer_ids,
            renovated=False,
            cutted=False,
            date_limit__gte=now,
        ).values_list("bill__customer_id", flat=True).distinct())
        recent_purchase_counts = dict(Bill.objects.filter(
            customer_id__in=customer_ids,
            date__gte=vip_since,
            sale__isnull=False,
        ).values("customer_id").annotate(
            purchase_count=DbCount("id", distinct=True),
        ).values_list("customer_id", "purchase_count"))
        customers_with_sales = set(Bill.objects.filter(
            customer_id__in=customer_ids,
            sale__isnull=False,
        ).values_list("customer_id", flat=True).distinct())
        wholesale_customer_ids = set(WholesalePartner.objects.filter(
            customer_id__in=customer_ids,
        ).values_list("customer_id", flat=True))

        for item in customers:
            has_active_service = item.active and item.id in active_customer_ids
            recent_purchase_count = recent_purchase_counts.get(item.id, 0)
            has_purchases = item.id in customers_with_sales
            status_badges = [
                '<span class="customer-status status-active"><i class="mdi mdi-check-circle"></i>Activo</span>'
                if has_active_service else
                '<span class="customer-status status-inactive"><i class="mdi mdi-pause-circle"></i>Inactivo</span>'
            ]
            if item.id in wholesale_customer_ids:
                status_badges.append(
                    '<span class="customer-status status-wholesale"><i class="mdi mdi-store"></i>Mayorista</span>'
                )
            if (
                item.id not in wholesale_customer_ids
                and recent_purchase_count >= VIP_MIN_PURCHASES
            ):
                status_badges.append(
                    '<span class="customer-status status-vip"><i class="mdi mdi-crown"></i>VIP</span>'
                )
            if item.id not in wholesale_customer_ids and not has_purchases:
                status_badges.append(
                    '<span class="customer-status status-never"><i class="mdi mdi-cart-off"></i>Sin compras</span>'
                )

            actions = [
                f'<a href="/count/sale/{item.id}" class="btn btn-primary btn-icon-text"><i class="mdi mdi-square-inc-cash"></i>Vender</a>'
            ]
            if can_change:
                actions.append(
                    f'<a href="/user/update-customer/{item.id}" class="btn btn-info btn-icon-text"><i class="mdi mdi-information"></i>Planes</a>'
                )
            actions.extend([
                f'<a href="/user/customer-ticket/{item.id}" class="btn btn-warning btn-icon-text"><i class="mdi mdi-ticket-confirmation"></i>Ticket</a>',
                f'<a href="/user/customer-history/{item.id}" class="btn btn-secondary btn-icon-text"><i class="mdi mdi-history"></i>Historial</a>',
            ])
            if can_delete:
                actions.append(
                    f'<a href="/user/delete-customer/{item.id}" class="btn btn-danger btn-icon-text"><i class="mdi mdi-delete-forever"></i>Eliminar</a>'
                )

            actions_html = (
                '<div class="customer-actions" role="group" aria-label="Acciones del cliente">'
                + ''.join(actions)
                + '</div>'
            )
            json_data.append([
                item.id,
                item.name,
                str(item.phone),
                '<div class="customer-statuses">' + ''.join(status_badges) + '</div>',
                actions_html,
            ])

        return json_data


class CustomerDeleteView(DeleteView):

    model = Customer
    success_url = reverse_lazy("list-customer")


@method_decorator(login_required, name='dispatch')

class ProfileNextExpiredView(ListView):

    model = Sale
    template_name = "user/list-to-expire.html"
    allowed_days = {0, 1, 2, 3}

    def get_selected_days(self):
        try:
            selected_days = int(self.request.GET.get("days", 3))
        except (TypeError, ValueError):
            selected_days = 3
        return selected_days if selected_days in self.allowed_days else 3

    def get_queryset(self,  *args, **kwargs):
        selected_days = self.get_selected_days()
        target_date = django_timezone.localdate() + datetime.timedelta(days=selected_days)
        sales_to_expires = self.model.objects.filter(
            profile__saled=True,
            renovated=False,
            cutted=False,
            date_limit__date=target_date,
        ).select_related(
            "bill__customer",
            "profile__count__platform",
            "profile__count__plan",
        ).order_by('date_limit')
        for sale in sales_to_expires:
            sale.rest_days = selected_days
        return sales_to_expires

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_days = self.get_selected_days()
        context.update({
            "expiring_days": selected_days,
            "expiring_target_date": django_timezone.localdate() + datetime.timedelta(days=selected_days),
            "expiring_is_today": selected_days == 0,
        })
        return context


    def post(self, request, *args, **kwargs):


        counts = {}
        renewed_any = False
        for item in request.POST:
            if item.isnumeric():
                if request.POST[item] == 'on':
                    with transaction.atomic():
                        sale = Sale.close_open_history_for_renewal(item)
                        if sale is None:
                            continue
                        bill = Bill.objects.create(customer_id=sale.bill.customer.id, saler=request.user, total=0)
                        date_limit = CalculateDateLimit(sale.date_limit, int(request.POST['months']))
                        renewed_sale = request.user.sale_profile(
                            sale.profile,
                            int(request.POST['months']),
                            date_limit,
                            bill,
                            device_mac=sale.device_mac,
                            device_key=sale.device_key,
                        )
                        subtotal = Price.objects.filter(platform=sale.profile.count.platform, num_profiles=1).first()
                        if subtotal:
                            bill.total = subtotal.price * int(request.POST['months'])
                            bill.save(update_fields=["total"])
                    renewed_any = True
                    message_renew(sale.profile, bill.customer, date_limit, renewed_sale)

        if not renewed_any:
            messages.warning(request, "No se encontró un servicio vigente para renovar.")
        return redirect('bill-list')


class SendMessageProfileNextExpiredView(View):

    model = Sale

    def get(self,  *args, **kwargs):

        days = kwargs['days']
        sign = kwargs['sign']
        date_init = django_timezone.now()
        if sign == "positive":
            date_finish = django_timezone.now() + datetime.timedelta(days=days)
        else:
            date_finish = django_timezone.now() - datetime.timedelta(days=days)
        date_init = date_init.strftime("%Y-%m-%d")
        date_finish = date_finish.strftime("%Y-%m-%d")
        sales_to_expires = self.model.objects.filter(profile__saled=True, renovated=False, cutted=False, date_limit=date_finish).order_by('date_limit')
        data=[]
        for sale in sales_to_expires:
            rest_days = getDifference(sale.date_limit.date(), django_timezone.localdate(), 'days')
            sale.rest_days = -rest_days
            count_data = {
                'platform': sale.profile.count.platform.name,
                'plan': sale.profile.count.plan.name if sale.profile.count.plan else '',
                'name': sale.bill.customer.name,
                "phone": sale.bill.customer.phone.as_e164,
                'email': sale.access_identifier,
                'password': sale.access_password,
                'days': str(sale.rest_days)
            }
            data.append(count_data)
            message_expired(count_data)

        return JsonResponse({"status":200, "response":data })




@method_decorator(login_required, name='dispatch')
class ProfileExpiredView(ListView):

    model = Sale
    template_name = "user/list-expired.html"

    def get_queryset(self,  *args, **kwargs):
        date_finish = django_timezone.localdate()
        active_replacement = self.model.objects.filter(
            bill__customer_id=OuterRef("bill__customer_id"),
            profile_id=OuterRef("profile_id"),
            renovated=False,
            cutted=False,
            date_limit__date__gte=date_finish,
        ).exclude(pk=OuterRef("pk"))
        sale_expired = self.model.objects.filter(
            profile__saled=True,
            renovated=False,
            cutted=False,
            date_limit__date__lt=date_finish,
        ).annotate(
            has_active_replacement=Exists(active_replacement),
        ).filter(
            has_active_replacement=False,
        ).select_related(
            "bill__customer",
            "profile__count__platform",
            "profile__count__plan",
        ).order_by('-date_limit')
        for sale in sale_expired:
            rest_days = getDifference(sale.date_limit.date(), django_timezone.localdate(), 'days')
            sale.rest_days = -rest_days
        return sale_expired

    def get_context_data(self,**kwargs):
        context = super(ProfileExpiredView,self).get_context_data(**kwargs)
        context['now'] = django_timezone.localtime()
        context['expired_reference_date'] = django_timezone.localdate()
        return context

class SendMessagesWhatsappApi(View) :

    def get(self, request, *args, **kwargs):
        counts = []
        payload = Customer.get_phones_for_messages( Sale)
        for  data in payload:
            message = f"Hola, {payload[data]['name']} tu servicio  {payload[data]['platform']}\n" \
                      f" 👤USUARIO: {payload[data]['email']} \n" \
                      f" 🔐CONTRASEÑA: {payload[data]['password']}  \n" \
                      f" {payload[data]['days']}  \n" \
                      f" Avísame si lo vas a renovar. Muchas gracias 🙂"
            counts.append([payload[data]['name'], payload[data]['email']])
            send_message(payload[data]['phone'], message)
        return JsonResponse(payload)
