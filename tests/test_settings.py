from pathlib import Path

import pytest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client


def test_documentation_domain_uses_repository_docs_by_default():
    docs = Path(__file__).resolve().parents[1] / "doc"
    domain = settings.WISSENSWIKI["DOMAINS"][0]

    assert Path(domain["source"]) == docs
    assert Path(domain["relations"]) == settings.VAR_DIR / "doc-relations"
    assert Path(domain["relations"]).is_dir()
    assert (docs / "README.md").is_file()


@pytest.mark.django_db
def test_documentation_domain_is_visible_in_the_wiki():
    client = Client()
    client.force_login(User.objects.create_user("writer"))

    response = client.get("/wiki/api", {"domain": "Dokumentation"})

    assert response.status_code == 200
    assert any(block["id"] == "doc:README.md" for block in response.json()["blocks"])
