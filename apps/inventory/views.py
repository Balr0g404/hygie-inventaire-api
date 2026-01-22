from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

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


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated]


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.select_related("structure")
    serializer_class = SiteSerializer
    permission_classes = [IsAuthenticated]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.select_related("site")
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.select_related("structure", "location")
    serializer_class = ContainerSerializer
    permission_classes = [IsAuthenticated]


class LotTemplateViewSet(viewsets.ModelViewSet):
    queryset = LotTemplate.objects.select_related("organization")
    serializer_class = LotTemplateSerializer
    permission_classes = [IsAuthenticated]


class LotTemplateItemViewSet(viewsets.ModelViewSet):
    queryset = LotTemplateItem.objects.select_related("template", "item")
    serializer_class = LotTemplateItemSerializer
    permission_classes = [IsAuthenticated]


class LotInstanceViewSet(viewsets.ModelViewSet):
    queryset = LotInstance.objects.select_related("template", "container")
    serializer_class = LotInstanceSerializer
    permission_classes = [IsAuthenticated]


class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.select_related("item")
    serializer_class = BatchSerializer
    permission_classes = [IsAuthenticated]


class StockLineViewSet(viewsets.ModelViewSet):
    queryset = StockLine.objects.select_related("lot_instance", "item", "batch")
    serializer_class = StockLineSerializer
    permission_classes = [IsAuthenticated]


class StockMovementViewSet(viewsets.ModelViewSet):
    queryset = StockMovement.objects.select_related(
        "structure", "created_by", "from_lot", "to_lot", "item", "batch"
    )
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]


class InventorySessionViewSet(viewsets.ModelViewSet):
    queryset = InventorySession.objects.select_related(
        "structure", "container", "validated_by"
    )
    serializer_class = InventorySessionSerializer
    permission_classes = [IsAuthenticated]


class InventoryLineViewSet(viewsets.ModelViewSet):
    queryset = InventoryLine.objects.select_related("session", "item")
    serializer_class = InventoryLineSerializer
    permission_classes = [IsAuthenticated]
