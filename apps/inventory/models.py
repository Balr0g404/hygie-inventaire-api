# apps/inventory/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.organizations.models import Organization, Structure


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Item(TimeStampedModel):
    """
    Référentiel global à l'organisation (CRF).
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="items")

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, blank=True, default="")
    unit = models.CharField(max_length=32, blank=True, default="")  # ex: piece, boite, paire, metre
    category = models.CharField(max_length=128, blank=True, default="")

    is_consumable = models.BooleanField(default=True)
    requires_expiry = models.BooleanField(default=False)
    requires_lot_number = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "name"]),
            models.Index(fields=["organization", "sku"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="uniq_item_name_per_org",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Site(TimeStampedModel):
    """
    Un site de stockage pour une structure (ex: Garage UL, Local DPS, Entrepôt DT).
    """

    structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="sites")
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, default="")

    class Meta:
        indexes = [models.Index(fields=["structure", "name"])]

    def __str__(self) -> str:
        return f"{self.structure_id} - {self.name}"


class Location(TimeStampedModel):
    """
    Emplacement dans un site (ex: Armoire 1, Étagère A, Coffre VPSP).
    """

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="locations")
    name = models.CharField(max_length=255)
    location_type = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "name"], name="uniq_location_name_per_site"),
        ]
        indexes = [models.Index(fields=["site", "name"])]

    def __str__(self) -> str:
        return f"{self.site_id} - {self.name}"


class Container(TimeStampedModel):
    """
    Conteneur identifié: sac (intervention / oxy / 1er secours), VPSP, bouteille O2, malle réserve, etc.
    """

    class Type(models.TextChoices):
        BAG_INTERVENTION = "BAG_INTERVENTION", "Sac d'intervention"
        BAG_OXY = "BAG_OXY", "Sac d'oxygénothérapie"
        BAG_FIRST_AID = "BAG_FIRST_AID", "Sac de premiers secours"
        VEHICLE_VPSP = "VEHICLE_VPSP", "VPSP"
        OXYGEN_CYLINDER = "OXYGEN_CYLINDER", "Bouteille O2"
        RESERVE_CASE = "RESERVE_CASE", "Malle/Sac réserve"
        OTHER = "OTHER", "Autre"

    structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="containers")
    location = models.ForeignKey(
        Location,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="containers",
    )

    type = models.CharField(max_length=32, choices=Type.choices)
    identifier = models.CharField(max_length=64)  # QR/Codebar physique
    label = models.CharField(max_length=255, blank=True, default="")

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["structure", "identifier"],
                name="uniq_container_identifier_per_structure",
            ),
        ]
        indexes = [
            models.Index(fields=["structure", "type"]),
            models.Index(fields=["structure", "identifier"]),
        ]

    def __str__(self) -> str:
        return f"{self.identifier} ({self.get_type_display()})"


class LotTemplate(TimeStampedModel):
    """
    Recette officielle d'un lot (ex: CRF POS/DUO/MOT/2024-001).
    """

    class Code(models.TextChoices):
        LOT_A = "LOT_A", "Lot A (secours)"
        LOT_B = "LOT_B", "Lot B (1er secours)"
        LOT_C = "LOT_C", "Lot C (intervention)"
        VPSP = "VPSP", "VPSP"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="lot_templates"
    )

    code = models.CharField(max_length=16, choices=Code.choices)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32, blank=True, default="")  # ex: POS/DUO/MOT/2024-001
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "version"],
                name="uniq_template_per_org_code_version",
            ),
        ]
        indexes = [models.Index(fields=["organization", "code", "version"])]

    def __str__(self) -> str:
        return f"{self.code} - {self.version}"


class LotTemplateItem(TimeStampedModel):
    class Group(models.TextChoices):
        ADMIN_DOCS = "ADMIN_DOCS", "Administratif/Documents"
        COMMS = "COMMS", "Communication"
        PROTECTION = "PROTECTION", "Protection/Hygiène/Sécurité"
        VITALS = "VITALS", "Bilans"
        WOUNDS = "WOUNDS", "Hémorragies/Plaies"
        TRAUMA = "TRAUMA", "Immobilisations/Trauma"
        RESUSC = "RESUSC", "Réanimation"
        DIVERS = "DIVERS", "Divers"
        SPECIFIC_KITS = "SPECIFIC_KITS", "Kits spécifiques"

    template = models.ForeignKey(LotTemplate, on_delete=models.CASCADE, related_name="items")
    group = models.CharField(max_length=32, choices=Group.choices)

    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    expected_qty = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["template", "group", "item"],
                name="uniq_template_group_item",
            ),
            models.CheckConstraint(
                condition=Q(expected_qty__gte=0),
                name="check_expected_qty_non_negative",
            ),
        ]


class LotInstance(TimeStampedModel):
    """
    Un lot réel attaché à un conteneur (ex: Sac intervention Lot C UL01).
    """

    template = models.ForeignKey(LotTemplate, on_delete=models.PROTECT, related_name="instances")
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name="lots")

    last_checked_at = models.DateTimeField(null=True, blank=True)
    next_check_due_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, default="READY")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["template", "container"], name="uniq_template_container"
            ),
        ]


class Batch(TimeStampedModel):
    """
    Lot de fabrication / péremption pour un item.
    """

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="batches")
    lot_number = models.CharField(max_length=64, blank=True, default="")
    expires_at = models.DateField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["item", "expires_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["item", "lot_number", "expires_at"],
                name="uniq_batch_per_item_number_expiry",
            ),
        ]


class StockLine(TimeStampedModel):
    lot_instance = models.ForeignKey(
        LotInstance, on_delete=models.CASCADE, related_name="stock_lines"
    )
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.PROTECT)

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["lot_instance", "item", "batch"],
                name="uniq_stockline_per_lot_item_batch",
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0), name="check_stock_quantity_non_negative"
            ),
        ]


class StockMovement(TimeStampedModel):
    class Type(models.TextChoices):
        IN = "IN", "Entrée"
        OUT = "OUT", "Sortie"
        TRANSFER = "TRANSFER", "Transfert"
        ADJUST = "ADJUST", "Ajustement"
        CONSUME = "CONSUME", "Consommation mission"
        RESTOCK = "RESTOCK", "Réassort"

    structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="movements")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)

    type = models.CharField(max_length=16, choices=Type.choices)

    from_lot = models.ForeignKey(
        LotInstance, null=True, blank=True, on_delete=models.SET_NULL, related_name="movements_out"
    )
    to_lot = models.ForeignKey(
        LotInstance, null=True, blank=True, on_delete=models.SET_NULL, related_name="movements_in"
    )

    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, null=True, blank=True, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    reason = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="check_movement_qty_positive"),
            models.CheckConstraint(
                condition=(
                    Q(type="TRANSFER", from_lot__isnull=False, to_lot__isnull=False)
                    | Q(type="IN", to_lot__isnull=False)
                    | Q(type="OUT", from_lot__isnull=False)
                    | Q(type="ADJUST")
                    | Q(type="CONSUME", from_lot__isnull=False)
                    | Q(type="RESTOCK", to_lot__isnull=False)
                ),
                name="check_movement_lot_consistency",
            ),
        ]


class InventorySession(TimeStampedModel):
    structure = models.ForeignKey(Structure, on_delete=models.PROTECT, related_name="inventories")
    container = models.ForeignKey(Container, on_delete=models.PROTECT, related_name="inventories")

    validated_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="validated_inventories",
    )


class InventoryLine(TimeStampedModel):
    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)

    expected_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    counted_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["session", "item"], name="uniq_inventory_line_per_session_item"
            ),
            models.CheckConstraint(
                condition=Q(expected_qty__gte=0), name="check_expected_non_negative"
            ),
            models.CheckConstraint(
                condition=Q(counted_qty__gte=0), name="check_counted_non_negative"
            ),
        ]
