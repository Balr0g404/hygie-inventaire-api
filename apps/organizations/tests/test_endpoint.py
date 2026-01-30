import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.organizations.models import Membership, Organization, Structure


@pytest.mark.django_db
def test_organization_crud():
    user = get_user_model().objects.create_user(email="user@example.com", password="passw0rd!")
    client = APIClient()
    client.force_authenticate(user=user)

    create_resp = client.post(
        "/api/v1/organizations/",
        {"name": "Croix Rouge", "slug": "crf", "is_active": True},
        format="json",
    )
    assert create_resp.status_code == 201
    org_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/organizations/")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    update_resp = client.patch(f"/api/v1/organizations/{org_id}/", {"name": "CRF"}, format="json")
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "CRF"

    delete_resp = client.delete(f"/api/v1/organizations/{org_id}/")
    assert delete_resp.status_code == 204


@pytest.mark.django_db
def test_structure_and_membership_crud():
    user = get_user_model().objects.create_superuser(
        email="admin@example.com", password="passw0rd!"
    )
    other_user = get_user_model().objects.create_user(
        email="other@example.com", password="passw0rd!"
    )
    org = Organization.objects.create(name="Organisation", slug="org")
    client = APIClient()
    client.force_authenticate(user=user)

    structure_resp = client.post(
        "/api/v1/structures/",
        {"organization": org.id, "level": "LOCAL", "name": "UL 01"},
        format="json",
    )
    assert structure_resp.status_code == 201
    structure_id = structure_resp.json()["id"]

    structure_list = client.get("/api/v1/structures/")
    assert structure_list.status_code == 200
    assert len(structure_list.json()) == 1

    structure_update = client.patch(
        f"/api/v1/structures/{structure_id}/", {"code": "UL01"}, format="json"
    )
    assert structure_update.status_code == 200
    assert structure_update.json()["code"] == "UL01"

    membership_resp = client.post(
        "/api/v1/memberships/",
        {"user": other_user.id, "structure": structure_id, "role": "ADMIN"},
        format="json",
    )
    assert membership_resp.status_code == 201
    membership_id = membership_resp.json()["id"]

    membership_list = client.get("/api/v1/memberships/")
    assert membership_list.status_code == 200
    assert len(membership_list.json()) == 1

    membership_update = client.patch(
        f"/api/v1/memberships/{membership_id}/", {"is_fc_up_to_date": True}, format="json"
    )
    assert membership_update.status_code == 200
    assert membership_update.json()["is_fc_up_to_date"] is True

    delete_resp = client.delete(f"/api/v1/memberships/{membership_id}/")
    assert delete_resp.status_code == 204
    assert Membership.objects.count() == 0

    delete_structure = client.delete(f"/api/v1/structures/{structure_id}/")
    assert delete_structure.status_code == 204
    assert Structure.objects.count() == 0
