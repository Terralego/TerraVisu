from constance.test import override_config
from django.core import mail
from django.test import TestCase
from django.utils.timezone import now

from project.geosource.models import SourceReporting
from project.geosource.tests.factories import PostGISSourceFactory
from project.visu.tasks import periodic_source_refresh_report


class PeriodicReportTaskTestCase(TestCase):
    @override_config(
        INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS="terravisu@terra.org",
        INSTANCE_EMAIL_SOURCE_TYPE="periodic",
    )
    def test_report_active_email_sent(self):
        PostGISSourceFactory.create(
            report=SourceReporting.objects.create(status=0), last_refresh=now()
        )
        self.assertTrue(periodic_source_refresh_report())
        # test mail in outbox
        self.assertEqual(len(mail.outbox), 1)

    @override_config(
        INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS="terravisu@terra.org",
        INSTANCE_EMAIL_SOURCE_TYPE="periodic",
    )
    def test_report_active_email_not_sent(self):
        self.assertTrue(periodic_source_refresh_report())
        # test mail in outbox
        self.assertEqual(len(mail.outbox), 0)

    @override_config(
        INSTANCE_EMAIL_SOURCE_REFRESH_RECIPIENTS="terravisu@terra.org",
        INSTANCE_EMAIL_SOURCE_TYPE="everytime",
    )
    def test_report_inactive(self):
        PostGISSourceFactory.create(
            report=SourceReporting.objects.create(status=0), last_refresh=now()
        )
        self.assertTrue(periodic_source_refresh_report())
        # test mail in outbox
        self.assertEqual(len(mail.outbox), 0)
