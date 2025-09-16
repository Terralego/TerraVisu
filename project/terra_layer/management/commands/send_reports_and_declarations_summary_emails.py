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
from project.terra_layer.models import Declaration, Report, Status, StatusChange


class BaseSummaryHandler:
    """Abstract base class to implement for both Report and Declaration models."""

    model_class = None
    admin_url_name = None
    manager_field = None
    template_name = None
    status_change_field = None

    def get_admin_url(self, instance):
        """Generate admin URL for an instance."""
        server_name = settings.ALLOWED_HOSTS[-1]
        admin_url = reverse(self.admin_url_name, args=(instance.pk,))
        return f"https://{server_name}{admin_url}"

    def get_manager_emails(self):
        """Get email addresses of managers for this model."""
        filter_kwargs = {self.manager_field: True}
        return list(
            User.objects.filter(**filter_kwargs).values_list("email", flat=True)
        )

    def get_created_last_month(self, last_month):
        """Get instances created in the last month."""
        return self.model_class.objects.filter(
            created_at__month=last_month.month,
            created_at__year=last_month.year,
        )

    def get_updated_last_month(self, last_month):
        """Get instances updated in the last month."""
        filter_kwargs = {
            f"{self.status_change_field}__isnull": False,
            "updated_at__month": last_month.month,
            "updated_at__year": last_month.year,
        }

        latest_status_updates = (
            StatusChange.objects.filter(**filter_kwargs)
            .select_related(self.status_change_field)
            .order_by(self.status_change_field, "-updated_at")
            .distinct(self.status_change_field)
        )

        # Store last update date on instance for later display.
        instances = []
        for status_change in latest_status_updates:
            instance = getattr(status_change, self.status_change_field)
            instance.last_updated_at = status_change.updated_at
            instances.append(instance)

        return instances

    def extract_as_json_data(self, instances, language, date_field="created_at"):
        """Extract instances as data for email template."""
        instances_data = []

        for instance in instances:
            with translation.override(language):
                status_display = instance.get_status_display()

            instance_date = getattr(instance, date_field)

            instance_data = {
                "id": instance.pk,
                date_field: instance_date,
                "status": status_display,
                "url": self.get_admin_url(instance),
            }
            instances_data.append(instance_data)

        return instances_data

    def get_status_distribution(self, queryset, language):
        """Get distribution of statuses for a queryset."""
        distribution = {}
        with translation.override(language):
            for status_code, status_label in Status.choices:
                distribution[status_label] = queryset.filter(status=status_code).count()
        return distribution

    def prepare_email_context(
        self, last_month, created_instances, updated_instances, all_instances, language
    ):
        """Prepare context data for the email template."""
        with translation.override(language):
            last_month_display = date_format(last_month, "F")

        return {
            "last_month": last_month_display,
            "created_count": len(created_instances),
            "updated_count": len(updated_instances),
            "total_count": all_instances.count(),
            "created": self.extract_as_json_data(
                created_instances, language, "created_at"
            ),
            "updated": self.extract_as_json_data(
                updated_instances, language, "last_updated_at"
            ),
            "instance_title": config.INSTANCE_TITLE,
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
            "monthly_distribution": self.get_status_distribution(
                self.model_class.objects.filter(
                    created_at__month=last_month.month,
                    created_at__year=last_month.year,
                ),
                language,
            ),
            "total_distribution": self.get_status_distribution(all_instances, language),
        }

    def send_summary_email(
        self, context, managers_emails, language, dry_run=False, stdout=None
    ):
        """Send the summary email to managers."""
        if not managers_emails:
            return 0

        with translation.override(language):
            subject_prefix = _(self.subject_prefix)
            full_subject = f"{subject_prefix} - {config.INSTANCE_TITLE}"
            template = get_template(self.template_name)
            message = template.render(context=context)

        if dry_run:
            stdout.write(f"\n{'=' * 50}")
            stdout.write(
                f"DRY RUN - Email would be sent to: {', '.join(managers_emails)}"
            )
            stdout.write(f"Subject: {full_subject}")
            stdout.write(f"{'=' * 50}")
            stdout.write(message)
            stdout.write(f"{'=' * 50}\n")
            return len(managers_emails)

        return send_mail(
            subject=full_subject,
            message=message,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=managers_emails,
            fail_silently=True,
        )

    def create_and_send_summary_email(
        self, last_month, language, dry_run=False, stdout=None
    ):
        """Process and send summary emails for a Declaration or Report models."""
        # Get data
        all_instances = self.model_class.objects.all()
        created_instances = self.get_created_last_month(last_month)
        updated_instances = self.get_updated_last_month(last_month)
        managers_emails = self.get_manager_emails()

        # Prepare and send email
        context = self.prepare_email_context(
            last_month=last_month,
            created_instances=created_instances,
            updated_instances=updated_instances,
            all_instances=all_instances,
            language=language,
        )

        sent_emails = self.send_summary_email(
            context, managers_emails, language, dry_run, stdout
        )

        return sent_emails


class DeclarationSummaryHandler(BaseSummaryHandler):
    """Summary handler for Declaration model."""

    model_class = Declaration
    admin_url_name = "config_site:terra_layer_declaration_change"
    manager_field = "is_declaration_manager"
    template_name = "declarations_summary.txt"
    subject_prefix = _("Monthly declarations summary")
    status_change_field = "declaration"


class ReportSummaryHandler(BaseSummaryHandler):
    """Summary handler for Report model."""

    model_class = Report
    admin_url_name = "config_site:terra_layer_report_change"
    manager_field = "is_report_manager"
    template_name = "reports_summary.txt"
    subject_prefix = _("Monthly reports summary")
    status_change_field = "report"

    def get_created_last_month(self, last_month):
        """Override method with optimized queries."""
        return (
            super()
            .get_created_last_month(last_month)
            .select_related("layer", "layer__main_field")
            .order_by("layer", "feature")
        )

    def get_updated_last_month(self, last_month):
        """Override method with optimized queries."""
        filter_kwargs = {
            "report__isnull": False,
            "updated_at__month": last_month.month,
            "updated_at__year": last_month.year,
        }

        latest_status_updates = (
            StatusChange.objects.filter(**filter_kwargs)
            .select_related("report", "report__layer", "report__layer__main_field")
            .order_by("report", "-updated_at")
            .distinct("report")
        )

        reports = []
        for status_change in latest_status_updates:
            report = status_change.report
            report.last_updated_at = status_change.updated_at
            reports.append(report)

        return reports

    def get_display_name(self, layer):
        """Get display name for a layer."""
        return layer.name or f"{_('Layer')} {layer.pk}"

    def get_feature_display(self, report):
        """Get display value for a feature."""
        feature_main_field = getattr(report.layer.main_field, "name", None)
        if feature_main_field:
            feature_main_field_value = report.feature.properties.get(
                feature_main_field, None
            )
            if feature_main_field_value:
                return feature_main_field_value
        object_str = _("Object")
        return f"{object_str} {report.feature.pk}"

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

            report_date = getattr(report, date_field)

            report_data = {
                "id": report.pk,
                date_field: report_date,
                "status": status_display,
                "url": self.get_admin_url(report),
            }
            grouped_reports[layer_display][feature_display].append(report_data)

        return grouped_reports

    def prepare_email_context(
        self, last_month, created_instances, updated_instances, all_instances, language
    ):
        """Prepare context data for the report email template."""
        with translation.override(language):
            last_month_display = date_format(last_month, "F")

        return {
            "last_month": last_month_display,
            "created_count": len(created_instances),
            "updated_count": len(updated_instances),
            "total_count": all_instances.count(),
            "grouped_created": self.group_reports_by_layer_and_feature(
                created_instances, language, "created_at"
            ),
            "grouped_updated": self.group_reports_by_layer_and_feature(
                updated_instances, language, "last_updated_at"
            ),
            "instance_title": config.INSTANCE_TITLE,
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
            "monthly_distribution": self.get_status_distribution(
                self.model_class.objects.filter(
                    created_at__month=last_month.month,
                    created_at__year=last_month.year,
                ),
                language,
            ),
            "total_distribution": self.get_status_distribution(all_instances, language),
        }


class Command(BaseCommand):
    """Management command to send monthly summary emails to managers. This should run on the first day of every month."""

    help = (
        "Send monthly summary emails with reports and declarations "
        "created and updated in the last month. This should run on the first day of every month."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--language",
            type=str,
            default="en",
            help="Language for the summary email",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print rendered emails to terminal instead of sending them",
        )

    def handle(self, *args, **options):
        """Main command handler."""
        language = options["language"]
        dry_run = options["dry_run"]

        # Calculate last month
        last_month = timezone.now() - relativedelta(months=1)

        # Process Reports
        sent_emails = ReportSummaryHandler().create_and_send_summary_email(
            last_month, language, dry_run, self.stdout
        )
        self.stdout.write(f"Sent {sent_emails} report summary emails.")

        # Process Declarations
        sent_emails = DeclarationSummaryHandler().create_and_send_summary_email(
            last_month, language, dry_run, self.stdout
        )
        self.stdout.write(f"Sent {sent_emails} declaration summary emails.")
