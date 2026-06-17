"""Role-based DRF permission classes."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Allow access only to authenticated users with the admin role."""

    message = "Only admin users may perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_role)


class IsAdminOrReadOnly(BasePermission):
    """Read access for any authenticated user; writes for admins only.

    Used on the menu endpoints: customers browse, admins manage.
    """

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_admin_role


class IsOwnerOrAdmin(BasePermission):
    """Object-level access for the owning customer or any admin.

    The view is expected to expose the owner via ``obj.customer``.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        return user.is_admin_role or obj.customer_id == user.id
