from rest_framework import permissions


class SourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_perm("geosource.can_manage_sources")
