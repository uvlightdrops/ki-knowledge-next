"""Authenticated KI generation and explicit acceptance, separate from publication."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from ki_core.core.errors import AIError

from knext.config import ConfigurationError
from .ai_models import TextProposal
from .ai_service import ProposalError, accept, generate
from .forms import RevisionForm
from .importers.base import ImportFailure
from .models import ContentDocument
from .services import RevisionConflict


class ProposalForm(RevisionForm):
    instruction = forms.CharField(max_length=4000)
    context = forms.CharField(max_length=30000, required=False, strip=False)
    start = forms.IntegerField(min_value=0)
    end = forms.IntegerField(min_value=1)


@login_required
@require_POST
def propose(request, pk):
    document = get_object_or_404(ContentDocument, pk=pk)
    form = ProposalForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Auftrag oder Textauswahl ungültig.", "errors": form.errors.get_json_data()}, status=400)
    try:
        proposal = generate(document, request.user, form.cleaned_data)
    except RevisionConflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    except ProposalError as error:
        return JsonResponse({"error": str(error)}, status=422)
    except (ConfigurationError, AIError):
        return JsonResponse({"error": "KI-Konfiguration ungültig. Provider, Modell und Zugang prüfen."}, status=503)
    return JsonResponse({
        "id": str(proposal.pk), "text": proposal.text, "provider": proposal.provider,
        "model": proposal.model, "accept_url": reverse("content:ai-accept", args=[proposal.pk]),
        "discard_url": reverse("content:ai-discard", args=[proposal.pk]),
    })


@login_required
@require_POST
def accept_proposal(request, pk):
    proposal = get_object_or_404(TextProposal, pk=pk, created_by=request.user)
    form = RevisionForm(request.POST)
    text = request.POST.get("text", "")
    if not form.is_valid() or not text.strip() or len(text) > 200000:
        return JsonResponse({"error": "Ersatztext oder Arbeitsstand ungültig."}, status=400)
    try:
        accept(proposal, request.user, form.cleaned_data, text)
    except RevisionConflict as error:
        return JsonResponse({"error": str(error)}, status=409)
    except (ImportFailure, ValidationError) as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse({"url": reverse("content:editor", args=[proposal.document_id])})


@login_required
@require_POST
def discard_proposal(request, pk):
    proposal = get_object_or_404(TextProposal, pk=pk, created_by=request.user)
    if not TextProposal.objects.filter(pk=proposal.pk, status="ready").update(status="discarded"):
        return JsonResponse({"error": "Dieser Vorschlag ist nicht mehr offen."}, status=409)
    return JsonResponse({"discarded": True})
