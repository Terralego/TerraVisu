from constance import config
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import get_template
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from geostore.views import FeatureViewSet, LayerGroupViewsSet, LayerViewSet
from mapbox_baselayer.models import MapBaseLayer
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import (
    JSONParser,
    MultiPartParser,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from project.terra_layer.models import (
    Declaration,
    DeclarationConfig,
    Report,
    StyleImage,
)
from project.terra_layer.serializers import (
    DeclarationConfigSerializer,
    DeclarationSerializer,
    GeostoreFeatureSerializer,
    ReportSerializer,
)

from ...accounts.models import User
from ..permissions import ReadOnly
from ..serializers import MapBaseLayerSerializer, StyleImageSerializer


class GeostoreLayerViewSet(LayerViewSet):
    permission_classes = (ReadOnly,)


class GeostoreFeatureViewSet(FeatureViewSet):
    permission_classes = (ReadOnly,)
    serializer_class = GeostoreFeatureSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("reports")


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


class NotifyManagersViewMixin:
    def get_object_full_url(self, report):
        scheme = "https" if settings.SSL_ENABLED else "http"
        server_name = self.request.get_host()
        admin_url = reverse(
            f"config_site:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            args=(report.pk,),
        )
        return f"{scheme}://{server_name}{admin_url}"

    def send_email_to_managers(self, template_name, context, title):
        managers_emails = User.objects.filter(
            **{f"is_{self.model._meta.model_name}_manager": True}
        ).values_list("email", flat=True)
        if managers_emails:
            txt_template = get_template(template_name)
            txt_message = txt_template.render(context=context)
            send_mail(
                title,
                txt_message,
                None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=managers_emails,
                fail_silently=True,
            )


class ReportCreateAPIView(NotifyManagersViewMixin, generics.CreateAPIView):
    model = Report
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"Created report": report.pk},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        context = {
            "layer": report.layer.name,
            "instance_title": config.INSTANCE_TITLE,
            "url": self.get_object_full_url(report),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        self.send_email_to_managers(
            "new_report.txt", context, _("New report submitted")
        )
        return report


class DeclarationConfigDetailAPIView(generics.RetrieveAPIView):
    permission_classes = (ReadOnly,)
    serializer_class = DeclarationConfigSerializer

    def get_object(self):
        return DeclarationConfig.objects.first()


class DeclarationRateThrottle(AnonRateThrottle):
    rate = "5/minutes"


class DeclarationCreateAPIView(NotifyManagersViewMixin, generics.CreateAPIView):
    model = Declaration
    throttle_classes = [DeclarationRateThrottle]
    serializer_class = DeclarationSerializer
    parser_classes = [MultiPartParser, JSONParser]
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        declaration = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"Created declaration": declaration.pk},
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    def perform_create(self, serializer):
        user = None
        if not self.request.user.is_anonymous:
            user = self.request.user
        declaration = serializer.save(user=user)
        context = {
            "instance_title": config.INSTANCE_TITLE,
            "url": self.get_object_full_url(declaration),
            "report_mail_signature": config.REPORT_MAIL_SIGNATURE,
        }
        self.send_email_to_managers(
            "new_declaration.txt",
            context,
            _("New declaration submitted"),
        )
        return declaration


class IconViewSet(viewsets.ModelViewSet):
    serializer_class = StyleImageSerializer
    queryset = StyleImage.objects.all()
    ordering_fields = (
        "id",
        "name",
    )
    search_fields = ["name"]
