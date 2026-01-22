from rest_framework.routers import DefaultRouter

from .views import MembershipViewSet, OrganizationViewSet, StructureViewSet

router = DefaultRouter()
router.register("organizations", OrganizationViewSet, basename="organization")
router.register("structures", StructureViewSet, basename="structure")
router.register("memberships", MembershipViewSet, basename="membership")

urlpatterns = router.urls
