import csv
import io

import freezegun
from django.core import mail
from django.test import TestCase
from django.utils.html import format_html

from project.accounts.tests.factories import SuperUserFactory
from project.geosource.models import FieldTypes
from project.terra_layer.models import ManagersMessage, ReportField, StatusChange
from project.terra_layer.tests.factories import (
    AuthentifiedDeclarationFactory,
    DeclarationFieldFactory,
    DeclarationFileFactory,
    LayerFactory,
    ReportFactory,
    ReportFileFactory,
    StatusChangeFactory,
    UnauthentifiedDeclarationFactory,
)


class LayerAdminTesCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        LayerFactory.create_batch(10)
        cls.user = SuperUserFactory.create()

    def setUp(self):
        self.client.force_login(self.user)

    def test_list(self):
        response = self.client.get("/debug/terra_layer/layer/")
        self.assertEqual(response.status_code, 200)


class ReportAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = SuperUserFactory.create(is_report_manager=True)
        cls.report = ReportFactory.create(user=cls.user)
        cls.report_file = ReportFileFactory(report=cls.report)
        field = cls.report.config.layer.source.fields.create(
            name="test_field", label="test_label", data_type=FieldTypes.String.value
        )
        cls.report_field = ReportField.objects.create(
            config=cls.report.config,
            order=1,
            field=field,
        )
        cls.main_field_name = getattr(cls.report.layer.main_field, "name")
        cls.report.feature.properties[cls.main_field_name] = (
            "test_displayed_feature_name"
        )
        cls.report.feature.save()
        StatusChangeFactory(report=cls.report)
        cls.report_no_object_label = ReportFactory.create(user=cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Remove file from disk
        cls.report_file.delete()

    def setUp(self):
        self.client.force_login(self.user)

    def test_report_list(self):
        response = self.client.get("/debug/terra_layer/report/")
        self.assertEqual(response.status_code, 200)

    def test_reportconfig_list(self):
        response = self.client.get("/debug/terra_layer/reportconfig/")
        self.assertEqual(response.status_code, 200)

    def test_reportfield_list(self):
        response = self.client.get("/debug/terra_layer/reportfield/")
        self.assertEqual(response.status_code, 200)

    def test_report_change(self):
        response = self.client.get(
            f"/debug/terra_layer/report/{self.report.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            format_html(
                f"<strong>{self.main_field_name}</strong>: test_displayed_feature_name"
            ),
        )
        self.assertContains(response, self.report_file.file.name)

    def test_report_without_name_change(self):
        response = self.client.get(
            f"/debug/terra_layer/report/{self.report_no_object_label.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            format_html(
                f"<strong>ID</strong>: {self.report_no_object_label.feature.pk}"
            ),
        )

    def test_report_change_status_sends_email(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            f"/debug/terra_layer/report/{self.report.pk}/change/",
            {
                "geom": '{"type": "Point", "coordinates": [6.851806864142417, 43.58039085560784]}',
                "status": "ACCEPTED",
                "managers_message": "Your report has been treated",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your report has been updated")
        status_change = StatusChange.objects.filter(report=self.report).last()
        self.assertEqual(status_change.message, "Your report has been treated")
        self.assertEqual(status_change.status_before, "NEW")
        self.assertEqual(status_change.status_after, "ACCEPTED")
        self.assertEqual(str(status_change), f"Status change {status_change.pk}")

    def test_report_change_message_sends_email(self):
        self.assertEqual(len(mail.outbox), 0)
        # Update with same status as before
        response = self.client.post(
            f"/debug/terra_layer/report/{self.report.pk}/change/",
            {
                "geom": '{"type": "Point", "coordinates": [6.851806864142417, 43.58039085560784]}',
                "status": "NEW",
                "managers_message": "Some info about your report",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Follow-up information about your report"
        )
        managers_message = ManagersMessage.objects.filter(report=self.report).last()
        self.assertEqual(managers_message.message, "Some info about your report")
        self.assertEqual(
            str(managers_message), f"Managers message {managers_message.pk}"
        )


class DeclarationAdminTestCase(TestCase):
    @classmethod
    @freezegun.freeze_time("2025-01-01 00:00:00")
    def setUpTestData(cls):
        cls.user = SuperUserFactory.create(is_declaration_manager=True)
        cls.declaration_field_1 = DeclarationFieldFactory()
        cls.declaration_config = cls.declaration_field_1.config
        cls.declaration = AuthentifiedDeclarationFactory()
        cls.declaration_no_user = UnauthentifiedDeclarationFactory()
        cls.declaration_file = DeclarationFileFactory(
            declaration=cls.declaration_no_user
        )
        StatusChangeFactory(declaration=cls.declaration_no_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Remove file from disk
        cls.declaration_file.delete()

    def setUp(self):
        self.client.force_login(self.user)

    def test_declaration_list(self):
        response = self.client.get("/config/terra_layer/declaration/")
        self.assertEqual(response.status_code, 200)
        html_content = response.content.decode()
        row_count = html_content.count('class="field-created_at')
        self.assertEqual(row_count, 2)

    @freezegun.freeze_time("2025-02-01 00:00:00")
    def test_declaration_list_and_filter(self):
        UnauthentifiedDeclarationFactory()
        response = self.client.get(
            "/config/terra_layer/declaration/?created_month_year=2025-02"
        )
        self.assertEqual(response.status_code, 200)
        html_content = response.content.decode()
        row_count = html_content.count('class="field-created_at')
        self.assertEqual(row_count, 1)

    def test_declarationconfig_list(self):
        response = self.client.get("/config/terra_layer/declarationconfig/")
        self.assertEqual(response.status_code, 200)

    def test_declaration_change_and_file(self):
        response = self.client.get(
            f"/config/terra_layer/declaration/{self.declaration_no_user.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.declaration_file.file.name)

    def test_declaration_change_status_sends_email(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            f"/config/terra_layer/declaration/{self.declaration.pk}/change/",
            {
                "geom": '{"type": "Point", "coordinates": [6.851806864142417, 43.58039085560784]}',
                "status": "ACCEPTED",
                "managers_message": "Your declaration has been treated",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Your declaration has been updated")
        status_change = StatusChange.objects.filter(
            declaration=self.declaration
        ).first()
        self.assertEqual(status_change.message, "Your declaration has been treated")
        self.assertEqual(str(status_change), f"Status change {status_change.pk}")

    def test_export_csv_data_formatting(self):
        response = self.client.post(
            "/config/terra_layer/declaration/",
            {
                "action": "export_as_csv",
                "_selected_action": [self.declaration.pk, self.declaration_no_user.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertEqual(
            response["Content-Disposition"], 'attachment; filename="declarations.csv"'
        )
        content = response.content.decode("utf-8")
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)

        expected_header = [
            "ID",
            "Created at",
            "Status",
            "Email",
            "Latitude",
            "Longitude",
            "Content",
            "Files",
            "Status changes",
        ]
        self.assertEqual(rows[0], expected_header)
        self.assertEqual(len(rows), 3)
        data_row = rows[1]
        self.assertEqual(data_row[0], str(self.declaration_no_user.pk))
        self.assertEqual(
            data_row[1], self.declaration_no_user.created_at.strftime("%d/%m/%Y %H:%M")
        )
        self.assertEqual(data_row[2], "New")
        self.assertEqual(data_row[3], "test@email.fr")
        self.assertEqual(data_row[4], "200000.0")
        self.assertEqual(data_row[5], "10000.0")
        expected_content = "The title of the field: Some message sent by a user though the feedback system | The Field Two: Some example content for testing purposes with additional information that provides context | Free comment: Another example with some extra information that was provided after the fields"
        self.assertEqual(data_row[6], expected_content)
        self.assertIn(self.declaration_file.file.name, data_row[7])
        self.assertEqual(data_row[8], "01/01/2025 (New → Accepted): Test text")

    def test_report_change_message_sends_email(self):
        self.assertEqual(len(mail.outbox), 0)
        response = self.client.post(
            f"/config/terra_layer/declaration/{self.declaration.pk}/change/",
            {
                "geom": '{"type": "Point", "coordinates": [6.851806864142417, 43.58039085560784]}',
                "status": "NEW",
                "managers_message": "Some information about your declaration",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject, "Follow-up information about your declaration"
        )
        managers_message = ManagersMessage.objects.filter(
            declaration=self.declaration
        ).first()
        self.assertEqual(
            managers_message.message, "Some information about your declaration"
        )
        self.assertEqual(
            str(managers_message), f"Managers message {managers_message.pk}"
        )
        response = self.client.get(
            f"/config/terra_layer/declaration/{self.declaration.pk}/change/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Some information about your declaration", response.content.decode()
        )
