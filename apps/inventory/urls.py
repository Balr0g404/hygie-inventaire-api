from rest_framework.routers import DefaultRouter

from .views import (
    BatchViewSet,
    ContainerViewSet,
    InventoryLineViewSet,
    InventorySessionViewSet,
    ItemViewSet,
    LocationViewSet,
    LotInstanceViewSet,
    LotTemplateItemViewSet,
    LotTemplateViewSet,
    SiteViewSet,
    StockLineViewSet,
    StockMovementViewSet,
)

router = DefaultRouter()
router.register("items", ItemViewSet, basename="item")
router.register("sites", SiteViewSet, basename="site")
router.register("locations", LocationViewSet, basename="location")
router.register("containers", ContainerViewSet, basename="container")
router.register("lot-templates", LotTemplateViewSet, basename="lot-template")
router.register("lot-template-items", LotTemplateItemViewSet, basename="lot-template-item")
router.register("lot-instances", LotInstanceViewSet, basename="lot-instance")
router.register("batches", BatchViewSet, basename="batch")
router.register("stock-lines", StockLineViewSet, basename="stock-line")
router.register("stock-movements", StockMovementViewSet, basename="stock-movement")
router.register("inventory-sessions", InventorySessionViewSet, basename="inventory-session")
router.register("inventory-lines", InventoryLineViewSet, basename="inventory-line")

urlpatterns = router.urls
