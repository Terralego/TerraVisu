from constance import config
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.formats import date_format
from django.utils.translation import gettext as _

from project.accounts.models import User
from project.terra_layer.models import Report, Status, StatusChange


class Command(BaseCommand):
    """Management command to send monthly reports summary emails to managers."""

    help = (
        "Send monthly summary email with reports created and updated in the last month"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--language",
            type=str,
            default="en",
            help="Language for the summary email",
        )

    def get_report_admin_url(self, report):
        """Generate admin URL for a report."""
        server_name = settings.ALLOWED_HOSTS[-1]
        report_admin_url = reverse(
            "config_site:terra_layer_report_change",
            args=(report.pk,),
        )
        return f"https://{server_name}{report_admin_url}"

    def get_status_distribution(self, queryset, language):
        """Get distribution of report statuses for a queryset."""
        distribution = {}
        with translation.override(language):
            for status_code, status_label in Status.choices:
                distribution[status_label] = queryset.filter(status=status_code).count()
        return distribution

    def get_display_name(self, layer):
        """Get display name for a layer."""
        return layer.name or f"{_('Layer')} {layer.pk}"

    def get_feature_display(self, report):
        """Get display value for a feature."""
        feature_main_field = getattr(report.layer.main_field, "name", None)
        if feature_main_field:
            return report.feature.properties.get(feature_main_field, report.feature.pk)
        return str(report.feature.pk)

    def group_reports_by_layer_and_feature(
        self, reports, language, date_field="created_at"
    ):
        """Group reports by layer and feature for email template."""
        grouped_reports = {}

        for report in reports:
            layer_display = self.get_display_name(report.layer)
            feature_display = self.get_feature_display(report)

            # Initialize nested dictionaries
            if layer_display not in grouped_reports:
                grouped_reports[layer_display] = {}
            if feature_display not in grouped_reports[layer_display]:
                grouped_reports[layer_display][feature_display] = []

            # Get status display in the specified language
            with translation.override(language):
                status_display = report.get_status_display()

            # Determine the date to use
            report_date = getattr(report, date_field)

            report_data = {
                "id": report.pk,
                date_field: report_date,
                "status": status_display,
                "url": self.get_report_admin_url(report),
            }
            grouped_reports[layer_display][feature_display].append(report_data)

        return grouped_reports

    def get_reports_created_last_month(self, last_month):
        """Get reports created in the last month."""
        return (
            Report.objects.filter(
                created_at__month=last_month.month,
                created_at__year=last_month.year,
            )
            .select_related("layer", "layer__main_field")
            .order_by("layer", "feature")
        )

    def get_reports_updated_last_month(self, last_month):
        """Get reports updated in the last month with their latest status changes."""
        latest_status_updates = (
            StatusChange.objects.filter(
                report__isnull=False,
                updated_at__month=last_month.month,
                updated_at__year=last_month.year,
            )
            .select_related("report", "report__layer", "report__layer__main_field")
            .order_by("report", "-updated_at")
            .distinct("report")
        )

        # Attach the update date to each report for easier processing
        reports = []
        for status_change in latest_status_updates:
            report = status_change.report
            report.last_updated_at = status_change.updated_at
            reports.append(report)

        return reports

    def get_manager_emails(self):
        """Get email addresses of all report managers."""
        return list(
            User.objects.filter(is_report_manager=True).values_list("email", flat=True)
        )

    def prepare_email_context(
        self, last_month, created_reports, updated_reports, all_reports, language
    ):
        """Prepare context data for the email template."""
        with translation.override(language):
            last_month_display = date_format(last_month, "F")

        return {
            "last_month": last_month_display,
            "created_count": len(created_reports),
            "updated_count": len(updated_reports),
            "total_count": all_reports.count(),
            "grouped_created": self.group_reports_by_layer_and_feature(
                created_reports, language, "created_at"
            ),
            "grouped_updated": self.group_reports_by_layer_and_feature(
                updated_reports, language, "last_updated_at"
            ),
            "instance_title": config.INSTANCE_TITLE,
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
            "monthly_distribution": self.get_status_distribution(
                Report.objects.filter(
                    created_at__month=last_month.month,
                    created_at__year=last_month.year,
                ),
                language,
            ),
            "total_distribution": self.get_status_distribution(all_reports, language),
        }

    def send_summary_email(self, context, managers_emails, language):
        """Send the summary email to managers."""
        if not managers_emails:
            return 0

        with translation.override(language):
            subject_prefix = _('Monthly reports summary')
            full_subject = f"{subject_prefix} - {config.INSTANCE_TITLE}"
            txt_template = get_template("reports_summary.txt")
            message = txt_template.render(context=context)

        return send_mail(
            subject=full_subject,
            message=message,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=managers_emails,
            fail_silently=True,
        )

    def handle(self, *args, **options):
        """Main command handler."""
        language = options["language"]

        # Calculate last month
        last_month = timezone.now() - relativedelta(months=1)

        # Get data
        all_reports = Report.objects.all()
        created_reports = list(self.get_reports_created_last_month(last_month))
        updated_reports = self.get_reports_updated_last_month(last_month)
        managers_emails = self.get_manager_emails()

        # Prepare email context
        context = self.prepare_email_context(
            last_month=last_month,
            created_reports=created_reports,
            updated_reports=updated_reports,
            all_reports=all_reports,
            language=language,
        )

        # Send emails
        sent_emails = self.send_summary_email(context, managers_emails, language)

        # Output result
        self.stdout.write(
            self.style.SUCCESS(f"Successfully sent {sent_emails} summary emails.")
        )

        if not managers_emails:
            self.stdout.write(
                self.style.WARNING("No report managers found. No emails sent.")
            )
