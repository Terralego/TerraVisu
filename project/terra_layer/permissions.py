from rest_framework import permissions


class LayerPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_anonymous and request.user.has_terra_perm(
            "can_manage_layers"
        )


class ScenePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return not request.user.is_anonymous and request.user.has_terra_perm(
            "can_manage_layers"
        )


class SourcePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_anonymous and request.user.has_terra_perm(
            "can_manage_sources"
        )


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
