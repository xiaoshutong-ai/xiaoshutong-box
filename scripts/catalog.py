#!/usr/bin/env python3
"""Build and validate the Baibaoxiang unified catalog from per-app manifests."""

from __future__ import annotations

import argparse
import base64
import json
import os
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = ROOT / "apps"
CATALOG_PATH = ROOT / "versions.json"
REPO = "xiaoshutong-ai/xiaoshutong-box"
CDN_URL = f"https://cdn.jsdelivr.net/gh/{REPO}@main/versions.json"
PURGE_URL = f"https://purge.jsdelivr.net/gh/{REPO}@main/versions.json"
DATA_URI_PREFIX = "data:image/png;base64,"
REQUIRED = (
    "package", "name", "desc", "versionCode", "versionName", "apkUrl",
    "sha256", "sizeBytes", "publishedAt", "releaseTag", "changelog",
    "minVersionCode", "iconFile", "catalogOrder", "catalogUpdatedAt",
)


class CatalogError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise CatalogError(message)


def parse_time(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CatalogError(f"{field}: invalid ISO-8601 value {value!r}") from exc
    if parsed.tzinfo is None:
        fail(f"{field}: timezone is required")
    return parsed


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot read JSON {path.relative_to(ROOT)}: {exc}") from exc


def png_size(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        fail("icon must be a PNG with an IHDR header")
    return struct.unpack(">II", data[16:24])


def load_manifests() -> list[tuple[Path, dict, bytes]]:
    manifests: list[tuple[Path, dict, bytes]] = []
    seen_packages: set[str] = set()
    seen_orders: set[int] = set()
    for path in sorted(APPS_DIR.glob("*-version.json")):
        data = read_json(path)
        missing = [key for key in REQUIRED if key not in data]
        if missing:
            fail(f"{path.relative_to(ROOT)}: missing required fields {missing}")
        package = str(data["package"])
        order = data["catalogOrder"]
        if package in seen_packages:
            fail(f"duplicate package {package}")
        if not isinstance(order, int) or order < 0 or order in seen_orders:
            fail(f"{path.relative_to(ROOT)}: invalid/duplicate catalogOrder {order!r}")
        seen_packages.add(package)
        seen_orders.add(order)

        version_code = data["versionCode"]
        min_version_code = data["minVersionCode"]
        size_bytes = data["sizeBytes"]
        if not isinstance(version_code, int) or version_code <= 0:
            fail(f"{path.relative_to(ROOT)}: versionCode must be a positive integer")
        if not isinstance(min_version_code, int) or min_version_code < 0 or min_version_code > version_code:
            fail(f"{path.relative_to(ROOT)}: minVersionCode must be 0..versionCode")
        if not isinstance(size_bytes, int) or size_bytes <= 0:
            fail(f"{path.relative_to(ROOT)}: sizeBytes must be a positive integer")
        sha = str(data["sha256"]).lower()
        if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            fail(f"{path.relative_to(ROOT)}: sha256 must be 64 lowercase hex characters")
        if not str(data["apkUrl"]).startswith("https://github.com/xiaoshutong-ai/xiaoshutong-box/releases/download/"):
            fail(f"{path.relative_to(ROOT)}: apkUrl must use the canonical xiaoshutong-box GitHub Release channel")
        install_page = data.get("preferredInstallPageUrl")
        if install_page:
            parsed_install_page = urlparse(str(install_page))
            if parsed_install_page.scheme != "https" or parsed_install_page.hostname not in {"pgyer.com", "www.pgyer.com"}:
                fail(f"{path.relative_to(ROOT)}: preferredInstallPageUrl must use https://www.pgyer.com/")
        parse_time(str(data["publishedAt"]), f"{path.name}.publishedAt")
        parse_time(str(data["catalogUpdatedAt"]), f"{path.name}.catalogUpdatedAt")

        icon_path = (path.parent / str(data["iconFile"])).resolve()
        try:
            icon_path.relative_to(APPS_DIR.resolve())
        except ValueError:
            fail(f"{path.relative_to(ROOT)}: iconFile escapes apps/")
        try:
            icon_bytes = icon_path.read_bytes()
        except OSError as exc:
            raise CatalogError(f"{path.relative_to(ROOT)}: cannot read icon {icon_path}: {exc}") from exc
        width, height = png_size(icon_bytes)
        if (width, height) != (192, 192):
            fail(f"{path.relative_to(ROOT)}: icon must be 192x192 PNG, got {width}x{height}")

        manifests.append((path, data, icon_bytes))
    if not manifests:
        fail("no apps/*-version.json manifests found")
    return sorted(manifests, key=lambda item: item[1]["catalogOrder"])


def build_catalog() -> dict:
    manifests = load_manifests()
    latest = max(manifests, key=lambda item: parse_time(str(item[1]["catalogUpdatedAt"]), item[0].name))
    apps: list[dict] = []
    for _path, data, icon_bytes in manifests:
        item = {
            "package": data["package"],
            "name": data["name"],
            "desc": data["desc"],
            "versionCode": data["versionCode"],
            "versionName": data["versionName"],
            "apkUrl": data["apkUrl"],
            "size": data["sizeBytes"],
            "sizeBytes": data["sizeBytes"],
            "sha256": data["sha256"],
            "icon": DATA_URI_PREFIX + base64.b64encode(icon_bytes).decode("ascii"),
            "changelog": data["changelog"],
            "minVersionCode": data["minVersionCode"],
        }
        preferred = data.get("preferredApkUrl")
        if preferred:
            item["preferredApkUrl"] = preferred
        install_page = data.get("preferredInstallPageUrl")
        if install_page:
            item["preferredInstallPageUrl"] = install_page
        apps.append(item)
    return {"updatedAt": latest[1]["catalogUpdatedAt"], "apps": apps}


def render_catalog() -> str:
    return json.dumps(build_catalog(), ensure_ascii=False, indent=2) + "\n"


def normalize_eol(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def cmd_generate(_args: argparse.Namespace) -> None:
    rendered = render_catalog().encode("utf-8")
    current = CATALOG_PATH.read_bytes() if CATALOG_PATH.exists() else b""
    if b"\r\n" in current:
        rendered = rendered.replace(b"\n", b"\r\n")
    CATALOG_PATH.write_bytes(rendered)
    print(f"CATALOG_GENERATE=PASS apps={len(build_catalog()['apps'])}")


def cmd_check(_args: argparse.Namespace) -> None:
    expected = render_catalog().encode("utf-8")
    actual = CATALOG_PATH.read_bytes()
    if normalize_eol(actual) != expected:
        fail("versions.json is not the exact generated content; run scripts/catalog.py generate")
    print(f"CATALOG_GENERATED_MATCH=PASS apps={len(build_catalog()['apps'])}")


def resolve_github_token() -> str | None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    token = result.stdout.strip()
    return token or None


def github_json(url: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "xiaoshutong-box-catalog-gate",
    }
    token = resolve_github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise CatalogError(f"GitHub API request failed: {url}: {exc}") from exc


def cmd_verify_releases(_args: argparse.Namespace) -> None:
    releases = github_json(f"https://api.github.com/repos/{REPO}/releases?per_page=100")
    if not isinstance(releases, list):
        fail("GitHub releases endpoint returned an unexpected payload")
    by_tag = {release.get("tag_name"): release for release in releases}
    count = 0
    for path, data, _icon in load_manifests():
        tag = data["releaseTag"]
        release = by_tag.get(tag)
        if release is None:
            fail(f"{path.name}: release {tag} was not found in the latest 100 releases")
        if release.get("draft") or release.get("prerelease"):
            fail(f"{path.name}: release {tag} is draft/prerelease")
        if release.get("published_at") != data["publishedAt"]:
            fail(f"{path.name}: publishedAt mismatch: manifest={data['publishedAt']} release={release.get('published_at')}")
        asset_name = Path(urlparse(data["apkUrl"]).path).name
        assets = [asset for asset in release.get("assets", []) if asset.get("name") == asset_name]
        if len(assets) != 1:
            fail(f"{path.name}: expected exactly one release asset named {asset_name}")
        asset = assets[0]
        if asset.get("state") != "uploaded":
            fail(f"{path.name}: release asset {asset_name} is not uploaded")
        if asset.get("browser_download_url") != data["apkUrl"]:
            fail(f"{path.name}: apkUrl does not match GitHub release asset URL")
        if asset.get("size") != data["sizeBytes"]:
            fail(f"{path.name}: size mismatch: manifest={data['sizeBytes']} release={asset.get('size')}")
        digest = asset.get("digest")
        expected_digest = f"sha256:{data['sha256']}"
        if digest != expected_digest:
            fail(f"{path.name}: digest mismatch: manifest={expected_digest} release={digest}")
        count += 1
        print(f"RELEASE_ASSET=PASS package={data['package']} tag={tag} bytes={data['sizeBytes']}")
    print(f"CATALOG_RELEASES=PASS apps={count}")


def url_json(url: str, timeout: int = 20) -> tuple[dict, dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "xiaoshutong-box-catalog-gate", "Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return json.load(resp), headers
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise CatalogError(f"request failed: {url}: {exc}") from exc


def cmd_purge_verify(args: argparse.Namespace) -> None:
    purge, _headers = url_json(PURGE_URL)
    if purge.get("status") != "finished":
        fail(f"jsDelivr purge did not finish: {purge}")
    expected = build_catalog()
    last = None
    for attempt in range(1, args.attempts + 1):
        try:
            remote, headers = url_json(CDN_URL)
            last = (remote, headers)
            if remote == expected:
                print(
                    "CDN_CATALOG=PASS "
                    f"attempt={attempt} apps={len(remote['apps'])} "
                    f"age={headers.get('age', 'n/a')} "
                    f"x-cache={headers.get('x-cache', 'n/a')} "
                    f"cf-cache-status={headers.get('cf-cache-status', 'n/a')}"
                )
                return
        except CatalogError as exc:
            print(f"CDN_CATALOG_RETRY attempt={attempt} error={exc}", file=sys.stderr)
        time.sleep(args.delay)
    if last:
        remote, _headers = last
        fail(
            "CDN catalog did not converge to current generated catalog; "
            f"remoteUpdatedAt={remote.get('updatedAt')} expectedUpdatedAt={expected.get('updatedAt')}"
        )
    fail("CDN catalog could not be read after purge")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("generate")
    sub.add_parser("check")
    sub.add_parser("verify-releases")
    purge = sub.add_parser("purge-verify")
    purge.add_argument("--attempts", type=int, default=6)
    purge.add_argument("--delay", type=float, default=2.0)
    args = parser.parse_args()
    commands = {
        "generate": cmd_generate,
        "check": cmd_check,
        "verify-releases": cmd_verify_releases,
        "purge-verify": cmd_purge_verify,
    }
    try:
        commands[args.command](args)
    except CatalogError as exc:
        print(f"CATALOG_GATE=FAIL {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
