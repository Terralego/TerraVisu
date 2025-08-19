import django_filters
from django.contrib import admin
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import FilterSet

from project.terra_layer.models import Layer, Scene


class SceneFilterSet(FilterSet):
    def filter_user_scenes(self, queryset, name, value):
        if value:
            return Scene.objects.get_user_scenes(self.request.user)
        return queryset

    viewer = django_filters.BooleanFilter(
        help_text="Filter out scenes that are not visible to the viewer for frontend",
        method="filter_user_scenes",
    )

    class Meta:
        model = Scene
        fields = ["viewer"]


class LayerFilterSet(FilterSet):
    class Meta:
        model = Layer
        fields = [
            "source",
            "group",
            "group__view",
            "active_by_default",
            "in_tree",
            "table_enable",
        ]


class MonthYearFilter(admin.SimpleListFilter):
    title = _("Creation month")
    parameter_name = "created_month_year"

    def lookups(self, request, model_admin):
        dates = model_admin.model.objects.dates("created_at", "month", order="DESC")
        choices = []
        for date_obj in dates:
            month_year = f"{date_obj.year}-{date_obj.month:02d}"
            month_display = date_format(date_obj).split(" ")[1].capitalize()
            month_year_display = f"{month_display} {date_obj.year}"
            choices.append((month_year, month_year_display))
        return choices

    def queryset(self, request, queryset):
        if self.value():
            month_year = request.GET.get(self.parameter_name)
            if month_year:
                year, month = month_year.split("-")
                year = int(year)
                month = int(month)
                return queryset.filter(created_at__year=year, created_at__month=month)
        return queryset
