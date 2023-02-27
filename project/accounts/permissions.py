from rest_framework.permissions import SAFE_METHODS, BasePermission


class GroupAdminPermission(BasePermission):
    """Group viewset should be accessible in read only to can_manage_users permission"""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return not request.user.is_anonymous and (
                request.user.has_terra_perm("can_manage_users")
                or request.user.has_terra_perm("can_manage_groups")
            )
        return not request.user.is_anonymous and request.user.has_terra_perm(
            "can_manage_groups"
        )
