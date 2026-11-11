"""Supervise the local webserver and a separate importworker."""

import argparse
import os
import signal
import subprocess
import sys
import time

from knext.config import PROJECT_ROOT


def _stop(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        print("Dienst reagiert nicht auf Stop; wird beendet. Unterbrochene Jobs prüfen.", file=sys.stderr)
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run(address: str, *, noreload: bool = False) -> int:
    """Keep both children attached; stop their sibling on unexpected exit."""
    stopping = False

    def request_stop(signum, frame) -> None:
        nonlocal stopping
        stopping = True

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    processes = []
    try:
        for name, args in (
            ("Importworker", ["content_worker"]),
            ("Django", ["runserver", *(["--noreload"] if noreload else []), address]),
        ):
            process = subprocess.Popen(
                [sys.executable, "-u", str(PROJECT_ROOT / "manage.py"), *args],
                cwd=PROJECT_ROOT, start_new_session=True,
            )
            processes.append((name, process))
        while not stopping:
            for name, process in processes:
                code = process.poll()
                if code is not None:
                    print(f"{name} wurde unerwartet beendet (Exit {code}); lokaler Betrieb wird gestoppt.", file=sys.stderr)
                    return code if code > 0 else 1
            time.sleep(0.2)
        return 0
    finally:
        for _, process in reversed(processes):
            _stop(process)
        for sig, handler in previous.items():
            signal.signal(sig, handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("address", nargs="?", default="127.0.0.1:8780")
    parser.add_argument("--noreload", action="store_true")
    arguments = parser.parse_args()
    sys.exit(run(arguments.address, noreload=arguments.noreload))
