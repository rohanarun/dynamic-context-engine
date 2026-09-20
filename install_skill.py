#!/usr/bin/env python3
"""Install an offline, self-contained agent skill without changing agent settings."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
DESTINATIONS = {"codex": ".agents/skills", "claude": ".claude/skills", "hermes": ".hermes/skills"}

def install(destination, force=False):
    target = destination / "dynamic-context"
    if target.exists() and not force:
        raise SystemExit(f"{target} already exists. Use --force to replace this skill only.")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / "skills/dynamic-context", target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "jev_context", target / "scripts/jev_context", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return target

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", choices=DESTINATIONS)
    parser.add_argument("--path", type=Path, help="Custom skills directory (useful for project-local installs)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not args.path and not args.agent:
        parser.error("Choose --agent or --path")
    target = install(args.path or Path.home() / DESTINATIONS[args.agent], args.force)
    print(f"Installed: {target}\nSet TYPESAFE_API_KEY in your agent environment, then invoke dynamic-context.")
