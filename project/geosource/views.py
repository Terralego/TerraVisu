from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import SourceFilterSet
from .models import Source, SourceReporting
from .parsers import NestedMultipartJSONParser
from .permissions import SourcePermission
from .serializers import SourceListSerializer, SourceSerializer


class SourceModelViewset(ModelViewSet):
    parser_classes = (JSONParser, NestedMultipartJSONParser)
    permission_classes = (SourcePermission,)
    filterset_class = SourceFilterSet
    search_fields = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return SourceListSerializer
        return SourceSerializer

    def get_queryset(self):
        qs = Source.objects.all().order_by("-id")
        if self.action == "list":
            # used to filter by layers count
            qs = qs.annotate(layers_count=Count("layers"))
        return qs

    def perform_create(self, serializers):
        serializers.save(author=self.request.user)

    @action(detail=True, methods=["get"])
    def refresh(self, request, pk):
        """Schedule a refresh now"""

        source = self.get_object()

        force_refresh = request.query_params.get("force")

        refresh_job = source.run_async_method("refresh_data", force=force_refresh)
        if refresh_job:
            source.status = Source.Status.PENDING.value
            if not source.report:
                source.report = SourceReporting.objects.create()
            source.save()
            return Response(
                data=source.get_status(),
                status=status.HTTP_202_ACCEPTED,
            )

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=["get"])
    def property_values(self, request, pk):
        """
        Returns all distinct values of specified GET "property" params from
        database for the specified source layer.

        Note: if some record has no value for this property, None is contained in the
        result list.
        """
        property_to_list = request.query_params.get("property")
        if not property_to_list:
            return Response(
                {"error": 'Invalid "property" GET parameter'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source = self.get_object()
        result = source.get_layer().get_property_values(property_to_list)

        return Response(result)
