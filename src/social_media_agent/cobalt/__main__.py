"""CLI for the local Cobalt API — works on any OS with Python.

    python -m social_media_agent.cobalt ensure   # start if not already up (setup uses this)
    python -m social_media_agent.cobalt status
    python -m social_media_agent.cobalt start
    python -m social_media_agent.cobalt stop
"""
import argparse
import json
import sys

from social_media_agent.cobalt import server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m social_media_agent.cobalt")
    parser.add_argument("command", choices=("ensure", "start", "stop", "status"))
    args = parser.parse_args(argv)

    try:
        if args.command == "status":
            print(json.dumps(server.status(), indent=2))
            return 0
        if args.command == "stop":
            stopped = server.stop()
            print("stopped" if stopped else "nothing to stop")
            return 0
        if args.command == "ensure":
            already = server.ensure()
            print(f"cobalt ready at {server.api_url()}" + (" (already running)" if already else " (started)"))
            return 0
        if args.command == "start":
            pid = server.start()
            print(f"cobalt running at {server.api_url()}" + (f" (pid {pid})" if pid else " (already running)"))
            return 0
    except server.CobaltSetupError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
