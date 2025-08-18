from constance import config
from django import forms
from django.contrib.gis import forms as gis_forms
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from project.terra_layer.models import (
    Declaration,
    Report,
    Status,
)


class EmailSendingOnUpdateForm(gis_forms.ModelForm):
    administrators_message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
        required=False,
        help_text=_("Optional message to send user on status change"),
        label=_("Administrators message"),
    )

    def save(self, commit=True):
        is_update = self.instance.pk is not None
        instance = super().save(commit)
        recipients = self.get_recipients_emails(instance)
        if is_update and "status" in self.changed_data and recipients:
            context = self.get_email_context(instance)
            txt_template = get_template(self.mail_template)
            txt_message = txt_template.render(context=context)
            send_mail(
                self.mail_title,
                txt_message,
                None,
                recipient_list=recipients,
                fail_silently=True,
            )
        return instance


class ReportAdminForm(EmailSendingOnUpdateForm):
    mail_template = "changed_report.txt"
    mail_title = _("Your report has been updated")

    def get_recipients_emails(self, instance):
        return [instance.user.email] if instance.user else []

    def get_email_context(self, instance):
        context = {
            "layer": instance.layer.name,
            "status": getattr(Status, instance.status).label,
            "administrators_message": self.cleaned_data.get(
                "administrators_message", ""
            ),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        return context

    class Meta:
        model = Report
        fields = ["status", "administrators_message"]


class DeclarationAdminForm(EmailSendingOnUpdateForm):
    geom = gis_forms.PointField(widget=gis_forms.OSMWidget)
    mail_template = "changed_declaration.txt"
    mail_title = _("Your declaration has been updated")

    def get_recipients_emails(self, instance):
        return [instance.user.email] if instance.user else [instance.email] if instance.email else []

    def get_email_context(self, instance):
        context = {
            "status": getattr(Status, instance.status).label,
            "administrators_message": self.cleaned_data.get(
                "administrators_message", ""
            ),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        return context

    class Meta:
        model = Declaration
        fields = ["status", "administrators_message"]
