import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import Permission, PermissionsMixin, _user_has_perm
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from project.accounts.managers import UserManager


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
        help_text=_("Designates whether the user " "can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
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

    @property
    def terra_permissions_codenames(self):
        perms = self.functional_permissions
        return perms.values_list("codename", flat=True)

    def has_terra_perm(self, codename):
        if self.is_superuser:
            return True
        return _user_has_perm(self, f"{self._meta.app_label}.{codename}", None)


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
