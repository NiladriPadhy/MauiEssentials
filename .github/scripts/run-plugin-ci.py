#!/usr/bin/env python3
"""Build, test, and optionally pack one MauiEssentials plugin folder."""

from __future__ import annotations

import argparse
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

LINUX_NET10_PROPS = """<Project>
  <PropertyGroup>
    <TargetFrameworks Condition="'$(TargetFrameworks)' != '' and $(TargetFrameworks.Contains('net10.0'))">net10.0</TargetFrameworks>
  </PropertyGroup>
</Project>
"""


_linux_msbuild_args: list[str] | None = None


def linux_msbuild_args() -> list[str]:
    """On Linux, drop ios/android TFMs so restore does not require those workloads."""
    global _linux_msbuild_args
    if _linux_msbuild_args is not None:
        return _linux_msbuild_args
    if platform.system() != "Linux":
        _linux_msbuild_args = []
        return _linux_msbuild_args
    path = Path(tempfile.gettempdir()) / "mauiessentials-linux-net10.props"
    path.write_text(LINUX_NET10_PROPS, encoding="utf-8")
    print(f"Linux: collapsing multi-TFM projects to net10.0 ({path})", flush=True)
    _linux_msbuild_args = [f"-p:CustomAfterMicrosoftCommonProps={path}"]
    return _linux_msbuild_args


def local_name(tag: str) -> str:
    return tag.split("}")[-1]


def parse_csproj_values(csproj: Path, names: set[str]) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {name: [] for name in names}
    try:
        tree = ET.parse(csproj)
    except ET.ParseError as exc:
        print(f"::warning::Could not parse {csproj}: {exc}")
        return values
    for element in tree.iter():
        name = local_name(element.tag)
        if name in names and element.text:
            values[name].append(element.text.strip())
    return values


def declared_tfms(csproj: Path) -> set[str]:
    raw = parse_csproj_values(csproj, {"TargetFramework", "TargetFrameworks"})
    tfms: set[str] = set()
    for blob in raw["TargetFramework"] + raw["TargetFrameworks"]:
        for part in blob.split(";"):
            item = part.strip()
            if item and not item.startswith("$("):
                tfms.add(item)
    return tfms


def is_packable(csproj: Path) -> bool:
    raw = parse_csproj_values(csproj, {"IsPackable", "IsTestProject"})
    if any(value.lower() == "true" for value in raw["IsTestProject"]):
        return False
    if any(value.lower() == "false" for value in raw["IsPackable"]):
        return False
    return True


def tfm_matches(requested: str, actual: str) -> bool:
    if actual == requested:
        return True
    if "-" not in requested:
        return False
    if not actual.startswith(requested):
        return False
    rest = actual[len(requested) :]
    return not rest or rest[0].isdigit()


def matching_tfms(requested: list[str], actual: set[str]) -> list[str]:
    matched: list[str] = []
    for item in requested:
        for tfm in sorted(actual):
            if tfm_matches(item, tfm) and tfm not in matched:
                matched.append(tfm)
    return matched


def find_csprojs(root: Path, folder: str) -> list[Path]:
    base = root / folder
    if not base.is_dir():
        return []
    projects = []
    for path in sorted(base.rglob("*.csproj")):
        parts = set(path.parts)
        if "bin" in parts or "obj" in parts:
            continue
        projects.append(path)
    return projects


def run(command: list[str], cwd: Path) -> None:
    print(f"::group::{' '.join(command)}")
    print(f"cwd={cwd}")
    completed = subprocess.run(command, cwd=cwd)
    print("::endgroup::")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def extra_msbuild() -> list[str]:
    return linux_msbuild_args()


def build_project(csproj: Path, tfm: str | None, configuration: str) -> None:
    command = ["dotnet", "build", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal"]
    command.extend(extra_msbuild())
    if tfm:
        command.extend(["-f", tfm])
    run(command, csproj.parent)


def test_project(csproj: Path, tfm: str | None, configuration: str) -> None:
    command = ["dotnet", "test", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal"]
    command.extend(extra_msbuild())
    if tfm:
        command.extend(["-f", tfm])
    run(command, csproj.parent)


def pack_project(csproj: Path, tfms: list[str] | None, configuration: str) -> None:
    command = ["dotnet", "pack", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal", "--no-build"]
    command.extend(extra_msbuild())
    if not tfms:
        run(command, csproj.parent)
        return
    # Semicolon-separated TargetFrameworks is parsed as two properties (MSB1006).
    for tfm in tfms:
        run(command + [f"-p:TargetFramework={tfm}"], csproj.parent)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", required=True)
    parser.add_argument("--frameworks", default="net10.0")
    parser.add_argument("--configuration", default="Release")
    parser.add_argument("--pack", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--test", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--build-unmatched", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    plugin_root = Path(args.plugin_root).resolve()
    if not plugin_root.is_dir():
        print(f"::error::Plugin folder not found: {plugin_root}")
        return 1

    requested = [item.strip() for item in args.frameworks.split(",") if item.strip()]
    src_projects = find_csprojs(plugin_root, "src")
    test_projects = find_csprojs(plugin_root, "tests")
    if not src_projects:
        print(f"::error::No src/*.csproj under {plugin_root}")
        return 1

    print(f"Plugin: {plugin_root.name}", flush=True)
    print(f"Frameworks: {', '.join(requested)}", flush=True)
    print(f"Source projects: {len(src_projects)}", flush=True)
    print(f"Test projects: {len(test_projects)}", flush=True)

    built_any = False
    for csproj in src_projects:
        actual = declared_tfms(csproj)
        matches = matching_tfms(requested, actual)
        if matches:
            for tfm in matches:
                build_project(csproj, tfm, args.configuration)
                built_any = True
        elif args.build_unmatched or any(item == "net10.0" for item in requested):
            build_project(csproj, None, args.configuration)
            built_any = True
        else:
            print(f"::notice::Skipping {csproj.name}; TFMs {sorted(actual)} do not match {requested}")

    if not built_any:
        print(f"::error::No projects built for {plugin_root.name} ({', '.join(requested)})")
        return 1

    tested_any = False
    if args.test:
        if not test_projects:
            print(f"::error::No tests/*.csproj under {plugin_root}")
            return 1
        for csproj in test_projects:
            actual = declared_tfms(csproj)
            matches = matching_tfms(requested, actual)
            if matches:
                for tfm in matches:
                    test_project(csproj, tfm, args.configuration)
                    tested_any = True
            elif any(item == "net10.0" for item in requested):
                test_project(csproj, None, args.configuration)
                tested_any = True
            else:
                print(f"::notice::Skipping tests {csproj.name}; TFMs {sorted(actual)} do not match {requested}")
        if not tested_any:
            print(f"::error::No tests ran for {plugin_root.name} ({', '.join(requested)})")
            return 1

    packed_any = False
    if args.pack:
        for csproj in src_projects:
            if not is_packable(csproj):
                continue
            actual = declared_tfms(csproj)
            matches = matching_tfms(requested, actual)
            if matches:
                pack_project(csproj, matches, args.configuration)
                packed_any = True
            elif any(item == "net10.0" for item in requested):
                pack_project(csproj, None, args.configuration)
                packed_any = True
        if not packed_any:
            print(f"::error::No packages generated for {plugin_root.name}")
            return 1
        packages = sorted(plugin_root.rglob("*.nupkg"))
        packages = [path for path in packages if "bin" in path.parts or "artifacts" in path.parts]
        print("Generated packages:", flush=True)
        for path in packages:
            print(f"  {path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
