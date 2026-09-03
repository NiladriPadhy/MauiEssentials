#!/usr/bin/env python3
"""Emit a JSON array of hub submodule plugin folders to build."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def plugin_paths(repo_root: Path) -> list[str]:
    modules = repo_root / ".gitmodules"
    if not modules.is_file():
        print("::error::.gitmodules not found", file=sys.stderr)
        sys.exit(1)
    output = git("config", "--file", str(modules), "--get-regexp", r"^submodule\..*\.path$")
    return sorted({line.split()[-1] for line in output.splitlines() if line.strip()})


def changed_files(base: str, head: str) -> list[str]:
    if not base or not head:
        return []
    return [line for line in git("diff", "--name-only", f"{base}...{head}").splitlines() if line]


def select(plugins: list[str], changed: list[str], only: str | None) -> list[str]:
    if only:
        if only not in plugins:
            print(f"::error::Unknown plugin '{only}'. Expected one of: {', '.join(plugins)}", file=sys.stderr)
            sys.exit(1)
        return [only]
    if not changed:
        return plugins
    for path in changed:
        if path == ".gitmodules" or path.startswith(".github/"):
            return plugins
    selected = []
    for plugin in plugins:
        prefix = plugin + "/"
        if any(path == plugin or path.startswith(prefix) for path in changed):
            selected.append(plugin)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--mode", choices=("all", "changed"), default="all")
    parser.add_argument("--only", default="")
    parser.add_argument("--base-sha", default="")
    parser.add_argument("--head-sha", default="")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    os.chdir(root)
    plugins = plugin_paths(root)
    only = args.only.strip() or None
    changed = changed_files(args.base_sha, args.head_sha) if args.mode == "changed" and not only else []
    selected = select(plugins, changed, only) if args.mode == "changed" or only else plugins
    print(json.dumps(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
