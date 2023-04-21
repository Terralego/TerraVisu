from rest_framework import permissions


class SourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.has_terra_perm("can_manage_sources")
