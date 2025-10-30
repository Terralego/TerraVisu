from constance import config
from django import forms
from django.contrib.gis import forms as gis_forms
from django.core.mail import send_mail
from django.template.loader import get_template
from django.utils.translation import gettext_lazy as _

from project.terra_layer.models import (
    Declaration,
    ManagersMessage,
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

    information_template = None
    status_change_template = None
    information_subject = None
    status_change_subject = None

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

    def get_email_context(self, instance):
        return {
            "status": getattr(Status, instance.status).label,
            "administrators_message": self.cleaned_data.get("managers_message", ""),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }

    def get_recipients(self, instance):
        return [instance.user.email] if instance.user else []

    def save(self, commit=True):
        instance = super().save(commit)
        managers_message = self.cleaned_data.get("managers_message", "")
        context = self.get_email_context(instance)
        recipients = self.get_recipients(instance)

        # Message update without status change
        if (
            "managers_message" in self.changed_data
            and "status" not in self.changed_data
        ):
            self.send_email(
                self.information_template,
                self.information_subject,
                context,
                recipients,
            )
            self.create_managers_message(instance, managers_message)

        # Status change
        elif "status" in self.changed_data:
            self.send_email(
                self.status_change_template,
                self.status_change_subject,
                context,
                recipients,
            )
            self.create_status_change(instance, managers_message)

        return instance


class ReportAdminForm(EmailSendingForm):
    geom = gis_forms.PointField(widget=gis_forms.OSMWidget, required=False)

    information_template = "report_information.txt"
    status_change_template = "changed_report.txt"
    information_subject = _("Follow-up information about your report")
    status_change_subject = _("Your report has been updated")

    def get_email_context(self, instance):
        context = super().get_email_context(instance)
        context["layer"] = instance.layer.name
        return context

    def create_managers_message(self, instance, message):
        ManagersMessage.objects.create(message=message, report=instance)

    def create_status_change(self, instance, message):
        StatusChange.objects.create(
            message=message,
            report=instance,
            status_before=self.status_before,
            status_after=instance.status,
        )

    class Meta:
        model = Report
        fields = ["status", "managers_message"]


class DeclarationAdminForm(EmailSendingForm):
    geom = gis_forms.PointField(widget=gis_forms.OSMWidget)

    information_template = "declaration_information.txt"
    status_change_template = "changed_declaration.txt"
    information_subject = _("Follow-up information about your declaration")
    status_change_subject = _("Your declaration has been updated")

    def get_recipients(self, instance):
        """Declaration can have email directly or via user"""
        if instance.user:
            return [instance.user.email]
        return [instance.email] if instance.email else []

    def create_managers_message(self, instance, message):
        ManagersMessage.objects.create(message=message, declaration=instance)

    def create_status_change(self, instance, message):
        StatusChange.objects.create(
            message=message,
            declaration=instance,
            status_before=self.status_before,
            status_after=instance.status,
        )

    class Meta:
        model = Declaration
        fields = ["status", "managers_message"]
