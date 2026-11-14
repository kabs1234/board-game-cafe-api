"""API-wide exception handling."""
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def handle_api_exception(exc: Exception, context: dict) -> Response | None:
    """Extend DRF's handler: deleting a still-referenced row returns 409 Conflict."""
    if isinstance(exc, ProtectedError):
        return Response(
            {"detail": "Cannot delete: other records still reference this object."},
            status=status.HTTP_409_CONFLICT,
        )
    return exception_handler(exc, context)
