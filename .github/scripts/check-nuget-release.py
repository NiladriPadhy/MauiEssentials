#!/usr/bin/env python3
"""Fail if NUGET_KEY is unusable or the csproj version is already on NuGet.org."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET

NUGET_ORG = "https://www.nuget.org"
NUGET_FLAT = "https://api.nuget.org/v3-flatcontainer"
CREATE_KEY = NUGET_ORG + "/api/v2/package/create-verification-key/{id}"
CREATE_KEY_VERSION = NUGET_ORG + "/api/v2/package/create-verification-key/{id}/{version}"
PUBLISH = NUGET_ORG + "/api/v2/package"


def load_ci():
    path = Path(__file__).with_name("run-plugin-ci.py")
    spec = importlib.util.spec_from_file_location("run_plugin_ci", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"::error::Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ci = load_ci()


def local_name(tag: str) -> str:
    return tag.split("}")[-1]


def property_text(path: Path, names: set[str]) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as exc:
        print(f"::warning::Could not parse {path}: {exc}")
        return values
    for element in tree.iter():
        name = local_name(element.tag)
        if name not in names:
            continue
        if element.attrib.get("Include") or element.attrib.get("include"):
            continue
        if element.text and element.text.strip() and not element.text.strip().startswith("$("):
            values[name] = element.text.strip()
    return values


def directory_build_props(plugin_root: Path, csproj: Path) -> list[Path]:
    props: list[Path] = []
    current = csproj.parent.resolve()
    root = plugin_root.resolve()
    seen: set[Path] = set()
    while True:
        candidate = current / "Directory.Build.props"
        if candidate.is_file() and candidate not in seen:
            props.append(candidate)
            seen.add(candidate)
        if current == root or current.parent == current:
            break
        current = current.parent
    props.reverse()
    return props


def package_identity(plugin_root: Path, csproj: Path) -> tuple[str, str]:
    merged: dict[str, str] = {}
    for path in directory_build_props(plugin_root, csproj) + [csproj]:
        merged.update(property_text(path, {"PackageId", "AssemblyName", "Version", "PackageVersion"}))
    package_id = merged.get("PackageId") or merged.get("AssemblyName") or csproj.stem
    version = merged.get("PackageVersion") or merged.get("Version")
    if not version:
        raise SystemExit(f"::error::{csproj} has no Version or PackageVersion")
    return package_id, version


def normalize_version(version: str) -> str:
    core, sep, pre = version.strip().partition("-")
    core = core.split("+", 1)[0]
    parts = [part for part in core.split(".") if part != ""]
    while len(parts) > 3 and parts[-1] == "0":
        parts.pop()
    normalized = ".".join(parts).lower()
    if sep:
        normalized += "-" + pre.split("+", 1)[0].lower()
    return normalized


def http(method: str, url: str, api_key: str | None = None, data: bytes | None = None) -> tuple[int, str]:
    headers = {
        "User-Agent": "MauiEssentials-check-nuget-release",
        "X-NuGet-Protocol-Version": "4.1.0",
    }
    if api_key:
        headers["X-NuGet-ApiKey"] = api_key
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, context=context, timeout=30) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.getcode() or 200, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body
    except urllib.error.URLError as exc:
        fail(f"Could not reach nuget.org ({exc.reason})")


def fail(message: str) -> None:
    print(f"::error::{message}")
    raise SystemExit(1)


def validate_key(api_key: str, package_id: str, version: str) -> None:
    encoded_id = urllib.parse.quote(package_id)
    encoded_version = urllib.parse.quote(version)
    url = CREATE_KEY_VERSION.format(id=encoded_id, version=encoded_version)
    status, body = http("POST", url, api_key=api_key)
    snippet = " ".join(body.split())[:300]
    print(f"NUGET_KEY check for {package_id} {version}: HTTP {status}")
    if status in {200, 201}:
        print("NUGET_KEY is accepted by nuget.org")
        return
    if status in {401, 403}:
        detail = snippet or "nuget.org rejected the key"
        fail(f"NUGET_KEY is expired, invalid, or not allowed to publish {package_id}. {detail}")
    if status == 404:
        status, body = http("POST", CREATE_KEY.format(id=encoded_id), api_key=api_key)
        snippet = " ".join(body.split())[:300]
        print(f"NUGET_KEY check for {package_id}: HTTP {status}")
        if status in {200, 201}:
            print("NUGET_KEY is accepted by nuget.org")
            return
        if status in {401, 403}:
            detail = snippet or "nuget.org rejected the key"
            fail(f"NUGET_KEY is expired, invalid, or not allowed to publish {package_id}. {detail}")
        status, body = http("PUT", PUBLISH, api_key=api_key, data=b"")
        snippet = " ".join(body.split())[:300]
        print(f"NUGET_KEY publish probe: HTTP {status}")
        if status in {401, 403}:
            detail = snippet or "nuget.org rejected the key"
            fail(f"NUGET_KEY is expired or invalid. {detail}")
        if status in {400, 409, 415}:
            print("NUGET_KEY is accepted by nuget.org")
            return
        fail(f"Could not validate NUGET_KEY (HTTP {status}). {snippet}")
    fail(f"Could not validate NUGET_KEY (HTTP {status}). {snippet}")


def published_versions(package_id: str) -> set[str]:
    url = f"{NUGET_FLAT}/{package_id.lower()}/index.json"
    status, body = http("GET", url)
    if status == 404:
        return set()
    if status != 200:
        fail(f"Could not list NuGet.org versions for {package_id} (HTTP {status})")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        fail(f"NuGet.org returned invalid version list for {package_id}")
    versions = payload.get("versions") or []
    return {normalize_version(str(item)) for item in versions}


def version_on_nuget(package_id: str, version: str, api_key: str) -> bool:
    encoded_id = urllib.parse.quote(package_id)
    encoded_version = urllib.parse.quote(version)
    url = CREATE_KEY_VERSION.format(id=encoded_id, version=encoded_version)
    status, body = http("POST", url, api_key=api_key)
    snippet = " ".join(body.split())[:300]
    print(f"Deployed version check for {package_id} {version}: HTTP {status}")
    if status in {401, 403}:
        detail = snippet or "nuget.org rejected the key"
        fail(f"NUGET_KEY is expired, invalid, or not allowed to publish {package_id}. {detail}")
    listed = published_versions(package_id)
    present = normalize_version(version) in listed
    if present:
        print(f"{package_id} {version} is already on NuGet.org")
    else:
        print(f"{package_id} {version} is not on NuGet.org")
    return present


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-root", default=".")
    args = parser.parse_args()

    plugin_root = Path(args.plugin_root).resolve()
    if not plugin_root.is_dir():
        fail(f"Plugin folder not found: {plugin_root}")

    api_key = os.environ.get("NUGET_KEY", "").strip()
    if not api_key:
        fail("NUGET_KEY secret is empty. Add a valid nuget.org API key under Settings → Secrets and variables → Actions.")

    src_projects = [path for path in ci.find_csprojs(plugin_root, "src") if ci.is_packable(path)]
    if not src_projects:
        fail(f"No packable src/*.csproj under {plugin_root}")

    packages = [package_identity(plugin_root, csproj) for csproj in src_projects]
    print("Release packages from csproj:")
    for package_id, version in packages:
        print(f"  {package_id} {version}")

    validate_key(api_key, packages[0][0], packages[0][1])

    already = []
    for package_id, version in packages:
        if version_on_nuget(package_id, version, api_key):
            already.append(f"{package_id} {version}")
    if already:
        fail("csproj release version matches a version already deployed to NuGet.org: " + ", ".join(already))

    print("No csproj release version is already on NuGet.org")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
