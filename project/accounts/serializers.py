from django.contrib.auth.models import Group
from rest_framework import serializers

from project.accounts.models import FunctionalPermission, User


class FunctionalPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FunctionalPermission
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()

    def get_modules(self, instance):
        return list(
            set(instance.functional_permissions.values_list("module", flat=True))
        )

    class Meta:
        model = User
        fields = (
            "id",
            "uuid",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
            "last_login",
            "groups",
            "user_permissions",
            "modules",
            "properties",
        )


class GroupSerializer(serializers.ModelSerializer):
    users = serializers.PrimaryKeyRelatedField(
        many=True,
        source="user_set",
        queryset=User.objects.all(),
        required=False,
    )

    permission_list = FunctionalPermissionSerializer(many=True, read_only=True)
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=FunctionalPermission.objects.all(),
        required=False,
    )

    class Meta:
        model = Group
        ref_name = "TerraGroupSerializer"
        fields = ("id", "name", "users", "permissions", "permission_list")
