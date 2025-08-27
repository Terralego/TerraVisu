import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Permission, PermissionsMixin, _user_has_perm
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from project.accounts.managers import UserManager
from project.accounts.tokens import generate_token


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    uuid = models.CharField(
        _("Unique identifier"), max_length=255, default=uuid.uuid4, unique=True
    )
    email = models.EmailField(_("email address"), unique=True)
    properties = models.JSONField(default=dict, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    is_report_manager = models.BooleanField(
        _("Report manager"),
        default=False,
        help_text=_(
            "Designates whether this user needs to receive email notifications "
            "about incoming reports, and monthly reports summary."
        ),
    )
    is_declaration_manager = models.BooleanField(
        _("Declaration manager"),
        default=False,
        help_text=_(
            "Designates whether this user needs to receive email notifications "
            "about incoming declarations, and monthly declarations summary."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def functional_permissions(self):
        if self.is_active:
            perms = FunctionalPermission.objects.all()

            if not self.is_superuser:
                perms = perms.filter(
                    Q(pk__in=self.user_permissions.all())
                    | Q(group__in=self.groups.all())
                )
        else:
            perms = FunctionalPermission.objects.none()
        return perms

    def has_terra_perm(self, codename):
        if self.is_superuser:
            return True
        return _user_has_perm(self, f"{self._meta.app_label}.{codename}", None)

    def get_jwt_token(self):
        payload = JSONWebTokenAuthentication.jwt_create_payload(self)
        return JSONWebTokenAuthentication.jwt_encode_payload(payload)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")


class FunctionalPermission(Permission):
    original = models.OneToOneField(
        Permission, on_delete=models.CASCADE, parent_link=True
    )
    module = models.CharField(blank=True, max_length=50)

    @property
    def name_translated(self):
        return _(self.name)

    def __str__(self):
        return f"{self.module}: {self.original.name} ({self.codename})"

    class Meta:
        verbose_name = _("Functional permission")
        verbose_name_plural = _("Functional permissions")


class PermanentAccessToken(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    token = models.CharField(
        max_length=255, unique=True, default=generate_token, blank=True, editable=False
    )
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Permanent access token")
        verbose_name_plural = _("Permanent access tokens")

    def __str__(self):
        return f"{self.user} - {self.token}"
