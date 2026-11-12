import json
import os
import subprocess
import sys

import pytest
import yaml

from knext.config import APP, PROJECT_ROOT, load_config
from scripts import setup_u7


def test_answers_survive_restart_as_editable_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "example.org")
    answers = setup_u7.SetupAnswers()
    assert answers.ask("domain", "Domain", "", setup_u7.domain_name) == "example.org"
    assert answers.path.stat().st_mode & 0o777 == 0o600
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt: prompts.append(prompt) or "")
    restarted = setup_u7.SetupAnswers()
    assert restarted.ask("domain", "Domain", "", setup_u7.domain_name) == "example.org"
    assert "[example.org]" in prompts[0]
    monkeypatch.setattr("builtins.input", lambda prompt: "new.example.org")
    assert restarted.ask("domain", "Domain", "", setup_u7.domain_name) == "new.example.org"
    assert setup_u7.SetupAnswers().values == {"domain": "new.example.org"}


def test_invalid_answer_retries_without_losing_saved_answers(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    replies = iter(["example.org", "invalid", "80", "9000"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
    answers = setup_u7.SetupAnswers()
    answers.ask("domain", "Domain", "", setup_u7.domain_name)
    assert answers.ask("port", "Port", "8780", setup_u7.web_port) == "9000"
    assert setup_u7.SetupAnswers().values == {"domain": "example.org", "port": "9000"}
    assert "Ungültige Eingabe" in capsys.readouterr().err
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("contents", ['{"password": "no"}', '[]', '{"domain": 42}', '{'])
def test_invalid_answer_file_is_not_silently_discarded(tmp_path, monkeypatch, contents):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    path = tmp_path / ".setup-u7-answers.json"
    path.write_text(contents)
    with pytest.raises((setup_u7.SetupError, ValueError)):
        setup_u7.SetupAnswers()
    assert path.read_text() == contents


def test_interrupt_keeps_previously_confirmed_answers(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    replies = iter(["example.org"])

    def answer(prompt):
        try:
            return next(replies)
        except StopIteration:
            raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", answer)
    previous_umask = os.umask(0o077)
    try:
        assert setup_u7.main() == 1
    finally:
        os.umask(previous_umask)
    assert setup_u7.SetupAnswers().values == {"domain": "example.org"}


def test_directory_answers_are_revalidated_on_restart(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    monkeypatch.setattr(setup_u7.Path, "home", lambda: tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    answers = setup_u7.SetupAnswers()
    for key in ("workspace", "data"):
        assert answers.ask(key, key, str(tmp_path / key), setup_u7.private_path) == str(tmp_path / key)
    (tmp_path / "workspace").write_text("not a directory")
    replies = iter(["", str(tmp_path / "other")])
    monkeypatch.setattr("builtins.input", lambda prompt: next(replies))
    restarted = setup_u7.SetupAnswers()
    assert restarted.ask("workspace", "Wiki", "", setup_u7.private_path) == str(tmp_path / "other")
    assert restarted.values["data"] == str(tmp_path / "data")


def test_failed_answer_save_preserves_previous_file(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "example.org")
    answers = setup_u7.SetupAnswers()
    answers.ask("domain", "Domain", "", setup_u7.domain_name)
    previous = answers.path.read_text()

    def fail_replace(source, destination):
        raise OSError("disk unavailable")

    monkeypatch.setattr(setup_u7.os, "replace", fail_replace)
    monkeypatch.setattr("builtins.input", lambda prompt: "other.example.org")
    with pytest.raises(OSError, match="disk unavailable"):
        answers.ask("domain", "Domain", "", setup_u7.domain_name)
    assert answers.path.read_text() == previous
    assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("name", ["", "*.example.org", "https://example.org", "example.org/path",
                                  "example.org:443", "-invalid.example", "a..example"])
def test_domain_rejects_non_host_names(name):
    with pytest.raises(setup_u7.SetupError):
        setup_u7.domain_name(name)


def test_existing_domain_backends_are_not_overwritten():
    assert setup_u7.backend_conflicts("example.org", "/ apache\nexample.org/static apache")
    assert not setup_u7.backend_conflicts("example.org", "/ apache\nother.example.org/ http:8000")


def test_proxy_probe_rejects_spoofing_and_removes_temporary_route(monkeypatch):
    commands = []

    def run(*command, capture=False):
        commands.append(command)
        return ""

    def request(domain, path, *, secure, headers=None):
        if not secure:
            return 301, {"Location": f"https://{domain}{path}"}, b""
        supplied = headers.get("X-Forwarded-Proto") if headers else "https"
        return 200, {}, json.dumps([supplied]).encode()

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "request", request)
    with pytest.raises(setup_u7.SetupError, match="überschreibt"):
        setup_u7.verify_proxy("example.org", set())
    assert commands[-1][:4] == ("uberspace", "web", "backend", "del")
    assert commands[-1][4] == commands[1][4]


def test_proxy_probe_requires_https_redirect_and_overwritten_header(monkeypatch):
    commands = []

    def run(*command, capture=False):
        commands.append(command)
        return ""

    def request(domain, path, *, secure, headers=None):
        if not secure:
            return 301, {"Location": f"https://{domain}{path}"}, b""
        return 200, {}, b'["https"]'

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "request", request)
    setup_u7.verify_proxy("example.org", set())
    assert commands[-1][:4] == ("uberspace", "web", "backend", "del")


def test_config_is_private_valid_and_supervisor_uses_worker_timeout(tmp_path, monkeypatch):
    from stackctl.spec import build_stack

    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    defaults = tmp_path / "config/defaults"
    defaults.mkdir(parents=True)
    (defaults / "stack.yaml").write_text((PROJECT_ROOT / "config/defaults/stack.yaml").read_text())
    setup_u7.write_config("example.org", 8780, tmp_path / "static", tmp_path / "var",
                          tmp_path / "wiki", tmp_path / "data")
    for path in (tmp_path / "ki.yaml", tmp_path / "creds.yaml"):
        assert path.stat().st_mode & 0o777 == 0o600
    config = load_config(tmp_path)
    assert config["apps"][APP]["django"]["https_proxy"] is True
    assert config["apps"][APP]["django"]["debug"] is False
    stack = build_stack(config["stack"], tmp_path)
    assert stack.target == "supervisord"
    assert stack.service("import-worker").stop_timeout == 300
    assert stack.service("django").command[-1] == "120"
    assert yaml.safe_load((tmp_path / "creds.yaml").read_text())["apps"][APP]["django"]["secret_key"]
    with pytest.raises(FileExistsError):
        setup_u7.write_config("example.org", 8780, tmp_path / "static", tmp_path / "var",
                              tmp_path / "wiki", tmp_path / "data")


def test_production_settings_report_only_explicit_hsts_recommendations(tmp_path):
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("KI_CFG_", "KI_NEXT_")) and key not in {"KI_STAGE", "KI_PROFILE"}}
    env.update({
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__DEBUG": "false",
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__SECRET_KEY": "test-key-" + "x" * 70,
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__HTTPS_PROXY": "true",
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__PATHS__VAR": str(tmp_path),
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__PATHS__WORKSPACE": str(tmp_path),
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__PATHS__DATA": str(tmp_path),
    })
    result = subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy", "--fail-level", "ERROR"],
        cwd=PROJECT_ROOT, env=env, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "(security.W005)" in result.stderr
    assert "(security.W021)" in result.stderr


@pytest.mark.parametrize(("output", "accepted"), [
    ("?: (security.W005) subdomains\n?: (security.W021) preload\n", True),
    ("?: (security.W005) subdomains\n?: (security.W008) redirect\n", False),
    ("unexpected error", False),
])
def test_deploy_check_only_accepts_named_hsts_warnings(monkeypatch, output, accepted):
    monkeypatch.setattr(setup_u7.subprocess, "run",
                        lambda *args, **kwargs: subprocess.CompletedProcess(args, 1, "", output))
    if accepted:
        setup_u7.check_deploy(PROJECT_ROOT / ".venv/bin/python")
    else:
        with pytest.raises(setup_u7.SetupError, match="Deployprüfung"):
            setup_u7.check_deploy(PROJECT_ROOT / ".venv/bin/python")
