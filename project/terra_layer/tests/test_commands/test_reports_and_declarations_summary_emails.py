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

        self.report4 = ReportFactory(status=Status.REJECTED)
        main_field_name = self.report4.layer.main_field.name
        report4_feature_properties = self.report4.feature.properties
        report4_feature_properties[main_field_name] = "Third feature"
        self.report4.feature.properties = report4_feature_properties
        self.report4.feature.save()
        self.report4.layer.name = "Other layer"
        self.report4.layer.save()

        self.declaration1 = DeclarationFactory(status=Status.REJECTED)
        self.declaration2 = DeclarationFactory(status=Status.NEW)
        self.declaration3 = DeclarationFactory(status=Status.ACCEPTED)
        StatusChangeFactory(report=self.report1, status_after=Status.ACCEPTED)
        StatusChangeFactory(report=self.report3, status_after=Status.ACCEPTED)
        StatusChangeFactory(declaration=self.declaration1, status_after=Status.REJECTED)
        StatusChangeFactory(declaration=self.declaration2, status_after=Status.REJECTED)
        # fmt: off
        self.REPORT_EMAIL = ("\n"
        "\n"
        "Bonjour,\n"
        "\n"
        "Veuillez trouver ci-dessous le récapitulatif mensuel des signalements créés et mis à jour sur TerraVisu Test.\n"
        "\n"
        "\n"
        "SIGNALEMENTS CRÉÉS EN OCTOBRE (4 AU TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "First layer\n"
        "   │\n"
        "   └── First feature\n"
        "          │\n"
        "          ├── Signalement "+str(self.report1.pk)+"    09/10/2025 00:00    Accepté\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report1.pk)+"/change/\n"
        "          │\n"
        "          ├── Signalement "+str(self.report2.pk)+"    09/10/2025 00:00    Nouveau\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report2.pk)+"/change/\n"
        "   │\n"
        "   └── Second feature\n"
        "          │\n"
        "          ├── Signalement "+str(self.report3.pk)+"    09/10/2025 00:00    Nouveau\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report3.pk)+"/change/\n"
        "\n"
        "Other layer\n"
        "   │\n"
        "   └── Third feature\n"
        "          │\n"
        "          ├── Signalement "+str(self.report4.pk)+"    09/10/2025 00:00    Rejeté\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report4.pk)+"/change/\n"
        "\n"
        "\n"
        "SIGNALEMENTS MIS À JOUR EN OCTOBRE (2 AU TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "First layer\n"
        "   │\n"
        "   └── First feature\n"
        "          │\n"
        "          ├── Signalement "+str(self.report1.pk)+"    mis à jour le 09/10/2025 00:00    Accepté\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report1.pk)+"/change/\n"
        "   │\n"
        "   └── Second feature\n"
        "          │\n"
        "          ├── Signalement "+str(self.report3.pk)+"    mis à jour le 09/10/2025 00:00    Nouveau\n"
        "          │   ▶ https://testserver.com/config/terra_layer/report/"+str(self.report3.pk)+"/change/\n"
        "\n"
        "\n"
        "RÉPARTITION DES SIGNALEMENTS\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "En octobre (4 au total) :\n"
        "\n"
        "   • Nouveau : 2\n"
        "   • En cours : 0\n"
        "   • Accepté : 1\n"
        "   • Rejeté : 1\n"
        "\n"
        "Depuis le début (5 au total) :\n"
        "\n"
        "   • Nouveau : 3\n"
        "   • En cours : 0\n"
        "   • Accepté : 1\n"
        "   • Rejeté : 1\n"
        "\n"
        "\n"
        "\n"
        "Bien cordialement,\n" 
        "\n"
        "Test Team\n")

        self.DECLARATION_EMAIL = ("\n"
        "\n"
        "Bonjour,\n"
        "\n"
        "Veuillez trouver ci-dessous le récapitulatif mensuel des déclarations créées et mises à jour sur TerraVisu Test.\n"
        "\n"
        "\n"
        "DÉCLARATIONS CRÉÉES EN OCTOBRE (3 AU TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "  │\n"
        "  ├── Déclaration "+str(self.declaration1.pk)+"    09/10/2025 00:00    Rejeté\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration1.pk)+"/change/\n"
        "  │\n"
        "  ├── Déclaration "+str(self.declaration2.pk)+"    09/10/2025 00:00    Nouveau\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration2.pk)+"/change/\n"
        "  │\n"
        "  ├── Déclaration "+str(self.declaration3.pk)+"    09/10/2025 00:00    Accepté\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration3.pk)+"/change/\n"
        "  \n"
        "\n"
        "\n"
        "DÉCLARATIONS MISES À JOUR EN OCTOBRE (2 AU TOTAL)\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "  │\n"
        "  ├── Déclaration "+str(self.declaration1.pk)+"    mis à jour le 09/10/2025 00:00    Rejeté\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration1.pk)+"/change/\n"
        "  │\n"
        "  ├── Déclaration "+str(self.declaration2.pk)+"    mis à jour le 09/10/2025 00:00    Nouveau\n"
        "  │   ▶ https://testserver.com/config/terra_layer/declaration/"+str(self.declaration2.pk)+"/change/\n"
        "\n"
        "\n"
        "\n"
        "RÉPARTITION DES DÉCLARATIONS\n"
        "─────────────────────────────────────────────────────────────────────────────\n"
        "\n"
        "En octobre (3 au total) :\n"
        "\n"
        "   • Nouveau : 1\n"
        "   • En cours : 0\n"
        "   • Accepté : 1\n"
        "   • Rejeté : 1\n"
        "\n"
        "Depuis le début (4 au total) :\n"
        "\n"
        "   • Nouveau : 2\n"
        "   • En cours : 0\n"
        "   • Accepté : 1\n"
        "   • Rejeté : 1\n"
        "\n"
        "\n"
        "\n"
        "Bien cordialement,\n"
        "\n"
        "Test Team\n")
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
        call_command("send_reports_and_declarations_summary_emails", language="fr")

        # Should have sent 2 emails (reports + declarations)
        self.assertEqual(len(mail.outbox), 2)

        # Find report and declaration emails
        report_email = mail.outbox[0]
        declaration_email = mail.outbox[1]

        # Check recipients
        self.assertIn("report_manager@test.com", report_email.to)
        self.assertIn("declaration_manager@test.com", declaration_email.to)

        # Check subject
        self.assertIn("Récapitulatif mensuel des signalements", report_email.subject)
        self.assertIn(
            "Récapitulatif mensuel des déclarations", declaration_email.subject
        )

        # Check content
        content = report_email.body
        expected_lines = self.REPORT_EMAIL.splitlines()
        actual_lines = content.splitlines()
        for i, expected_line in enumerate(expected_lines):
            self.assertEqual(expected_line, actual_lines[i])

        content = declaration_email.body
        expected_lines = self.DECLARATION_EMAIL.splitlines()
        actual_lines = content.splitlines()
        for i, expected_line in enumerate(expected_lines):
            self.assertEqual(expected_line, actual_lines[i])

    def test_no_managers_no_emails(self):
        """Test that no emails are sent when no managers exist."""
        User.objects.filter(is_report_manager=True).delete()
        User.objects.filter(is_declaration_manager=True).delete()
        mail.outbox.clear()
        call_command("send_reports_and_declarations_summary_emails", language="fr")
        self.assertEqual(len(mail.outbox), 0)
