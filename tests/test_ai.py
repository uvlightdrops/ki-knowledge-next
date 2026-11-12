"""KI requests remain bounded, user-owned proposals until explicit acceptance."""

from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from ki_core.core.errors import ProviderError
from ki_core.core.models import ChatResponse, Message, Role

from knext.config import APP, load_config
from knext.content.ai_models import TextProposal
from knext.content.models import ContentRevision
from knext.content.services import approve, import_upload, revise

pytestmark = pytest.mark.django_db
BODY = "Intro 😀.\n\n## Kapitel [kapitel]\n\nAlter Text.\n"


@pytest.fixture
def ai_environment():
    user = User.objects.create_user("ai-editor")
    run, _ = import_upload(SimpleUploadedFile("ai.md", BODY.encode()), "Books", user)
    document = run.documents.get()
    browser = Client()
    browser.force_login(user)
    config = load_config()
    config["apps"][APP]["ai"]["enabled"] = True
    config["llm"]["provider"] = "openai"
    config["llm"]["providers"]["openai"]["api_key"] = "synthetic-not-a-secret"
    client = Mock()
    client.chat.return_value = ChatResponse(
        message=Message(role=Role.ASSISTANT, content="Neuer Text."),
        provider="openai-compatible", model="gpt-4o-mini",
    )
    with patch("knext.content.ai_service.load_config", return_value=config), patch(
        "knext.content.ai_service.create_chat_client", return_value=client,
    ):
        yield document, user, browser, client, config


def payload(document, **overrides):
    start = BODY.index("Alter")
    return {
        "expected": document.revision_number, "title": document.title, "body": BODY,
        "start": start, "end": start + len("Alter Text."),
        "instruction": "Formuliere klarer.", "context": "", **overrides,
    }


def propose(environment, **overrides):
    document, _, browser, _, _ = environment
    return browser.post(f"/content/editor/{document.pk}/ai/", payload(document, **overrides))


def test_generate_sends_only_selected_text_and_explicit_context(ai_environment):
    document, user, browser, client, _ = ai_environment
    response = propose(ai_environment, context="Begriff: Erkenntnis")
    assert response.status_code == 200
    proposal = TextProposal.objects.get()
    assert proposal.created_by == user and proposal.status == "ready"
    assert ContentRevision.objects.filter(document=document).count() == 1
    request = client.chat.call_args.args[0]
    sent = request.messages[-1].content
    assert "Alter Text." in sent and "Begriff: Erkenntnis" in sent
    assert "Intro" not in sent and "kapitel" not in sent
    assert "synthetic-not-a-secret" not in response.content.decode()
    assert proposal.base_body == BODY
    page = BeautifulSoup(browser.get(f"/content/editor/{document.pk}/").content, "html.parser")
    assert page.select_one("#editor-ai").has_attr("hidden")
    assert page.select_one("#ai-proposal") is not None
    assert str(proposal.pk) in page.select_one("#editor-ai-pending").get_text()


def test_semantic_context_preset_is_explicit_and_persisted_in_provider_request(ai_environment):
    document, _, browser, client, _ = ai_environment
    page = BeautifulSoup(browser.get(f"/content/editor/{document.pk}/").content, "html.parser")
    option = page.select_one("#ai-context-preset option[value]:not([value=''])")
    assert option.get_text() == "Semantische Gliederung"
    context = option["value"]
    assert "Wissensverarbeitungssoftware" in context
    assert "prägnante Markdown-Überschriften" in context
    assert "Block-IDs und Metadaten bleiben erhalten" in context
    assert page.select_one("#ai-context").get_text() == ""
    client.chat.assert_not_called()
    assert propose(ai_environment, context=context).status_code == 200
    assert TextProposal.objects.get().context == context
    assert context in client.chat.call_args.args[0].messages[-1].content


def test_accept_saves_edited_proposal_without_changing_approval(ai_environment):
    document, user, browser, _, _ = ai_environment
    user.is_superuser = True
    user.save()
    approve(document, expected=1, user=user)
    approved_id = document.approved_revision_id
    result = propose(ai_environment).json()
    response = browser.post(result["accept_url"], {**payload(document), "text": "Manuell verbesserter Text."})
    assert response.status_code == 200
    document.refresh_from_db()
    assert document.revision_number == 2 and document.approved_revision_id == approved_id
    proposal = TextProposal.objects.get()
    assert proposal.accepted_revision.body == BODY.replace("Alter Text.", "Manuell verbesserter Text.")
    assert proposal.accepted_text == "Manuell verbesserter Text."
    assert proposal.accepted_revision.parent.body == BODY
    assert browser.post(result["accept_url"], {**payload(document), "text": "Doppelt"}).status_code == 409


def test_unsaved_buffer_is_backed_up_before_acceptance(ai_environment):
    document, _, browser, _, _ = ai_environment
    body = BODY + "\nUngespeicherte Gedanken."
    result = propose(ai_environment, body=body).json()
    response = browser.post(result["accept_url"], {**payload(document, body=body), "text": "Vorschlag."})
    assert response.status_code == 200
    revisions = list(document.revisions.order_by("number"))
    assert len(revisions) == 3
    assert revisions[1].body == body
    assert revisions[2].body == body.replace("Alter Text.", "Vorschlag.")


@pytest.mark.parametrize("change", ["buffer", "head", "title"])
def test_stale_proposal_rejects_acceptance_and_preserves_input(ai_environment, change):
    document, user, browser, _, _ = ai_environment
    result = propose(ai_environment).json()
    data = payload(document)
    if change == "head":
        revise(document, expected=1, title=document.title, body=BODY + "Concurrent.", user=user)
    else:
        data["body" if change == "buffer" else "title"] += "Changed"
    count = ContentRevision.objects.count()
    response = browser.post(result["accept_url"], {**data, "text": "New"})
    assert response.status_code == 409
    assert ContentRevision.objects.count() == count
    assert TextProposal.objects.get().status == "ready"


def test_invalid_result_rolls_back_unsaved_backup_and_acceptance(ai_environment):
    document, _, browser, _, _ = ai_environment
    body = BODY + "unsaved"
    result = propose(ai_environment, body=body, start=0, end=len(body)).json()
    response = browser.post(result["accept_url"], {
        **payload(document, body=body), "text": "---\nsecret: value\n---\ntext",
    })
    assert response.status_code == 400
    assert document.revisions.count() == 1
    assert TextProposal.objects.get().status == "ready"


def test_provider_failure_has_no_success_fallback_or_sensitive_error(ai_environment):
    _, _, _, client, _ = ai_environment
    client.chat.side_effect = ProviderError("token=private-content")
    response = propose(ai_environment)
    assert response.status_code == 422
    assert "private-content" not in response.content.decode()
    proposal = TextProposal.objects.get()
    assert proposal.status == "failed"
    assert "private-content" not in proposal.error
    assert ContentRevision.objects.count() == 1


@pytest.mark.parametrize("text", ["", " " * 3, None])
def test_empty_provider_results_are_failed(ai_environment, text):
    _, _, _, client, _ = ai_environment
    client.chat.return_value = ChatResponse(Message(Role.ASSISTANT, text), "openai", "test")
    assert propose(ai_environment).status_code == 422
    assert TextProposal.objects.get().status == "failed"


def test_discard_and_user_isolation_and_csrf(ai_environment):
    document, _, browser, _, _ = ai_environment
    result = propose(ai_environment).json()
    other = Client()
    other.force_login(User.objects.create_user("other"))
    assert other.post(result["accept_url"], {**payload(document), "text": "New"}).status_code == 404
    assert other.post(result["discard_url"]).status_code == 404
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(User.objects.get(username="ai-editor"))
    assert csrf.post(f"/content/editor/{document.pk}/ai/", payload(document)).status_code == 403
    assert browser.post(result["discard_url"]).status_code == 200
    assert TextProposal.objects.get().status == "discarded"
    assert document.revisions.count() == 1


@pytest.mark.parametrize("options", [
    {"start": 2, "end": 2}, {"end": 9999}, {"instruction": ""}, {"context": "a" * 30001},
])
def test_invalid_scope_is_rejected_before_provider_request(ai_environment, options):
    _, _, _, client, _ = ai_environment
    assert propose(ai_environment, **options).status_code in {400, 422}
    client.chat.assert_not_called()
    assert not TextProposal.objects.exists()


def test_disabled_auto_and_oversized_input_are_explicit(ai_environment):
    _, _, _, client, config = ai_environment
    config["apps"][APP]["ai"]["enabled"] = False
    assert propose(ai_environment).status_code == 422
    config["apps"][APP]["ai"]["enabled"] = True
    config["llm"]["provider"] = "auto"
    assert propose(ai_environment).status_code == 422
    config["llm"]["provider"] = "openai"
    config["apps"][APP]["ai"]["max_input_chars"] = 2
    assert propose(ai_environment).status_code == 422
    client.chat.assert_not_called()


def test_five_requests_per_minute_limit_does_not_call_provider_again(ai_environment):
    _, _, _, client, _ = ai_environment
    for _ in range(5):
        assert propose(ai_environment).status_code == 200
    response = propose(ai_environment)
    assert response.status_code == 422
    assert "fünf" in response.json()["error"]
    assert client.chat.call_count == 5


def test_pending_proposal_is_only_reloaded_for_its_author(ai_environment):
    document, _, _, _, _ = ai_environment
    propose(ai_environment)
    other = Client()
    other.force_login(User.objects.create_user("reader"))
    assert other.get(f"/content/editor/{document.pk}/").context["ai_pending"] is None


def test_neutral_connection_check_never_loads_documents(ai_environment, capsys):
    _, _, _, client, _ = ai_environment
    client.chat.return_value = ChatResponse(Message(Role.ASSISTANT, "OK"), "openai", "test")
    with patch("knext.content.management.commands.content_ai_check.create_chat_client", return_value=client):
        call_command("content_ai_check")
    assert ": OK" in capsys.readouterr().out
    assert "Connection test" in client.chat.call_args.args[0].messages[0].content
    assert not TextProposal.objects.exists()
