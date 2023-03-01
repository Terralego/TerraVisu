from django.contrib.auth.models import Group
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from project.accounts.models import FunctionalPermission, User
from project.accounts.permissions import GroupAdminPermission
from project.accounts.serializers import (
    FunctionalPermissionSerializer,
    GroupSerializer,
    UserSerializer,
)


class UserViewsSet(viewsets.ModelViewSet):
    permission_classes = [
        IsAuthenticated,
    ]
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = (
        permissions.IsAuthenticated,
        GroupAdminPermission,
    )
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class FunctionalPermissionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = FunctionalPermission.objects.all()
    serializer_class = FunctionalPermissionSerializer

    @action(
        detail=False,
        methods=["get"],
    )
    def available(self, request, *args, **kwargs):
        """List only logged user permission"""
        perms = request.user.functional_permissions
        serializer = self.get_serializer(perms, many=True)
        return Response(serializer.data)
