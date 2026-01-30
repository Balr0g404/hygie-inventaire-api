from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Membership, Organization, Structure
from .permissions import (
    MembershipPermission,
    StructurePermission,
    get_user_structure_ids,
)
from .serializers import MembershipSerializer, OrganizationSerializer, StructureSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]


class StructureViewSet(viewsets.ModelViewSet):
    serializer_class = StructureSerializer
    permission_classes = [StructurePermission]

    def get_queryset(self):
        queryset = Structure.objects.select_related("organization", "parent")
        user = self.request.user
        if user.is_superuser:
            return queryset
        structure_ids = get_user_structure_ids(user)
        return queryset.filter(id__in=structure_ids)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [MembershipPermission]

    def get_queryset(self):
        queryset = Membership.objects.select_related("user", "structure")
        user = self.request.user
        if user.is_superuser:
            return queryset
        return queryset.filter(user=user)
