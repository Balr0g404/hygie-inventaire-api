from rest_framework import serializers

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


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = (
            "id",
            "organization",
            "name",
            "sku",
            "unit",
            "category",
            "is_consumable",
            "requires_expiry",
            "requires_lot_number",
            "is_active",
        )
        read_only_fields = ("id",)


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ("id", "structure", "name", "address")
        read_only_fields = ("id",)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "site", "name", "location_type")
        read_only_fields = ("id",)


class ContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = ("id", "structure", "location", "type", "identifier", "label", "is_active")
        read_only_fields = ("id",)


class LotTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotTemplate
        fields = ("id", "organization", "code", "name", "version", "is_active")
        read_only_fields = ("id",)


class LotTemplateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotTemplateItem
        fields = ("id", "template", "group", "item", "expected_qty", "notes")
        read_only_fields = ("id",)


class LotInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LotInstance
        fields = (
            "id",
            "template",
            "container",
            "last_checked_at",
            "next_check_due_at",
            "status",
        )
        read_only_fields = ("id",)


class BatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Batch
        fields = ("id", "item", "lot_number", "expires_at")
        read_only_fields = ("id",)


class StockLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLine
        fields = ("id", "lot_instance", "item", "batch", "quantity")
        read_only_fields = ("id",)


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = (
            "id",
            "structure",
            "created_by",
            "type",
            "from_lot",
            "to_lot",
            "item",
            "batch",
            "quantity",
            "reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class InventorySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySession
        fields = (
            "id",
            "structure",
            "container",
            "validated_at",
            "validated_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class InventoryLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryLine
        fields = ("id", "session", "item", "expected_qty", "counted_qty")
        read_only_fields = ("id",)
