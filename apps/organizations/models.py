# apps/organizations/models.py
from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)  # ex: "crf"
    is_active = models.BooleanField(default=True)


class Structure(models.Model):
    class Level(models.TextChoices):
        NATIONAL = "NATIONAL", "National"
        TERRITORIAL = "TERRITORIAL", "Territorial"
        LOCAL = "LOCAL", "Local"

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="structures"
    )
    level = models.CharField(max_length=20, choices=Level.choices)

    name = models.CharField(max_length=255)

    # arbre
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )

    # identifiants utiles (CRF)
    code = models.CharField(max_length=64, blank=True, default="")  # ex: code UL/DT, optionnel

    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "level"]),
            models.Index(fields=["parent"]),
        ]


class Membership(models.Model):
    class Role(models.TextChoices):
        VIEWER = "VIEWER", "Lecteur"
        REFERENT = "REFERENT", "Référent matériel"
        ADMIN = "ADMIN", "Admin structure"

    class Grade(models.TextChoices):
        STAGIAIRE = "STAGIAIRE", "Stagiaire"
        PSE1 = "PSE1", "PSE1"
        PSE2 = "PSE2", "PSE2"
        CI = "CI", "Chef d'Intervention"
        CDPE = "CDPE", "Chef DPS petite envergure"
        CDMGE = "CDMGE", "Chef DPS moyenne/grande envergure"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    structure = models.ForeignKey(Structure, on_delete=models.CASCADE, related_name="memberships")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    grade = models.CharField(max_length=20, choices=Grade.choices, default=Grade.STAGIAIRE)

    is_fc_up_to_date = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # utile pour historiser / audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        (
            models.UniqueConstraint(
                fields=["user", "structure"], name="uniq_membership_user_structure"
            ),
        )
        indexes = [
            models.Index(fields=["structure", "role"]),
            models.Index(fields=["structure", "is_active"]),
        ]
