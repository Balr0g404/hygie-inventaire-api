from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Membership, Organization, Structure
from .serializers import MembershipSerializer, OrganizationSerializer, StructureSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]


class StructureViewSet(viewsets.ModelViewSet):
    queryset = Structure.objects.select_related("organization", "parent")
    serializer_class = StructureSerializer
    permission_classes = [IsAuthenticated]


class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("user", "structure")
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]
