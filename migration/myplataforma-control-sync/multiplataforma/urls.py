from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from multiplataforma import views


urlpatterns = [
    path("password_reset", views.PasswordResetRequest.as_view(), name="password_reset_own"),
    path(
        "password_reset/done-owner/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done_own.html"
        ),
        name="password_reset_done_own",
    ),
    path(
        "reset_own/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm_own.html"
        ),
        name="password_reset_confirm_own",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete_own.html"
        ),
        name="password_reset_complete",
    ),
    path("", views.IndexView, name="index"),
    path("portal/<slug:section>/", views.PortalSectionView, name="portal-section"),
    path("mayoristas/", views.WholesalePartnersView, name="wholesale-partners"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)
