"""Append-only ORM boundary for stored source and content snapshots."""

from django.core.exceptions import ValidationError
from django.db import models


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Gespeicherte Quellen und Revisionen sind unveränderlich.")

    def delete(self):
        raise ValidationError("Gespeicherte Quellen und Revisionen dürfen nicht gelöscht werden.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Gespeicherte Quellen und Revisionen sind unveränderlich.")

    def bulk_create(self, objs, **kwargs):
        if kwargs.get("update_conflicts"):
            raise ValidationError("Unveränderliche Datensätze dürfen nicht überschrieben werden.")
        # Model validation and hashes must also apply to bulk inserts.
        objs = list(objs)
        for obj in objs:
            obj.prepare_snapshot()
        return super().bulk_create(objs, **kwargs)


class ImmutableModel(models.Model):
    objects = ImmutableQuerySet.as_manager()

    class Meta:
        abstract = True

    def prepare_snapshot(self) -> None:
        """Validate a new snapshot before persistence."""

    def save(self, *args, **kwargs) -> None:
        if kwargs.get("force_update") or kwargs.get("update_fields") or not self._state.adding:
            raise ValidationError("Gespeicherte Quellen und Revisionen sind unveränderlich.")
        if self.pk is not None and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Gespeicherte Quellen und Revisionen sind unveränderlich.")
        self.prepare_snapshot()
        kwargs["force_insert"] = True
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Gespeicherte Quellen und Revisionen dürfen nicht gelöscht werden.")
