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
    StatusChange,
)


class EmailSendingForm(gis_forms.ModelForm):
    managers_message = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 4, "cols": 60}),
        required=False,
        help_text=_("Optional message to send user on status change"),
        label=_("Managers message"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_before = self.instance.status

    def send_email(self, template_name, mail_title, context, recipients):
        if recipients:
            txt_template = get_template(template_name)
            txt_message = txt_template.render(context=context)
            send_mail(
                mail_title,
                txt_message,
                None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=recipients,
                fail_silently=True,
            )


class ReportAdminForm(EmailSendingForm):
    geom = gis_forms.PointField(widget=gis_forms.OSMWidget)

    def get_email_context(self, instance):
        context = {
            "layer": instance.layer.name,
            "status": getattr(Status, instance.status).label,
            "managers_message": self.cleaned_data.get("managers_message", ""),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        return context

    def save(self, commit=True):
        is_update = self.instance.pk is not None
        instance = super().save(commit)
        if is_update and "status" in self.changed_data:
            recipients = [instance.user.email] if instance.user else []
            context = self.get_email_context(instance)
            self.send_email(
                "changed_report.txt",
                _("Your report has been updated"),
                context,
                recipients,
            )
        managers_message = self.cleaned_data.get("managers_message", "")
        StatusChange.objects.create(
            message=managers_message,
            report=instance,
            status_before=self.status_before,
            status_after=instance.status,
        )
        return instance

    class Meta:
        model = Report
        fields = ["status", "managers_message"]


class DeclarationAdminForm(EmailSendingForm):
    geom = gis_forms.PointField(widget=gis_forms.OSMWidget)

    def get_email_context(self, instance):
        context = {
            "status": getattr(Status, instance.status).label,
            "managers_message": self.cleaned_data.get("managers_message", ""),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        return context

    def save(self, commit=True):
        is_update = self.instance.pk is not None
        instance = super().save(commit)
        if is_update and "status" in self.changed_data:
            recipients = (
                [instance.user.email]
                if instance.user
                else [instance.email]
                if instance.email
                else []
            )
            context = self.get_email_context(instance)
            self.send_email(
                "changed_declaration.txt",
                _("Your declaration has been updated"),
                context,
                recipients,
            )
            managers_message = self.cleaned_data.get("managers_message", "")
            StatusChange.objects.create(
                message=managers_message,
                declaration=instance,
                status_before=self.status_before,
                status_after=instance.status,
            )
        return instance

    class Meta:
        model = Declaration
        fields = ["status", "managers_message"]
