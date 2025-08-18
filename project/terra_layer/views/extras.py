from constance import config
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from geostore.views import FeatureViewSet, LayerGroupViewsSet, LayerViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import generics, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import (
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from project.terra_layer.models import Declaration, DeclarationConfig, Report
from project.terra_layer.serializers import (
    DeclarationConfigSerializer,
    DeclarationSerializer,
    ReportSerializer,
)

from ...accounts.models import User
from ..permissions import ReadOnly
from ..serializers import MapBaseLayerSerializer


class GeostoreLayerViewSet(LayerViewSet):
    permission_classes = (ReadOnly,)


class GeostoreFeatureViewSet(FeatureViewSet):
    permission_classes = (ReadOnly,)


class GeostoreLayerGroupViewsSet(LayerGroupViewsSet):
    permission_classes = (ReadOnly,)


class BaseLayerViewSet(viewsets.ModelViewSet):
    serializer_class = MapBaseLayerSerializer
    queryset = MapBaseLayer.objects.all()

    @action(detail=True)
    def tilejson(self, request, *args, **kwargs):
        """Full tilejson"""
        base_layer = self.get_object()
        return Response(base_layer.tilejson)


class NotifyManagersMixin:
    def send_email_to_managers(self, template_name, context, title):
        report_managers_emails = User.objects.filter(
            is_report_and_declaration_manager=True
        ).values_list("email", flat=True)
        if report_managers_emails:
            txt_template = get_template(template_name)
            txt_message = txt_template.render(context=context)
            send_mail(
                title,
                txt_message,
                f"noreply@{self.request.get_host()}",
                recipient_list=report_managers_emails,
                fail_silently=True,
            )


class ReportCreateAPIView(NotifyManagersMixin, generics.CreateAPIView):
    model = Report
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def get_report_full_url(self, report):
        scheme = "https" if settings.SSL_ENABLED else "http"
        server_name = self.request.get_host()
        admin_url = reverse(
            f"config_site:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=(report.pk,),
        )
        return f"{scheme}://{server_name}{admin_url}"

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        context = {
            "layer": report.layer.name,
            "instance_title": config.INSTANCE_TITLE,
            "url": self.get_report_full_url(report),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        self.send_email_to_managers(
            "new_report.txt", context, _("New report submitted")
        )


class DeclarationConfigDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (ReadOnly,)
    serializer_class = DeclarationConfigSerializer

    def get_object(self):
        return DeclarationConfig.objects.first()


class DeclarationRateThrottle(AnonRateThrottle):
    rate = "5/minutes"


class DeclarationCreateAPIView(NotifyManagersMixin, generics.CreateAPIView):
    model = Declaration
    throttle_classes = [DeclarationRateThrottle]
    serializer_class = DeclarationSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [AllowAny]

    def get_declaration_full_url(self, report):
        scheme = "https" if settings.SSL_ENABLED else "http"
        server_name = self.request.get_host()
        admin_url = reverse(
            f"config_site:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=(report.pk,),
        )
        return f"{scheme}://{server_name}{admin_url}"

    def perform_create(self, serializer):
        user = None
        if not self.request.user.is_anonymous:
            user = self.request.user
        declaration = serializer.save(user=user)
        context = {
            "instance_title": config.INSTANCE_TITLE,
            "url": self.get_declaration_full_url(declaration),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        self.send_email_to_managers(
            "new_declaration.txt",
            context,
            _("New declaration submitted"),
        )
