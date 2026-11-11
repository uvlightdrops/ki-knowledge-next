"""Configuration boundaries shared by the host and local deployment."""

import os
import shutil
import subprocess
import sys

import pytest
import yaml
from django.test import Client
from django.db import OperationalError

from knext.config import APP, PROJECT_ROOT, ConfigurationError, load_config, resolve_path


@pytest.fixture
def config_root(tmp_path, monkeypatch):
    for name in os.environ:
        if name.startswith(("KI_CFG_", "KI_NEXT_")) or name in {"KI_STAGE", "KI_PROFILE"}:
            monkeypatch.delenv(name)
    defaults = tmp_path / "config" / "defaults"
    defaults.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / "config" / "defaults" / "stack.yaml", defaults / "stack.yaml")
    return tmp_path


def write_layer(root, path, value):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(yaml.safe_dump(value), encoding="utf-8")


def app_value(field, value):
    return {"apps": {APP: {"django": {field: value}}}}


def test_defaults_preserve_local_settings(config_root):
    config = load_config(config_root)
    assert config["apps"][APP]["django"]["debug"] is True
    assert config["apps"][APP]["paths"]["var"] == "var"
    assert config["stack"]["services"]["django"]["port"] == 8780
    assert set(config["stack"]["services"]) == {"django"}
    assert config["apps"][APP]["relation_catalog"] == {"preset": "documentation", "types": []}


def test_relation_catalog_config_validates_presets_and_custom_definitions(config_root):
    write_layer(config_root, "ki.yaml", {"apps": {APP: {"relation_catalog": {
        "preset": "basic", "types": [{"key": "explores", "label": "Erkundet", "description": "Erkundet das Ziel."}],
    }}}})
    assert load_config(config_root)["apps"][APP]["relation_catalog"]["preset"] == "basic"
    write_layer(config_root, "ki.yaml", {"apps": {APP: {"relation_catalog": {"preset": "unknown"}}}})
    with pytest.raises(ConfigurationError):
        load_config(config_root)


def test_layer_priority(config_root, monkeypatch):
    values = [
        ("config/defaults/hosts.yaml", "defaults"),
        ("ki.yaml", "main"),
        ("config/profiles/writing.yaml", "profile"),
        ("config/stages/dev.yaml", "stage"),
        ("config/runtime/runtime.yaml", "runtime"),
    ]
    for path, host in values:
        write_layer(config_root, path, app_value("allowed_hosts", [host]))
        if host == "profile":
            monkeypatch.setenv("KI_PROFILE", "writing")
        if host == "stage":
            monkeypatch.setenv("KI_STAGE", "dev")
        assert load_config(config_root)["apps"][APP]["django"]["allowed_hosts"] == [host]
    monkeypatch.setenv("KI_NEXT_ALLOWED_HOSTS", "old.local, second.local")
    with pytest.warns(FutureWarning):
        assert load_config(config_root)["apps"][APP]["django"]["allowed_hosts"] == ["old.local", "second.local"]


def test_canonical_environment_overrides_legacy_and_credentials_override_both(config_root, monkeypatch):
    monkeypatch.setenv("KI_NEXT_DEBUG", "0")
    monkeypatch.setenv("KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__DEBUG", "true")
    monkeypatch.setenv("KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__SECRET_KEY", "synthetic-env")
    write_layer(config_root, "creds.yaml", app_value("secret_key", "synthetic-file"))
    with pytest.warns(FutureWarning):
        config = load_config(config_root)["apps"][APP]["django"]
    assert config["debug"] is True
    assert config["secret_key"] == "synthetic-file"


def test_stage_marker_and_environment_select_only_one_layer(config_root, monkeypatch):
    write_layer(config_root, "config/stages/first.yaml", app_value("allowed_hosts", ["first"]))
    write_layer(config_root, "config/stages/second.yaml", app_value("allowed_hosts", ["second"]))
    (config_root / "config/stages/.active_stage").write_text("first")
    assert load_config(config_root)["apps"][APP]["django"]["allowed_hosts"] == ["first"]
    monkeypatch.setenv("KI_STAGE", "second")
    assert load_config(config_root)["apps"][APP]["django"]["allowed_hosts"] == ["second"]


@pytest.mark.parametrize("stage", ["missing", "../outside", "/tmp/outside", "x/y"])
def test_missing_or_invalid_selected_stage_fails(config_root, monkeypatch, stage):
    monkeypatch.setenv("KI_STAGE", stage)
    with pytest.raises(ConfigurationError, match="KI_STAGE"):
        load_config(config_root)


def test_project_isolation_from_cwd_and_home(config_root, tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    write_layer(other, "ki.yaml", app_value("debug", False))
    write_layer(other, ".config/ki/creds.yaml", app_value("secret_key", "do-not-read"))
    monkeypatch.chdir(other)
    monkeypatch.setenv("HOME", str(other))
    config = load_config(config_root)["apps"][APP]["django"]
    assert config["debug"] is True
    assert config["secret_key"] == ""


@pytest.mark.parametrize("payload", [
    {"apps": {APP: {"django": {"debgu": True}}}},
    app_value("debug", "yes"),
    app_value("allowed_hosts", []),
    {"stack": {"services": {"django": {"port": 0}}}},
    {"stack": {"services": {"django": {"port": 65536}}}},
    {"stack": {"target": "k8s"}},
    {"stack": {"services": {"ollama": {}}}},
    {"apps": {APP: {"django": {"__replace__": True, "debug": True}}}},
])
def test_invalid_config_fails_explicitly(config_root, payload):
    write_layer(config_root, "ki.yaml", payload)
    with pytest.raises(ConfigurationError, match="Schema-Regel"):
        load_config(config_root)


def test_debug_false_requires_explicit_secret(config_root):
    write_layer(config_root, "ki.yaml", app_value("debug", False))
    with pytest.raises(ConfigurationError, match="secret_key"):
        load_config(config_root)
    write_layer(config_root, "creds.yaml", app_value("secret_key", "synthetic-private-key"))
    assert load_config(config_root)["apps"][APP]["django"]["debug"] is False


@pytest.mark.parametrize("contents", [
    "apps: [synthetic-secret",
    "- synthetic-secret",
    "false",
    "0",
])
def test_yaml_errors_do_not_disclose_values(config_root, contents):
    (config_root / "ki.yaml").write_text(contents)
    with pytest.raises(ConfigurationError) as error:
        load_config(config_root)
    assert "synthetic-secret" not in str(error.value)


def test_validation_errors_do_not_disclose_secret_values(config_root):
    write_layer(config_root, "creds.yaml", app_value("secret_key", ["synthetic-secret"]))
    with pytest.raises(ConfigurationError) as error:
        load_config(config_root)
    assert "secret_key" in str(error.value)
    assert "synthetic-secret" not in str(error.value)


def test_legacy_paths_preserve_var_relative_defaults(config_root, monkeypatch):
    monkeypatch.setenv("KI_NEXT_VAR", str(config_root / "private"))
    with pytest.warns(FutureWarning):
        config = load_config(config_root)
    assert config["apps"][APP]["paths"]["var"] == str(config_root / "private")
    assert resolve_path("doc", config_root) == config_root / "doc"


def test_invalid_legacy_boolean_is_not_silently_disabled(config_root, monkeypatch):
    monkeypatch.setenv("KI_NEXT_DEBUG", "yes")
    with pytest.raises(ConfigurationError, match="KI_NEXT_DEBUG"):
        load_config(config_root)


def test_environment_and_credentials_are_validated_after_all_layers(config_root, monkeypatch):
    monkeypatch.setenv("KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__DEBUG", "invalid")
    write_layer(config_root, "creds.yaml", app_value("debug", True))
    assert load_config(config_root)["apps"][APP]["django"]["debug"] is True


def test_cli_validation_does_not_print_values(config_root, monkeypatch, capsys):
    from knext import config

    write_layer(config_root, "creds.yaml", app_value("secret_key", "synthetic-private"))
    monkeypatch.setattr(config, "PROJECT_ROOT", config_root)
    assert config.main() == 0
    assert "synthetic-private" not in capsys.readouterr().out
    write_layer(config_root, "ki.yaml", app_value("debug", "invalid"))
    assert config.main() == 1
    assert "synthetic-private" not in capsys.readouterr().out


def test_local_stack_uses_same_loader_without_automatic_migration(config_root):
    from stackctl.spec import build_stack

    write_layer(config_root, "config/runtime/runtime.yaml", {"stack": {"services": {"django": {"port": 18780}}}})
    stack = build_stack(load_config(config_root)["stack"], PROJECT_ROOT)
    django = stack.service("django")
    assert django.port == 18780
    assert django.url == "http://127.0.0.1:18780/health/ready/"
    assert django.command[1:] == [
        "-m", "knext.devserver", "--noreload", "127.0.0.1:18780",
    ]
    assert django.prepare == []
    assert django.health_timeout == 30
    assert django.health_retries == 60


def test_stackctl_manifest_loads_real_project_config(config_root, monkeypatch):
    from stackctl.spec import find_project, load_raw_spec

    monkeypatch.setenv("KI_CFG_STACK__SERVICES__DJANGO__PORT", "18782")
    spec = load_raw_spec(find_project(PROJECT_ROOT))
    assert spec["services"]["django"]["port"] == 18782
    assert set(spec["services"]) == {"django"}


@pytest.mark.parametrize("debug", ["true", "false"])
def test_settings_use_explicit_secret_without_creating_local_key(config_root, debug):
    env = {
        **os.environ,
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__PATHS__VAR": str(config_root / "private"),
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__SECRET_KEY": "synthetic-explicit",
        "KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__DEBUG": debug,
    }
    result = subprocess.run(
        [sys.executable, "-c",
         "from knext import settings; "
         "assert settings.SECRET_KEY == 'synthetic-explicit'; "
         "assert str(settings.DATABASES['default']['NAME']).endswith('private/db.sqlite3')"],
        cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert not (config_root / "private" / "secret_key").exists()


@pytest.mark.django_db
def test_readiness_checks_database_without_login():
    response = Client().get("/health/ready/")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.django_db
def test_readiness_rejects_pending_migrations(monkeypatch):
    monkeypatch.setattr("knext.health.MigrationExecutor.migration_plan", lambda *args: [object()])
    response = Client().get("/health/ready/")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}


def test_readiness_reports_database_failure_without_details(monkeypatch):
    def failed(*args):
        raise OperationalError("synthetic-secret")

    monkeypatch.setattr("knext.health.MigrationExecutor", failed)
    response = Client().get("/health/ready/")
    assert response.status_code == 503
    assert b"synthetic-secret" not in response.content


def test_readiness_is_read_only():
    assert Client().post("/health/ready/").status_code == 405
