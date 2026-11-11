"""Startup argument handling without migrations or a live development server."""

import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from knext.config import PROJECT_ROOT


@pytest.fixture
def startup(tmp_path):
    shutil.copyfile(PROJECT_ROOT / "start", tmp_path / "start")
    defaults = tmp_path / "config/defaults"
    defaults.mkdir(parents=True)
    shutil.copyfile(PROJECT_ROOT / "config/defaults/stack.yaml", defaults / "stack.yaml")
    binary = tmp_path / ".venv/bin/python"
    binary.parent.mkdir(parents=True)
    binary.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        "from knext import config\n"
        "config.PROJECT_ROOT = Path.cwd()\n"
        "if sys.argv[1] == '-':\n"
        "    sys.argv = sys.argv[1:]\n"
        "    exec(compile(sys.stdin.read(), '<startup>', 'exec'))\n"
        "else:\n"
        "    with open('calls.jsonl', 'a') as stream:\n"
        "        stream.write(json.dumps({'args': sys.argv[1:], "
        "'hosts': os.environ.get('KI_NEXT_ALLOWED_HOSTS')}) + '\\n')\n",
    )
    binary.chmod(0o700)
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("KI_CFG_", "KI_NEXT_")) and key not in {"KI_STAGE", "KI_PROFILE"}
    }
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    return tmp_path, env


def run_start(startup, *args):
    root, env = startup
    return subprocess.run(
        ["sh", str(root / "start"), *args], cwd=root, env=env,
        capture_output=True, text=True, timeout=30,
    )


def calls(startup):
    path = startup[0] / "calls.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


@pytest.mark.parametrize("args,address", [
    ([], "127.0.0.1:8780"),
    (["127.0.0.1:8782"], "127.0.0.1:8782"),
])
def test_start_preserves_local_default_and_explicit_address(startup, args, address):
    result = run_start(startup, *args)
    assert result.returncode == 0, result.stderr
    assert [call["args"] for call in calls(startup)] == [
        ["manage.py", "migrate", "--noinput"], ["-m", "knext.devserver", address],
    ]
    assert all(call["hosts"] is None for call in calls(startup))


def test_lan_start_adds_exact_host_and_binds_all_interfaces(startup):
    result = run_start(startup, "--lan", "192.168.1.20")
    assert result.returncode == 0, result.stderr
    assert calls(startup)[-1]["args"] == ["-m", "knext.devserver", "0.0.0.0:8780"]
    assert calls(startup)[-1]["hosts"] == "localhost,127.0.0.1,192.168.1.20"
    assert "http://192.168.1.20:8780/" in result.stdout


@pytest.mark.parametrize("args", [
    ["--lan"], ["--lan", "bad"], ["--lan", "0.0.0.0"], ["--lan", "127.0.0.1"],
    ["--lan", "224.0.0.1"], ["--lan", "192.168.1.20", "extra"], ["--unknown"],
])
def test_invalid_start_arguments_fail_before_migrations(startup, args):
    result = run_start(startup, *args)
    assert result.returncode != 0
    assert result.stderr
    assert calls(startup) == []


@pytest.mark.parametrize("hosts", [["*"], ["localhost"]])
def test_lan_start_rejects_overriding_credentials_hosts(startup, hosts):
    root, _ = startup
    (root / "creds.yaml").write_text(yaml.safe_dump({
        "apps": {"ki_knowledge_next": {"django": {"allowed_hosts": hosts}}},
    }))
    result = run_start(startup, "--lan", "192.168.1.20")
    assert result.returncode != 0
    assert calls(startup) == []
