"""Offline preflight CLI. No APK downloading, installation or mutation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .apk import InspectionError, check_profile, inspect_set


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vesktop Android: offline APK research and preflight")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "check"):
        command = commands.add_parser(name, help="Inspect APK metadata" if name == "inspect" else "Check declared split requirements and an optional exact profile")
        command.add_argument("apks", type=Path, nargs="+")
        command.add_argument("--profile", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect_set(args.apks)
        if args.profile:
            if args.profile.stat().st_size > 65536:
                raise InspectionError("Compatibility profile exceeds size limit")
            profile = json.loads(args.profile.read_text(encoding="utf-8"))
            errors = check_profile(report, profile)
            report["profile"] = {"file_name": args.profile.name, "base_fingerprint_matches": not errors, "errors": errors}
        print(json.dumps(report, indent=2, sort_keys=True))
        if args.command == "check":
            return 2 if report["set"]["blockers"] or report.get("profile", {}).get("errors") else 0
        return 0
    except (InspectionError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "patch_supported": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
