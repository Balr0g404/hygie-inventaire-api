from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Membership, Organization, Structure

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("id", "name", "slug", "is_active")
        read_only_fields = ("id",)


class StructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Structure
        fields = ("id", "organization", "level", "name", "parent", "code", "is_active")
        read_only_fields = ("id",)


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = (
            "id",
            "user",
            "structure",
            "role",
            "grade",
            "is_fc_up_to_date",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")
