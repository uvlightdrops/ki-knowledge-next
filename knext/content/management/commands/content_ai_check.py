"""Explicit neutral provider connection check without document context."""

from django.core.management.base import BaseCommand, CommandError
from ki_core.chat import create_chat_client
from ki_core.core.errors import AIError
from ki_core.core.models import ChatRequest, Message, Role

from knext.config import ConfigurationError
from knext.content.ai_service import ProposalError, ai_settings


class Command(BaseCommand):
    help = "Konfigurierten KI-Zugang mit neutralem Testtext prüfen; keine Dokumente senden."
    requires_system_checks = []

    def handle(self, *args, **options):
        try:
            config, selected = ai_settings()
            response = create_chat_client(config).chat(ChatRequest(messages=[
                Message(role=Role.USER, content="Connection test. Reply with exactly: OK"),
            ]))
            if response.message.content.strip() != "OK":
                raise ProposalError("Verbindung antwortet, aber der neutrale Test wurde nicht bestätigt.")
        except (AIError, ConfigurationError, ProposalError, ValueError, KeyError, IndexError, TypeError) as error:
            raise CommandError(
                f"KI-Test fehlgeschlagen ({type(error).__name__}); Konfiguration und Zugang prüfen.",
            ) from None
        self.stdout.write(f'{selected["provider"]} · {selected["model"]}: OK')
