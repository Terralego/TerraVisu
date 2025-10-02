from io import StringIO

import freezegun
from constance.test import override_config
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from project.accounts.models import User
from project.terra_layer.models import Status

from ..factories import (
    DeclarationFactory,
    ReportFactory,
    StatusChangeFactory,
    UserFactory,
)


class SummaryEmailCommandTestCase(TestCase):
    """Test the complete summary email command with realistic data."""

    @freezegun.freeze_time("2025-10-9 00:00:00")
    def setUp(self):
        self.report_manager = UserFactory(
            email="report_manager@test.com", is_report_manager=True
        )
        self.declaration_manager = UserFactory(
            email="declaration_manager@test.com", is_declaration_manager=True
        )
        self.report1 = ReportFactory(status=Status.ACCEPTED)
        main_field_name = self.report1.layer.main_field.name
        report1_feature_properties = self.report1.feature.properties
        report1_feature_properties[main_field_name] = "First feature"
        self.report1.feature.properties = report1_feature_properties
        self.report1.feature.save()
        self.report1.layer.name = "First layer"
        self.report1.layer.save()

        self.report2 = ReportFactory(
            layer=self.report1.layer, feature=self.report1.feature, status=Status.NEW
        )

        self.report3 = ReportFactory(layer=self.report1.layer, status=Status.NEW)
        report3_feature_properties = self.report3.feature.properties
        report3_feature_properties[main_field_name] = "Second feature"
        self.report3.feature.properties = report3_feature_properties
        self.report3.feature.save()

        self.report4 = ReportFactory(status=Status.NEW)
        self.feature = self.report4.feature
        self.report4.layer.name = "Other layer"
        self.report4.layer.save()

        self.declaration1 = DeclarationFactory(status=Status.NEW)
        self.declaration2 = DeclarationFactory(status=Status.NEW)
        self.declaration3 = DeclarationFactory(status=Status.NEW)
        StatusChangeFactory(report=self.report1, status_after=Status.ACCEPTED)
        StatusChangeFactory(report=self.report3, status_after=Status.ACCEPTED)
        StatusChangeFactory(declaration=self.declaration1, status_after=Status.REJECTED)
        StatusChangeFactory(declaration=self.declaration2, status_after=Status.REJECTED)
        # fmt: off
        self.REPORT_EMAIL = ("\n"
        "\n"
        "\n"
        "Hi,\n"
        "\n"
        "Please find below the monthly summary of created and updated reports on TerraVisu Test.\n"
        "\n"
        "\n"
        "REPORTS CREATED IN OCTOBER 2025 (3 IN TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "First layer\n"
        "   │\n"
        "   └── First feature\n"
        "          │\n"
        "          ├── Report "+str(self.report2.pk)+"    09/10/2025 00:00    New\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report2.pk)+"/change/\n"
        "   │\n"
        "   └── Second feature\n"
        "          │\n"
        "          ├── Report "+str(self.report3.pk)+"    09/10/2025 00:00    New\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report3.pk)+"/change/\n"
        "\n"
        "Other layer\n"
        "   │\n"
        "   └── Object " +str(self.feature.pk)+"\n"
        "          │\n"
        "          ├── Report "+str(self.report4.pk)+"    09/10/2025 00:00    New\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report4.pk)+"/change/\n"
        "\n"
        "\n"
        "REPORTS UPDATED IN OCTOBER 2025 (2 IN TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "First layer\n"
        "   │\n"
        "   └── First feature\n"
        "          │\n"
        "          ├── Report "+str(self.report1.pk)+"    updated at 09/10/2025 00:00    Accepted\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report1.pk)+"/change/\n"
        "   │\n"
        "   └── Second feature\n"
        "          │\n"
        "          ├── Report "+str(self.report3.pk)+"    updated at 09/10/2025 00:00    New\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report3.pk)+"/change/\n"
        "\n"
        "\n"
        "REPORTS DISTRIBUTION\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "From October :\n"
        "\n"
        "   • New : 3\n"
        "   • Pending : 0\n"
        "   • Accepted : 1\n"
        "   • Rejected : 0\n"
        "\n"
        "From the start :\n"
        "\n"
        "   • New : 4\n"
        "   • Pending : 0\n"
        "   • Accepted : 1\n"
        "   • Rejected : 0\n"
        "\n"
        "\n"
        "\n"
        "Regards,\n" 
        "\n"
        "Test Team\n")

        self.DECLARATION_EMAIL = ("\n"
        "\n"
        "\n"
        "Hi,\n"
        "\n"
        "Please find below the monthly summary of created and updated declarations on TerraVisu Test.\n"
        "\n"
        "\n"
        "DECLARATIONS CREATED IN OCTOBER 2025 (3 IN TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "  │\n"
        "  ├── Declaration "+str(self.declaration1.pk)+"    09/10/2025 00:00    New\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration1.pk)+"/change/\n"
        "  │\n"
        "  ├── Declaration "+str(self.declaration2.pk)+"    09/10/2025 00:00    New\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration2.pk)+"/change/\n"
        "  │\n"
        "  ├── Declaration "+str(self.declaration3.pk)+"    09/10/2025 00:00    New\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration3.pk)+"/change/\n"
        "\n"
        "\n"
        "\n"
        "DECLARATIONS UPDATED IN OCTOBER 2025 (2 IN TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "  │\n"
        "  ├── Declaration "+str(self.declaration1.pk)+"    updated at 09/10/2025 00:00    New\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration1.pk)+"/change/\n"
        "  │\n"
        "  ├── Declaration "+str(self.declaration2.pk)+"    updated at 09/10/2025 00:00    New\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration2.pk)+"/change/\n"
        "\n"
        "\n"
        "\n"
        "DECLARATIONS DISTRIBUTION\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "From October :\n"
        "\n"
        "   • New : 3\n"
        "   • Pending : 0\n"
        "   • Accepted : 0\n"
        "   • Rejected : 0\n"
        "\n"
        "From the start :\n"
        "\n"
        "   • New : 4\n"
        "   • Pending : 0\n"
        "   • Accepted : 0\n"
        "   • Rejected : 0\n"
        "\n"
        "\n"
        "\n"
        "Regards,\n"
        "\n"
        "Test Team\n")
        self.DECLARATION_HEADER = ("==================================================\n"
        "Sent 1 report summary emails.\n"
        "\n"
        "==================================================\n"
        "DRY RUN - Email would be sent to: declaration_manager@test.com\n"
        "Subject: Monthly declarations summary - TerraVisu Test\n"
        "==================================================\n")
        self.REPORT_HEADER = ("\n"
        "==================================================\n"
        "DRY RUN - Email would be sent to: report_manager@test.com\n"
        "Subject: Monthly reports summary - TerraVisu Test\n"
        "==================================================\n")
        # fmt: on

    @freezegun.freeze_time("2025-11-10 00:00:00")
    @override_settings(
        ALLOWED_HOSTS=["testserver.com"],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    @override_config(INSTANCE_TITLE="TerraVisu Test", REPORT_MAIL_SIGNATURE="Test Team")
    def test_summary_email_command_execution(self):
        """Test that the command executes and sends correct emails."""
        # Not included because not from last month
        self.report5 = ReportFactory()
        self.declaration3 = DeclarationFactory()
        # Run the command
        output = StringIO()
        call_command(
            "send_reports_and_declarations_summary_emails", language="en", stdout=output
        )

        # Should have sent 2 emails (reports + declarations)
        self.assertEqual(len(mail.outbox), 2)

        # Find report and declaration emails
        report_email = mail.outbox[0]
        declaration_email = mail.outbox[1]

        # Check recipients
        self.assertIn("report_manager@test.com", report_email.to)
        self.assertIn("declaration_manager@test.com", declaration_email.to)

        # Check subject
        self.assertIn("Monthly reports summary", report_email.subject)
        self.assertIn("Monthly declarations summary", declaration_email.subject)

        # Check content
        content = report_email.body
        expected_lines = self.REPORT_EMAIL.splitlines()
        actual_lines = content.splitlines()
        for i, expected_line in enumerate(expected_lines):
            self.assertEqual(expected_line, actual_lines[i].replace("\xa0", " "))

        content = declaration_email.body
        expected_lines = self.DECLARATION_EMAIL.splitlines()
        actual_lines = content.splitlines()
        for i, expected_line in enumerate(expected_lines):
            self.assertEqual(expected_line, actual_lines[i].replace("\xa0", " "))

    @freezegun.freeze_time("2025-11-10 00:00:00")
    @override_settings(
        ALLOWED_HOSTS=["testserver.com"],
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    )
    @override_config(INSTANCE_TITLE="TerraVisu Test", REPORT_MAIL_SIGNATURE="Test Team")
    def test_summary_email_dry_run_command_execution(self):
        """Test that the command executes properly with dry run mode."""
        # Not included because not from last month
        self.report5 = ReportFactory()
        self.declaration3 = DeclarationFactory()
        # Run the command
        output = StringIO()
        call_command(
            "send_reports_and_declarations_summary_emails",
            language="en",
            dry_run=True,
            stdout=output,
        )

        # Check content
        output_lines = output.getvalue().splitlines()

        expected_sections = [
            self.REPORT_HEADER.splitlines(),
            self.REPORT_EMAIL.splitlines(),
            self.DECLARATION_HEADER.splitlines(),
            self.DECLARATION_EMAIL.splitlines(),
        ]

        expected_lines = [line for section in expected_sections for line in section]

        for i, (expected, actual) in enumerate(zip(expected_lines, output_lines)):
            self.assertEqual(
                expected, actual.replace("\xa0", " "), f"Line {i + 1} mismatch"
            )

    def test_no_managers_no_emails(self):
        """Test that no emails are sent when no managers exist."""
        User.objects.filter(is_report_manager=True).delete()
        User.objects.filter(is_declaration_manager=True).delete()
        mail.outbox.clear()
        output = StringIO()
        call_command(
            "send_reports_and_declarations_summary_emails", language="fr", stdout=output
        )
        self.assertEqual(len(mail.outbox), 0)
