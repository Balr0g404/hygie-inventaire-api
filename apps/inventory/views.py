from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.organizations.permissions import (
    StructureScopedPermission,
    get_user_structure_ids,
)

from .models import (
    Batch,
    Container,
    InventoryLine,
    InventorySession,
    Item,
    Location,
    LotInstance,
    LotTemplate,
    LotTemplateItem,
    Site,
    StockLine,
    StockMovement,
)
from .serializers import (
    BatchSerializer,
    ContainerSerializer,
    InventoryLineSerializer,
    InventorySessionSerializer,
    ItemSerializer,
    LocationSerializer,
    LotInstanceSerializer,
    LotTemplateItemSerializer,
    LotTemplateSerializer,
    SiteSerializer,
    StockLineSerializer,
    StockMovementSerializer,
)


def _resolve_attr_path(obj, attr_path):
    current = obj
    for part in attr_path.split("__"):
        current = getattr(current, part, None)
        if current is None:
            return None
    return current


class StructureScopedQuerysetMixin:
    structure_path = None
    structure_request_field = None

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_superuser:
            return queryset
        structure_ids = get_user_structure_ids(user)
        if not self.structure_path:
            return queryset.none()
        return queryset.filter(**{f"{self.structure_path}__in": structure_ids})

    def get_structure_from_obj(self, obj):
        if not self.structure_path:
            return None
        return _resolve_attr_path(obj, self.structure_path)

    def get_structure_id_from_request(self, request):
        if not self.structure_request_field:
            return None
        return request.data.get(self.structure_request_field)


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]


class SiteViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Site.objects.select_related("structure")
    serializer_class = SiteSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "structure"
    structure_request_field = "structure"


class LocationViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Location.objects.select_related("site")
    serializer_class = LocationSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "site__structure"

    def get_structure_id_from_request(self, request):
        site_id = request.data.get("site")
        if not site_id:
            return None
        return Site.objects.filter(id=site_id).values_list("structure_id", flat=True).first()


class ContainerViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Container.objects.select_related("structure", "location")
    serializer_class = ContainerSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "structure"
    structure_request_field = "structure"


class LotTemplateViewSet(viewsets.ModelViewSet):
    queryset = LotTemplate.objects.select_related("organization")
    serializer_class = LotTemplateSerializer
    permission_classes = [IsAuthenticated]


class LotTemplateItemViewSet(viewsets.ModelViewSet):
    queryset = LotTemplateItem.objects.select_related("template", "item")
    serializer_class = LotTemplateItemSerializer
    permission_classes = [IsAuthenticated]


class LotInstanceViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = LotInstance.objects.select_related("template", "container")
    serializer_class = LotInstanceSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "container__structure"

    def get_structure_id_from_request(self, request):
        container_id = request.data.get("container")
        if not container_id:
            return None
        return (
            Container.objects.filter(id=container_id)
            .values_list("structure_id", flat=True)
            .first()
        )


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related("item")
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]


class StockLineViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = StockLine.objects.select_related("lot_instance", "item", "batch")
    serializer_class = StockLineSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "lot_instance__container__structure"

    def get_structure_id_from_request(self, request):
        lot_instance_id = request.data.get("lot_instance")
        if not lot_instance_id:
            return None
        return (
            LotInstance.objects.filter(id=lot_instance_id)
            .values_list("container__structure_id", flat=True)
            .first()
        )


class StockMovementViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related(
        "structure", "created_by", "from_lot", "to_lot", "item", "batch"
    )
    serializer_class = StockMovementSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "structure"
    structure_request_field = "structure"


class InventorySessionViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = InventorySession.objects.select_related("structure", "container", "validated_by")
    serializer_class = InventorySessionSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "structure"
    structure_request_field = "structure"


class InventoryLineViewSet(StructureScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = InventoryLine.objects.select_related("session", "item")
    serializer_class = InventoryLineSerializer
    permission_classes = [StructureScopedPermission]
    structure_path = "session__structure"

    def get_structure_id_from_request(self, request):
        session_id = request.data.get("session")
        if not session_id:
            return None
        return (
            InventorySession.objects.filter(id=session_id)
            .values_list("structure_id", flat=True)
            .first()
        )
