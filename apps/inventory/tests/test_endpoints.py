import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.inventory.models import InventoryLine, StockMovement
from apps.organizations.models import Membership, Organization, Structure


@pytest.mark.django_db
def test_inventory_crud_endpoints():
    user = get_user_model().objects.create_user(email="user@example.com", password="passw0rd!")
    client = APIClient()
    client.force_authenticate(user=user)

    org = Organization.objects.create(name="Organisation", slug="org")
    structure = Structure.objects.create(organization=org, level="LOCAL", name="UL 01")
    Membership.objects.create(
        user=user,
        structure=structure,
        role=Membership.Role.REFERENT,
    )

    item_resp = client.post(
        "/api/v1/items/",
        {"organization": org.id, "name": "Gants nitrile", "unit": "paire"},
        format="json",
    )
    assert item_resp.status_code == 201
    item_id = item_resp.json()["id"]

    site_resp = client.post(
        "/api/v1/sites/",
        {"structure": structure.id, "name": "Garage"},
        format="json",
    )
    assert site_resp.status_code == 201
    site_id = site_resp.json()["id"]

    location_resp = client.post(
        "/api/v1/locations/",
        {"site": site_id, "name": "Armoire 1"},
        format="json",
    )
    assert location_resp.status_code == 201
    location_id = location_resp.json()["id"]

    container_resp = client.post(
        "/api/v1/containers/",
        {
            "structure": structure.id,
            "location": location_id,
            "type": "BAG_FIRST_AID",
            "identifier": "SAC-01",
        },
        format="json",
    )
    assert container_resp.status_code == 201
    container_id = container_resp.json()["id"]

    template_resp = client.post(
        "/api/v1/lot-templates/",
        {"organization": org.id, "code": "LOT_A", "name": "Lot A", "version": "2024"},
        format="json",
    )
    assert template_resp.status_code == 201
    template_id = template_resp.json()["id"]

    template_item_resp = client.post(
        "/api/v1/lot-template-items/",
        {
            "template": template_id,
            "group": "PROTECTION",
            "item": item_id,
            "expected_qty": "10",
        },
        format="json",
    )
    assert template_item_resp.status_code == 201

    lot_instance_resp = client.post(
        "/api/v1/lot-instances/",
        {"template": template_id, "container": container_id, "status": "READY"},
        format="json",
    )
    assert lot_instance_resp.status_code == 201
    lot_instance_id = lot_instance_resp.json()["id"]

    batch_resp = client.post(
        "/api/v1/batches/",
        {"item": item_id, "lot_number": "LOT-1"},
        format="json",
    )
    assert batch_resp.status_code == 201
    batch_id = batch_resp.json()["id"]

    stock_line_resp = client.post(
        "/api/v1/stock-lines/",
        {
            "lot_instance": lot_instance_id,
            "item": item_id,
            "batch": batch_id,
            "quantity": "5",
        },
        format="json",
    )
    assert stock_line_resp.status_code == 201

    movement_resp = client.post(
        "/api/v1/stock-movements/",
        {
            "structure": structure.id,
            "created_by": user.id,
            "type": "IN",
            "to_lot": lot_instance_id,
            "item": item_id,
            "batch": batch_id,
            "quantity": "2",
            "reason": "approvisionnement",
        },
        format="json",
    )
    assert movement_resp.status_code == 201
    movement_id = movement_resp.json()["id"]

    session_resp = client.post(
        "/api/v1/inventory-sessions/",
        {"structure": structure.id, "container": container_id},
        format="json",
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    line_resp = client.post(
        "/api/v1/inventory-lines/",
        {"session": session_id, "item": item_id, "expected_qty": "10", "counted_qty": "9"},
        format="json",
    )
    assert line_resp.status_code == 201
    line_id = line_resp.json()["id"]

    list_resp = client.get("/api/v1/items/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    patch_resp = client.patch(f"/api/v1/items/{item_id}/", {"sku": "GANTS-001"}, format="json")
    assert patch_resp.status_code == 200
    assert patch_resp.json()["sku"] == "GANTS-001"

    delete_line = client.delete(f"/api/v1/inventory-lines/{line_id}/")
    assert delete_line.status_code == 204
    assert InventoryLine.objects.count() == 0

    delete_movement = client.delete(f"/api/v1/stock-movements/{movement_id}/")
    assert delete_movement.status_code == 204
    assert StockMovement.objects.count() == 0
