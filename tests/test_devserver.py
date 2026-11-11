"""Local child lifecycle without real servers or import data."""

import signal
import subprocess
from unittest.mock import Mock, patch

import pytest

from knext import devserver


@pytest.mark.parametrize("exits,index", [([1, None], 0), ([None, 0], 1)])
def test_child_exit_stops_both_process_groups(exits, index, capsys):
    children = [Mock(pid=4101, poll=Mock(return_value=exits[0])), Mock(pid=4102, poll=Mock(return_value=exits[1]))]
    with patch.object(devserver.subprocess, "Popen", side_effect=children) as spawn, patch.object(devserver.os, "killpg") as kill:
        assert devserver.run("127.0.0.1:18780", noreload=True) == 1
    assert spawn.call_args_list[0].args[0][-1] == "content_worker"
    assert spawn.call_args_list[1].args[0][-3:] == ["runserver", "--noreload", "127.0.0.1:18780"]
    assert all(call.kwargs["start_new_session"] for call in spawn.call_args_list)
    assert [call.args for call in kill.call_args_list] == [(4102, signal.SIGTERM), (4101, signal.SIGTERM)]
    assert ("Importworker" if index == 0 else "Django") in capsys.readouterr().err


def test_supervisor_signal_stops_children_and_restores_handlers():
    children = [Mock(pid=4101, poll=Mock(return_value=None)), Mock(pid=4102, poll=Mock(return_value=None))]
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    def stop(_):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
    with patch.object(devserver.subprocess, "Popen", side_effect=children), patch.object(devserver.os, "killpg"), patch.object(devserver.time, "sleep", side_effect=stop):
        assert devserver.run("127.0.0.1:18780") == 0
    assert {sig: signal.getsignal(sig) for sig in handlers} == handlers
    for child in children:
        child.wait.assert_called_once_with(timeout=30)


def test_spawn_failure_still_stops_started_worker():
    worker = Mock(pid=4101)
    with patch.object(devserver.subprocess, "Popen", side_effect=[worker, OSError("spawn failed")]), patch.object(devserver.os, "killpg") as kill:
        with pytest.raises(OSError, match="spawn failed"):
            devserver.run("127.0.0.1:18780")
    kill.assert_called_once_with(worker.pid, signal.SIGTERM)


def test_unresponsive_child_is_force_stopped_with_visible_warning(capsys):
    child = Mock(pid=4101, wait=Mock(side_effect=[subprocess.TimeoutExpired("worker", 30), 0]))
    with patch.object(devserver.os, "killpg") as kill:
        devserver._stop(child)
    assert [call.args[1] for call in kill.call_args_list] == [signal.SIGTERM, signal.SIGKILL]
    assert "Unterbrochene Jobs prüfen" in capsys.readouterr().err
