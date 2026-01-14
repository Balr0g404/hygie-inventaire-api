import os

from django.db import connections
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@extend_schema(tags=["Core"])
@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response({"status": "ok"})


@extend_schema(tags=["Core"])
@api_view(["GET"])
@permission_classes([AllowAny])
def ready(_request):
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1;")
    except Exception as e:
        return Response({"status": "down", "db": "down", "error": str(e)}, status=503)

    return Response({"status": "ok", "db": "ok"})


@extend_schema(tags=["Core"])
@api_view(["GET"])
@permission_classes([AllowAny])
def version(_request):
    return Response(
        {
            "name": os.getenv("APP_NAME", "hygie-api"),
            "version": os.getenv("APP_VERSION", "0.1.0"),
            "environment": os.getenv("DJANGO_SETTINGS_MODULE", ""),
        }
    )
