"""Process durable import jobs with a single filesystem-locked worker."""

import signal
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from knext.content.importers.base import ImportFailure
from knext.content.jobs import claim_job, execute_job, recover_interrupted, worker_lock
from knext.content.models import ImportJob


class Command(BaseCommand):
    help = "Registrierung, Extraktion und Dateisystem-Abbilder aus der DB-Queue ausführen."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Wartende Jobs abarbeiten, dann beenden.")
        parser.add_argument("--job", type=str, help="Nur diese Job-UUID abarbeiten und beenden.")

    def handle(self, *args, **options):
        self.stopping = False
        previous = {sig: signal.signal(sig, self.request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
        try:
            self.run_queue(options)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)

    def request_stop(self, signum, frame):
        self.stopping = True

    def run_queue(self, options):
        import uuid

        job_id = options["job"]
        if job_id:
            try:
                job_id = uuid.UUID(job_id)
            except ValueError as error:
                raise CommandError("--job benötigt eine gültige UUID.") from error
        try:
            with worker_lock():
                recovered = recover_interrupted()
                self.stdout.write(f"{recovered} unterbrochene Jobs zur Prüfung markiert.")
                if job_id:
                    selected = ImportJob.objects.filter(pk=job_id).first()
                    if selected is None:
                        raise CommandError("Der ausgewählte Job existiert nicht.")
                    if selected.status != ImportJob.Status.QUEUED:
                        raise CommandError(f"Job ist nicht wartend ({selected.status}); gegebenenfalls ausdrücklich erneut einreihen.")
                while not self.stopping:
                    close_old_connections()
                    job = claim_job(job_id)
                    if job is None:
                        if options["once"] or job_id:
                            break
                        time.sleep(2)
                        continue
                    execute_job(job)
                    job.refresh_from_db()
                    self.stdout.write(f"{job.pk}: {job.status}" + (f" — {job.error}" if job.error else ""))
                    if job_id:
                        if job.status == ImportJob.Status.FAILED:
                            raise CommandError(f"Job {job.pk} fehlgeschlagen: {job.error}")
                        break
        except ImportFailure as error:
            raise CommandError(str(error)) from error
