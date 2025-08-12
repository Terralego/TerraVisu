from constance import config
from django import forms
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from project.terra_layer.models import (
    Report,
    ReportStatus,
)


class ReportAdminForm(forms.ModelForm):
    administrators_message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
        required=False,
        help_text=_("Optional message to send user on status change"),
        label=_("Administrators message"),
    )

    class Meta:
        model = Report
        fields = ["status", "administrators_message"]

    def save(self, commit=True):
        is_update = self.instance.pk is not None
        instance = super().save(commit)
        if (
            is_update
            and "status" in self.changed_data
            and instance.user
            and instance.user.email
        ):
            context = {
                "layer": instance.layer.name,
                "status": getattr(ReportStatus, instance.status).label,
                "administrators_message": self.cleaned_data.get(
                    "administrators_message", ""
                ),
                "instance_title": config.INSTANCE_TITLE,
            }
            txt_template = get_template("changed_report.txt")
            txt_message = txt_template.render(context=context)
            # html_template = get_template("emails/sources_periodic_report/email.html")
            # html_message = html_template.render(context)
            send_mail(
                _("Your report has been updated"),
                txt_message,
                None,
                recipient_list=[instance.user.email],
                #    html_message=html_message,
                fail_silently=True,
            )
        return instance
