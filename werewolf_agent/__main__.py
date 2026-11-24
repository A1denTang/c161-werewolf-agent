"""Start the local model when needed and select the SDK's practice or tournament mode."""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import ProxyHandler, build_opener

from dotenv import load_dotenv

from .model import MODEL


ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / ".runtime"


@contextmanager
def local_server():
    port = int(os.getenv("WEREWOLF_PORT", "18261"))
    http = build_opener(ProxyHandler({}))

    def ready():
        try:
            with http.open(f"http://127.0.0.1:{port}/v1/models", timeout=1) as response:
                entries = json.load(response)["data"]
        except OSError:
            return False
        if not any(item.get("id") == MODEL for item in entries):
            raise RuntimeError(f"Port {port} belongs to another model. Set WEREWOLF_PORT to a free port.")
        return True

    if ready():
        yield
        return
    binary = Path(os.getenv("WEREWOLF_SERVER", RUNTIME / "llama-b12635" / "llama-server.exe"))
    weights = Path(os.getenv("WEREWOLF_MODEL_FILE", RUNTIME / "qwen2.5-3b-q4.gguf"))
    if not binary.is_file() or not weights.is_file():
        raise SystemExit("Local model or server missing. Run Setup.ps1 in the werewolf-agent folder.")
    RUNTIME.mkdir(exist_ok=True)
    logfile = RUNTIME / f"server-{os.getpid()}.log"
    args = [str(binary), "-m", str(weights), "--alias", MODEL, "--host", "127.0.0.1",
            "--port", str(port), "-ngl", "99", "-c", "24576", "--parallel", "4"]
    with logfile.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(args, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise SystemExit(f"Local model exited during startup. See {logfile}")
                if ready():
                    break
                time.sleep(0.35)
            else:
                raise SystemExit(f"Timed out waiting for the local model. See {logfile}")
            yield
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["demo", "check", "practice", "tournament"])
    parser.add_argument("--output", type=Path, help="Demo only: save the evidence as JSON")
    parser.add_argument("--layout", choices=["original", "swapped"], default="original",
                        help="Demo only: change the seat labels in every decision probe")
    parser.add_argument("--agent", default="werewolf_agent", help="SDK factory for a team or one game")
    args = parser.parse_args()
    load_dotenv(ROOT / ".env", override=False)
    if args.mode == "demo":
        from .rehearsal import run
        with local_server():
            return run(args.output, layout=args.layout)
    if args.output or args.layout != "original":
        parser.error("--output and --layout are demo options")
    if not os.getenv("ALTRUAGENT_OFFICIAL_AGENT_KEY", "").strip():
        raise SystemExit("Missing Official Agent Key. The offline demo works without a platform account.")
    from agent.__main__ import main as sdk_main
    flag = {"check": "--check-tournament", "practice": "--match", "tournament": "--tournament"}[args.mode]
    if args.mode == "check":
        return sdk_main([flag, "--agent", args.agent])
    with local_server():
        return sdk_main([flag, "--agent", args.agent])


if __name__ == "__main__":
    raise SystemExit(main())
