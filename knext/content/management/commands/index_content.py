"""Backfill derived graph resources without changing historical revisions."""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from knext.content.graph_services import index_revision
from knext.content.importers.base import ImportFailure
from knext.content.models import ContentRevision


class Command(BaseCommand):
    help = "Ressourcen und Quellgliederungen vorhandener Revisionen wiederholbar ergänzen."

    def handle(self, *args, **options) -> None:
        count = 0
        for revision in ContentRevision.objects.filter(outline__isnull=True).order_by("document_id", "number").iterator():
            try:
                index_revision(revision)
            except (ImportFailure, ValidationError) as error:
                raise CommandError(f"Revision {revision.pk} ({revision.document_id}, r{revision.number}): {error}") from error
            count += 1
        self.stdout.write(self.style.SUCCESS(f"{count} Revisionen indexiert."))
