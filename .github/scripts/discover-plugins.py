#!/usr/bin/env python3
"""Emit a JSON array of hub submodule plugin folders to build."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

# Shared libraries plus MVVMExpress. Used when submodule src is not checked out.
WINDOWS_TFM_PLUGINS = {
    "ApiCache",
    "ApiResilience",
    "FeatureFlags",
    "FormValidation",
    "JobQueue",
    "MediaPipeline",
    "MVVMExpress",
    "RetryQueue",
    "SecureStoragePlus",
    "SmartUpload",
}


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


def declared_tfms(csproj: Path) -> set[str]:
    tfms: set[str] = set()
    try:
        tree = ET.parse(csproj)
    except ET.ParseError:
        return tfms
    for element in tree.iter():
        name = element.tag.split("}")[-1]
        if name not in {"TargetFramework", "TargetFrameworks"} or not element.text:
            continue
        for part in element.text.split(";"):
            item = part.strip()
            if item and not item.startswith("$("):
                tfms.add(item)
    return tfms


def plugin_tfms(root: Path, plugin: str) -> set[str]:
    tfms: set[str] = set()
    src = root / plugin / "src"
    if not src.is_dir():
        return tfms
    for csproj in src.rglob("*.csproj"):
        parts = set(csproj.parts)
        if "bin" in parts or "obj" in parts:
            continue
        tfms.update(declared_tfms(csproj))
    return tfms


def tfm_matches(requested: str, actual: str) -> bool:
    if actual == requested:
        return True
    if "-" not in requested:
        return False
    if not actual.startswith(requested):
        return False
    rest = actual[len(requested) :]
    return not rest or rest[0].isdigit()


def has_tfm_prefix(root: Path, plugin: str, prefix: str) -> bool:
    tfms = plugin_tfms(root, plugin)
    if tfms:
        return any(tfm_matches(prefix, tfm) for tfm in tfms)
    # Hub checkout without submodules: fall back to the known shared set.
    if prefix.startswith("net10.0-windows"):
        return plugin in WINDOWS_TFM_PLUGINS
    return False


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
    parser.add_argument(
        "--require-tfm-prefix",
        default="",
        help="Keep only plugins whose src csproj declares a matching TFM (prefix match, e.g. net10.0-windows).",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    os.chdir(root)
    plugins = plugin_paths(root)
    only = args.only.strip() or None
    changed = changed_files(args.base_sha, args.head_sha) if args.mode == "changed" and not only else []
    selected = select(plugins, changed, only) if args.mode == "changed" or only else plugins
    prefix = args.require_tfm_prefix.strip()
    if prefix:
        selected = [plugin for plugin in selected if has_tfm_prefix(root, plugin, prefix)]
    print(json.dumps(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
