from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inventory.models import (
    Batch,
    Container,
    Item,
    Location,
    LotInstance,
    LotTemplate,
    LotTemplateItem,
    Site,
    StockLine,
)
from apps.organizations.models import Membership, Organization, Structure


@dataclass(frozen=True)
class UserSeed:
    email: str
    password: str
    full_name: str
    role: str
    is_staff: bool = False
    is_superuser: bool = False
    is_active: bool = True


class Command(BaseCommand):
    help = "Seed demo data for Croix-Rouge française (CRF)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data first (dev only).",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        flush = bool(options["flush"])

        if flush:
            self._flush_demo_data()

        org = self._seed_organization()

        structures = self._seed_structures(org)
        users = self._seed_users()
        self._seed_memberships(users, structures)

        items = self._seed_items(org)
        sites = self._seed_sites(structures)
        locations = self._seed_locations(sites)
        containers = self._seed_containers(structures, locations)

        templates = self._seed_lot_templates(org)
        self._seed_lot_template_items(templates, items)

        lot_instances = self._seed_lot_instances(templates, containers)
        batches = self._seed_batches(items)
        self._seed_stock_lines(lot_instances, items, batches)

        self.stdout.write(self.style.SUCCESS("✅ Seed demo CRF terminé."))

    # ---------------------------------------------------------------------
    # Flush (dev only)
    # ---------------------------------------------------------------------
    def _flush_demo_data(self) -> None:
        """
        Flush only what we seed here. Keep it conservative to avoid surprises.
        """
        self.stdout.write(self.style.WARNING("⚠️  Flush des données demo (CRF)…"))

        # Inventory
        StockLine.objects.all().delete()
        Batch.objects.all().delete()
        LotInstance.objects.all().delete()
        LotTemplateItem.objects.all().delete()
        LotTemplate.objects.all().delete()
        Container.objects.all().delete()
        Location.objects.all().delete()
        Site.objects.all().delete()
        Item.objects.all().delete()

        # Organizations
        Membership.objects.all().delete()
        Structure.objects.all().delete()
        Organization.objects.filter(slug="crf").delete()

        # Accounts (only demo users by email domain)
        User = get_user_model()
        User.objects.filter(email__endswith="@croix-rouge.fr").delete()

    # ---------------------------------------------------------------------
    # Organizations
    # ---------------------------------------------------------------------
    def _seed_organization(self) -> Organization:
        org, _ = Organization.objects.update_or_create(
            slug="crf",
            defaults={"name": "Croix-Rouge française", "is_active": True},
        )
        self.stdout.write(f"🏢 Organization: {org.name} ({org.slug})")
        return org

    def _seed_structures(self, org: Organization) -> dict[str, Structure]:
        # Create in hierarchy order
        national, _ = Structure.objects.update_or_create(
            organization=org,
            code="CRF",
            defaults={
                "level": "NATIONAL",
                "name": "Croix-Rouge française",
                "parent": None,
                "is_active": True,
            },
        )

        territorial, _ = Structure.objects.update_or_create(
            organization=org,
            code="DT01",
            defaults={
                "level": "TERRITORIAL",
                "name": "Direction territoriale de l'Ain",
                "parent": national,
                "is_active": True,
            },
        )

        ul01, _ = Structure.objects.update_or_create(
            organization=org,
            code="UL01",
            defaults={
                "level": "LOCAL",
                "name": "Unité locale du bassin-burgien",
                "parent": territorial,
                "is_active": True,
            },
        )

        ul02, _ = Structure.objects.update_or_create(
            organization=org,
            code="UL02",
            defaults={
                "level": "LOCAL",
                "name": "Unité locale du Bugey",
                "parent": territorial,
                "is_active": True,
            },
        )

        self.stdout.write("🏗️  Structures: CRF / DT01 / UL01 / UL02")
        return {"CRF": national, "DT01": territorial, "UL01": ul01, "UL02": ul02}

    # ---------------------------------------------------------------------
    # Accounts
    # ---------------------------------------------------------------------
    def _seed_users(self) -> dict[str, Any]:
        User = get_user_model()

        seeds = [
            UserSeed(
                email="admin@croix-rouge.fr",
                password="adminadmin",
                full_name="Audran Scieur",
                role="ADMIN_GLOBAL",
                is_staff=True,
                is_superuser=True,
            ),
            UserSeed(
                email="jeremy.vernadet@croix-rouge.fr",
                password="referent",
                full_name="Jérémy Vernadet",
                role="REFERENT",
            ),
            UserSeed(
                email="alex.dupont@croix-rouge.fr",
                password="utilisateur",
                full_name="Alex Dupont",
                role="MEMBER",
            ),
            UserSeed(
                email="lea.martin@croix-rouge.fr",
                password="utilisateur",
                full_name="Léa Martin",
                role="MEMBER",
            ),
            UserSeed(
                email="jean.leroy@croix-rouge.fr",
                password="utilisateur",
                full_name="Jean Leroy",
                role="MEMBER",
            ),
            UserSeed(
                email="chloe.bonnin@croix-rouge.fr",
                password="utilisateur",
                full_name="Chloé Bonnin",
                role="MEMBER",
            ),
            UserSeed(
                email="paul.gauthier@croix-rouge.fr",
                password="utilisateur",
                full_name="Paul Gauthier",
                role="MEMBER",
            ),
        ]

        users: dict[str, Any] = {}
        for s in seeds:
            user, created = User.objects.get_or_create(email=s.email)
            user.full_name = s.full_name
            user.role = s.role
            user.is_staff = s.is_staff
            user.is_superuser = s.is_superuser
            user.is_active = s.is_active

            # Always ensure password matches the seed (dev/demo)
            user.set_password(s.password)
            user.save()

            users[s.email] = user
            self.stdout.write(f"👤 User: {s.email} ({'created' if created else 'updated'})")

        return users

    # ---------------------------------------------------------------------
    # Memberships
    # ---------------------------------------------------------------------
    def _seed_memberships(self, users: dict[str, Any], structures: dict[str, Structure]) -> None:
        def upsert(email: str, structure_code: str, role: str, grade: str, is_fc: bool) -> None:
            user = users[email]
            structure = structures[structure_code]
            Membership.objects.update_or_create(
                user=user,
                structure=structure,
                defaults={
                    "role": role,
                    "grade": grade,
                    "is_fc_up_to_date": is_fc,
                    "is_active": True,
                },
            )

        upsert("admin@croix-rouge.fr", "CRF", "ADMIN", "CDMGE", True)
        upsert("jeremy.vernadet@croix-rouge.fr", "UL01", "REFERENT", "CI", True)
        upsert("alex.dupont@croix-rouge.fr", "UL02", "VIEWER", "PSE1", False)
        upsert("lea.martin@croix-rouge.fr", "UL01", "ADMIN", "CDPE", True)
        upsert("jean.leroy@croix-rouge.fr", "UL01", "VIEWER", "PSE2", True)
        upsert("chloe.bonnin@croix-rouge.fr", "UL02", "REFERENT", "PSE2", False)
        upsert("paul.gauthier@croix-rouge.fr", "UL02", "VIEWER", "STAGIAIRE", True)

        self.stdout.write("🤝 Memberships: OK")

    # ---------------------------------------------------------------------
    # Inventory - Items
    # ---------------------------------------------------------------------
    def _seed_items(self, org: Organization) -> dict[str, Item]:
        def upsert(
            sku: str,
            name: str,
            unit: str,
            category: str,
            is_consumable: bool,
            requires_expiry: bool,
            requires_lot_number: bool,
        ) -> Item:
            item, _ = Item.objects.update_or_create(
                organization=org,
                sku=sku,
                defaults={
                    "name": name,
                    "unit": unit,
                    "category": category,
                    "is_consumable": is_consumable,
                    "requires_expiry": requires_expiry,
                    "requires_lot_number": requires_lot_number,
                    "is_active": True,
                },
            )
            return item

        items = {
            "GANTS": upsert("CRF-GNT-NIT", "Gants nitrile", "paire", "Protection", True, False, False),
            "O2_2L": upsert("CRF-O2-2L", "Bouteille d'oxygène 2L", "unité", "Respiration", False, False, False),
            "FFP2": upsert("CRF-FFP2", "Masque FFP2", "unité", "Protection", True, False, False),
            "PAN_COMP": upsert("CRF-PAN-COMP", "Pansement compressif d'urgence", "unité", "Trauma", True, False, False),
            "COUV": upsert("CRF-COUV-ISO", "Couverture isotherme", "unité", "Divers", True, False, False),
            "GEL": upsert("CRF-GEL-HA", "Gel hydroalcoolique", "flacon", "Protection", True, True, True),
        }

        self.stdout.write(f"📦 Items: {len(items)}")
        return items

    # ---------------------------------------------------------------------
    # Inventory - Sites / Locations / Containers
    # ---------------------------------------------------------------------
    def _seed_sites(self, structures: dict[str, Structure]) -> dict[str, Site]:
        site_ul01, _ = Site.objects.update_or_create(
            structure=structures["UL01"],
            name="Local UL bassin-burgien",
            defaults={"address": "1 Avenue des belges, 01000 Bourg-en-Bresse"},
        )
        site_ul02, _ = Site.objects.update_or_create(
            structure=structures["UL02"],
            name="Local UL Ambérieu",
            defaults={"address": "5 avenue des Secours, 01500 Ambérieu-en-Bugey"},
        )
        self.stdout.write("📍 Sites: OK")
        return {"UL01": site_ul01, "UL02": site_ul02}

    def _seed_locations(self, sites: dict[str, Site]) -> dict[str, Location]:
        loc1, _ = Location.objects.update_or_create(
            site=sites["UL01"],
            name="Armoire principale",
            defaults={"location_type": "Stock"},
        )
        loc2, _ = Location.objects.update_or_create(
            site=sites["UL01"],
            name="VPSP 1",
            defaults={"location_type": "Véhicule"},
        )
        loc3, _ = Location.objects.update_or_create(
            site=sites["UL02"],
            name="Armoire d'urgence",
            defaults={"location_type": "Stock"},
        )
        loc4, _ = Location.objects.update_or_create(
            site=sites["UL02"],
            name="Remorque logistique",
            defaults={"location_type": "Véhicule"},
        )
        self.stdout.write("🗄️  Locations: OK")
        return {"UL01_ARM": loc1, "UL01_VPSP": loc2, "UL02_ARM": loc3, "UL02_REM": loc4}

    def _seed_containers(
        self, structures: dict[str, Structure], locations: dict[str, Location]
    ) -> dict[str, Container]:
        def upsert(identifier: str, structure_code: str, location_key: str, type_: str, label: str) -> Container:
            container, _ = Container.objects.update_or_create(
                identifier=identifier,
                defaults={
                    "structure": structures[structure_code],
                    "location": locations[location_key],
                    "type": type_,
                    "label": label,
                    "is_active": True,
                },
            )
            return container

        containers = {
            "UL01_BAG_INT": upsert("UL01-BAG-INT-01", "UL01", "UL01_ARM", "BAG_INTERVENTION", "Sac intervention principal"),
            "UL01_BAG_OXY": upsert("UL01-BAG-OXY-01", "UL01", "UL01_ARM", "BAG_OXY", "Sac oxygénothérapie"),
            "UL01_RES": upsert("UL01-RES-01", "UL01", "UL01_VPSP", "RESERVE_CASE", "Malle réserve"),
            "UL02_BAG_PS": upsert("UL02-BAG-PS-01", "UL02", "UL02_ARM", "BAG_FIRST_AID", "Sac premiers secours"),
            "UL02_O2": upsert("UL02-O2-01", "UL02", "UL02_REM", "OXYGEN_CYLINDER", "Bouteille O2 terrain"),
            "UL02_VPSP": upsert("UL02-VPSP-01", "UL02", "UL02_REM", "VEHICLE_VPSP", "VPSP 01"),
        }
        self.stdout.write(f"🎒 Containers: {len(containers)}")
        return containers

    # ---------------------------------------------------------------------
    # Inventory - Templates / Instances
    # ---------------------------------------------------------------------
    def _seed_lot_templates(self, org: Organization) -> dict[str, LotTemplate]:
        def upsert(code: str, name: str, version: str) -> LotTemplate:
            tpl, _ = LotTemplate.objects.update_or_create(
                organization=org,
                code=code,
                defaults={"name": name, "version": version, "is_active": True},
            )
            return tpl

        templates = {
            "LOT_A": upsert("LOT_A", "Lot A secours", "CRF-2024-001"),
            "LOT_B": upsert("LOT_B", "Lot B premiers secours", "CRF-2024-001"),
            "VPSP": upsert("VPSP", "Lot VPSP", "CRF-2024-001"),
        }
        self.stdout.write("🧰 LotTemplates: OK")
        return templates

    def _seed_lot_template_items(self, templates: dict[str, LotTemplate], items: dict[str, Item]) -> None:
        def upsert(template_key: str, group: str, item_key: str, expected_qty: str, notes: str) -> None:
            LotTemplateItem.objects.update_or_create(
                template=templates[template_key],
                group=group,
                item=items[item_key],
                defaults={"expected_qty": expected_qty, "notes": notes},
            )

        upsert("LOT_A", "PROTECTION", "GANTS", "20", "Gants nitrile taille mixte")
        upsert("LOT_A", "WOUNDS", "PAN_COMP", "6", "Pansements compressifs")
        upsert("LOT_A", "DIVERS", "COUV", "4", "Couvertures isothermes")
        upsert("LOT_B", "PROTECTION", "FFP2", "15", "Masques FFP2")
        upsert("LOT_B", "PROTECTION", "GEL", "3", "Gel hydroalcoolique")
        upsert("VPSP", "RESUSC", "O2_2L", "1", "Bouteille O2 pour VPSP")

        self.stdout.write("📋 LotTemplateItems: OK")

    def _seed_lot_instances(
        self, templates: dict[str, LotTemplate], containers: dict[str, Container]
    ) -> dict[str, LotInstance]:
        def upsert(template_key: str, container_key: str) -> LotInstance:
            li, _ = LotInstance.objects.update_or_create(
                template=templates[template_key],
                container=containers[container_key],
                defaults={"status": "READY", "last_checked_at": None, "next_check_due_at": None},
            )
            return li

        lot_instances = {
            "LI_1": upsert("LOT_A", "UL01_BAG_INT"),
            "LI_2": upsert("LOT_B", "UL01_BAG_OXY"),
            "LI_3": upsert("LOT_B", "UL02_BAG_PS"),
            "LI_4": upsert("VPSP", "UL02_VPSP"),
        }
        self.stdout.write("✅ LotInstances: OK")
        return lot_instances

    # ---------------------------------------------------------------------
    # Inventory - Batches / Stock lines
    # ---------------------------------------------------------------------
    def _seed_batches(self, items: dict[str, Item]) -> dict[str, Batch]:
        b1, _ = Batch.objects.update_or_create(
            item=items["GEL"],
            lot_number="GEL-2024-01",
            defaults={"expires_at": "2026-06-30"},
        )
        b2, _ = Batch.objects.update_or_create(
            item=items["FFP2"],
            lot_number="FFP2-2024-07",
            defaults={"expires_at": "2027-01-31"},
        )
        self.stdout.write("🧪 Batches: OK")
        return {"GEL": b1, "FFP2": b2}

    def _seed_stock_lines(
        self,
        lot_instances: dict[str, LotInstance],
        items: dict[str, Item],
        batches: dict[str, Batch],
    ) -> None:
        def upsert(li_key: str, item_key: str, qty: str, batch_key: str | None = None) -> None:
            StockLine.objects.update_or_create(
                lot_instance=lot_instances[li_key],
                item=items[item_key],
                batch=batches[batch_key] if batch_key else None,
                defaults={"quantity": qty},
            )

        upsert("LI_1", "GANTS", "18")
        upsert("LI_1", "PAN_COMP", "6")
        upsert("LI_1", "COUV", "4")

        upsert("LI_2", "FFP2", "14", "FFP2")
        upsert("LI_2", "GEL", "3", "GEL")

        upsert("LI_3", "FFP2", "10", "FFP2")
        upsert("LI_3", "GEL", "2", "GEL")

        upsert("LI_4", "O2_2L", "1")

        self.stdout.write("📈 StockLines: OK")
