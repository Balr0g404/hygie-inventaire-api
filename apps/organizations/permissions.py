from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Membership


def get_user_structure_ids(user):
    return Membership.objects.filter(user=user, is_active=True).values_list(
        "structure_id", flat=True
    )


def user_has_structure_role(user, structure_id, roles):
    return Membership.objects.filter(
        user=user, structure_id=structure_id, is_active=True, role__in=roles
    ).exists()


class StructurePermission(BasePermission):
    """
    Superusers: full access.
    Members: read-only on their structures.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method not in SAFE_METHODS:
            return False
        return Membership.objects.filter(user=request.user, structure=obj, is_active=True).exists()


class MembershipPermission(BasePermission):
    """
    Superusers: full access.
    Users: read-only on their own memberships.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.method not in SAFE_METHODS:
            return False
        return obj.user_id == request.user.id


class StructureScopedPermission(BasePermission):
    """
    Structure-scoped permission for inventory-like objects.
    Superusers: full access.
    Members: read access on their structures.
    Referent/Admin: write access on their structures.
    """

    write_roles = {Membership.Role.REFERENT, Membership.Role.ADMIN}

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        structure_id = None
        if hasattr(view, "get_structure_id_from_request"):
            structure_id = view.get_structure_id_from_request(request)
        if structure_id is None:
            return True
        return user_has_structure_role(request.user, structure_id, self.write_roles)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if not hasattr(view, "get_structure_from_obj"):
            return False
        structure = view.get_structure_from_obj(obj)
        if structure is None:
            return False
        membership_qs = Membership.objects.filter(
            user=request.user, structure=structure, is_active=True
        )
        if request.method in SAFE_METHODS:
            return membership_qs.exists()
        return membership_qs.filter(role__in=self.write_roles).exists()
