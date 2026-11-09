import pytest
from django.contrib.auth.models import User
from django.test import Client

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def wiki(tmp_path, settings):
    (tmp_path / "ws").mkdir()
    settings.WISSENSWIKI = {"WORKSPACE": str(tmp_path / "ws")}


def test_root_redirects_to_wiki_and_login_uses_admin():
    client = Client()
    assert client.get("/").url == "/wiki/"
    assert client.get("/wiki/").url.startswith("/admin/login/")
    assert client.get("/favicon.ico").status_code == 204


def test_wiki_page_is_served_with_content_security_policy():
    client = Client()
    client.force_login(User.objects.create_user("anna"))
    response = client.get("/wiki/graph-header/")
    assert response.status_code == 200
    policy = response["Content-Security-Policy"]
    assert "default-src 'self'" in policy and "frame-ancestors 'none'" in policy
