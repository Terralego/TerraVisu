from rest_framework import permissions


class SourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return request.user.has_terra_perm("can_manage_sources")
        return False
