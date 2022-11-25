from django import forms
from django.core.validators import URLValidator
from django.db.models.fields import TextField
from django.utils.translation import gettext_lazy as _


class LongURLField(TextField):
    default_validators = [URLValidator()]
    description = _("URL")

    def formfield(self, **kwargs):
        # As with CharField, this will cause URL validation to be performed
        # twice.
        defaults = {"form_class": forms.URLField}
        defaults.update(kwargs)
        return super().formfield(**defaults)
