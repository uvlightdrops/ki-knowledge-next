"""Readiness checks without exposing database or configuration details."""

import logging

from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


@require_safe
def ready(request: HttpRequest) -> JsonResponse:
    """Return ready only when the database is reachable and migrations are applied."""
    try:
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
    except DatabaseError as exc:
        logger.warning("Readiness database check failed (%s).", type(exc).__name__)
        return JsonResponse({"status": "not_ready"}, status=503)
    if pending:
        logger.warning("Readiness failed: pending database migrations; run manage.py migrate.")
        return JsonResponse({"status": "not_ready"}, status=503)
    return JsonResponse({"status": "ready"})
