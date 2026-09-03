#!/usr/bin/env python3
"""Build, test, and optionally pack one MauiEssentials plugin folder."""

from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


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


def project_references(csproj: Path) -> list[Path]:
    refs: list[Path] = []
    try:
        tree = ET.parse(csproj)
    except ET.ParseError:
        return refs
    for element in tree.iter():
        if local_name(element.tag) != "ProjectReference":
            continue
        include = element.attrib.get("Include") or element.attrib.get("include")
        if include:
            refs.append((csproj.parent / include).resolve())
    return refs


def collapse_linux_graph(projects: list[Path]) -> None:
    seen: set[Path] = set()
    queue = list(projects)
    while queue:
        csproj = queue.pop()
        if csproj in seen or not csproj.is_file():
            continue
        seen.add(csproj)
        collapse_linux_tfms(csproj)
        queue.extend(project_references(csproj))


def collapse_linux_tfms(csproj: Path) -> None:
    """Rewrite TargetFrameworks to net10.0 on Linux so restore does not pull iOS packs.

    MSBuild evaluates every TFM in the csproj before -f applies (NETSDK1178).
    Editing the file on the runner is the reliable isolation.
    """
    if platform.system() != "Linux":
        return
    text = csproj.read_text(encoding="utf-8")
    if "<TargetFrameworks" not in text or "net10.0" not in text:
        return
    collapsed, count = re.subn(
        r"\s*<TargetFrameworks\b[^>]*>.*?</TargetFrameworks>",
        "",
        text,
        flags=re.DOTALL,
    )
    if count == 0:
        return
    collapsed = re.sub(
        r"(<PropertyGroup>)",
        r"\1\n    <TargetFrameworks>net10.0</TargetFrameworks>",
        collapsed,
        count=1,
    )
    csproj.write_text(collapsed, encoding="utf-8")
    print(f"Linux: rewrote {csproj.name} TargetFrameworks to net10.0", flush=True)


def build_project(csproj: Path, tfm: str | None, configuration: str) -> None:
    command = ["dotnet", "build", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal"]
    if tfm:
        command.extend(["-f", tfm])
    run(command, csproj.parent)


def test_project(csproj: Path, tfm: str | None, configuration: str) -> None:
    command = ["dotnet", "test", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal"]
    if tfm:
        command.extend(["-f", tfm])
    run(command, csproj.parent)


def pack_project(csproj: Path, tfms: list[str] | None, configuration: str) -> None:
    command = ["dotnet", "pack", str(csproj), "-c", configuration, "--nologo", "--verbosity", "minimal", "--no-build"]
    if not tfms:
        run(command, csproj.parent)
        return
    # Isolate one TFM. `-p:TargetFramework=` still packs every TFM listed in the
    # csproj (NU5026 for unbuilt android/ios/net8). Do not join with ';' (MSB1006).
    for tfm in tfms:
        run(command + [f"-p:TargetFrameworks={tfm}"], csproj.parent)


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

    collapse_linux_graph(src_projects + test_projects)

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
