import json
import os
import subprocess
import sys

import pytest
import yaml

from knext.config import APP, PROJECT_ROOT, load_config
from scripts import setup_u7


def environment_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    environment = tmp_path / ".venv"
    (environment / "bin").mkdir(parents=True)
    (environment / "pyvenv.cfg").write_text("home = /usr/bin\n")
    (environment / "bin/python").touch()
    return environment


@pytest.mark.parametrize("reuse", [False, True])
def test_install_creates_or_reuses_environment(tmp_path, monkeypatch, reuse):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    if reuse:
        environment_fixture(tmp_path, monkeypatch)
    commands = []
    confirmations = []
    monkeypatch.setattr(setup_u7, "SIBLINGS", {})
    monkeypatch.setattr(setup_u7, "confirm", confirmations.append)

    def run(*command, capture=False):
        commands.append(command)
        if capture:
            return json.dumps({"version": [3, 12], "prefix": str(tmp_path / ".venv"),
                               "base_prefix": "/usr"})
        return ""

    monkeypatch.setattr(setup_u7, "run", run)
    assert setup_u7.install_packages() == tmp_path / ".venv/bin/python"
    assert any(command[1:3] == ("-m", "venv") for command in commands) is not reuse
    assert bool(confirmations) is reuse
    assert any(command[1:4] == ("-m", "pip", "install") for command in commands)
    assert any(command[1:4] == ("-m", "pip", "check") for command in commands)


@pytest.mark.parametrize("details", [
    {"version": [3, 11], "prefix": "local", "base_prefix": "/usr"},
    {"version": [3, 12], "prefix": "/usr", "base_prefix": "/usr"},
    {"version": [3, 12], "prefix": "/elsewhere", "base_prefix": "/usr"},
    {},
])
def test_incompatible_environment_is_not_modified(tmp_path, monkeypatch, details):
    environment = environment_fixture(tmp_path, monkeypatch)
    if details.get("prefix") == "local":
        details["prefix"] = str(environment)
    monkeypatch.setattr(setup_u7, "run", lambda *args, **kwargs: json.dumps(details))
    with pytest.raises(setup_u7.SetupError):
        setup_u7.existing_environment()
    assert (environment / "pyvenv.cfg").read_text() == "home = /usr/bin\n"


def test_reuse_requires_confirmation_before_installation(tmp_path, monkeypatch):
    environment = environment_fixture(tmp_path, monkeypatch)
    commands = []

    def run(*command, capture=False):
        commands.append(command)
        return json.dumps({"version": [3, 12], "prefix": str(environment), "base_prefix": "/usr"})

    def decline(message):
        raise setup_u7.SetupError("Abgebrochen")

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "confirm", decline)
    with pytest.raises(setup_u7.SetupError, match="Abgebrochen"):
        setup_u7.install_packages()
    assert len(commands) == 1
    assert commands[0][1] == "-I"


@pytest.mark.parametrize("kind", ["file", "incomplete", "symlink"])
def test_invalid_environment_paths_are_rejected(tmp_path, monkeypatch, kind):
    monkeypatch.setattr(setup_u7, "ROOT", tmp_path)
    environment = tmp_path / ".venv"
    if kind == "file":
        environment.touch()
    elif kind == "symlink":
        environment.symlink_to(tmp_path / "missing", target_is_directory=True)
    else:
        environment.mkdir()
    with pytest.raises(setup_u7.SetupError, match="Keine gültige"):
        setup_u7.existing_environment()


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


@pytest.mark.parametrize("root", ["example.org", "example.org/"])
def test_matching_domain_backends_are_skipped(root):
    listing = f"{root} http:8780 => NOT OK, no service\nexample.org/static apache\n/ apache (default)"
    assert setup_u7.missing_backend_routes("example.org", 8780, listing) == {}


@pytest.mark.parametrize("entry", [
    "example.org/ http:8000",
    "example.org/ apache",
    "example.org/static http:8780",
    "example.org/ http:8780, --remove-prefix",
])
def test_mismatching_backends_are_not_overwritten(entry):
    with pytest.raises(setup_u7.SetupError, match="Keine Überschreibung"):
        setup_u7.missing_backend_routes("example.org", 8780, entry)


@pytest.mark.parametrize("existing", ["", "example.org/ http:8780", "example.org/static apache"])
def test_activation_only_creates_missing_routes(monkeypatch, existing):
    commands = []
    confirmations = []

    def run(*command, capture=False):
        commands.append(command)
        return existing if capture else ""

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "confirm", confirmations.append)
    monkeypatch.setattr(setup_u7, "request", lambda *args, **kwargs: (200, {}, b'{"status":"ready"}'))
    setup_u7.activate(PROJECT_ROOT / ".venv/bin/python", "example.org", 8780)
    created = [command[4] for command in commands if command[:4] == ("uberspace", "web", "backend", "set")]
    assert ("example.org" in created) is ("http:8780" not in existing)
    assert ("example.org/static" in created) is ("static" not in existing)
    assert len(confirmations) == 1


def test_activation_with_all_routes_skips_routing_confirmation_but_checks_readiness(monkeypatch):
    commands = []
    requests = []

    def run(*command, capture=False):
        commands.append(command)
        return "example.org/ http:8780\nexample.org/static apache"

    def unexpected_confirmation(message):
        pytest.fail("No routing changes should need confirmation")

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "confirm", unexpected_confirmation)
    monkeypatch.setattr(setup_u7, "request", lambda *args, **kwargs:
                        requests.append(args) or (200, {}, b'{"status":"ready"}'))
    setup_u7.activate(PROJECT_ROOT / ".venv/bin/python", "example.org", 8780)
    assert not any(command[:4] == ("uberspace", "web", "backend", "set") for command in commands)
    assert requests == [("example.org", "/health/ready/")]


def test_activation_rejects_changed_route_after_confirmation(monkeypatch):
    listings = iter(["", "example.org/ http:9999"])
    commands = []

    def run(*command, capture=False):
        commands.append(command)
        return next(listings) if capture else ""

    monkeypatch.setattr(setup_u7, "run", run)
    monkeypatch.setattr(setup_u7, "confirm", lambda message: None)
    with pytest.raises(setup_u7.SetupError, match="Keine Überschreibung"):
        setup_u7.activate(PROJECT_ROOT / ".venv/bin/python", "example.org", 8780)
    assert not any(command[:4] == ("uberspace", "web", "backend", "set") for command in commands)


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
