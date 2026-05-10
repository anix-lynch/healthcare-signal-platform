#!/usr/bin/env python3
"""
Upload a local CSV to Fabric Lakehouse Files (bronze/) via OneLake DFS API.

Requires: az CLI logged in as SP, or env AZURE_CLIENT_ID / AZURE_CLIENT_SECRET / AZURE_TENANT_ID.
Token scope: https://storage.azure.com/

Usage (from repo root):
  source ~/.config/secrets/global.env
  python3 scripts/upload_bronze_to_onelake.py [--dry-run]

Defaults: FABRIC_WORKSPACE_ID, lakehouse id for HealthcareAnalytics (override with FABRIC_LAKEHOUSE_ID).
"""
from __future__ import annotations

import argparse
import os
import ssl
import subprocess
import sys
import urllib.error
import urllib.request

import certifi

# HealthcareAnalytics workspace + Lakehouse (same display name as workspace item)
DEFAULT_WORKSPACE = "577de43f-21b4-479e-99b6-ea78f32e5216"
DEFAULT_LAKEHOUSE = "28903c65-fb33-4a32-96ec-73898f26b13f"
STORAGE_RESOURCE = "https://storage.azure.com/"
ONELAKE_HOST = "onelake.dfs.fabric.microsoft.com"
CHUNK = 4 * 1024 * 1024  # 4 MiB


def get_storage_token() -> str:
    r = subprocess.run(
        [
            "az",
            "account",
            "get-access-token",
            "--resource",
            STORAGE_RESOURCE,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return r.stdout.strip()


def onelake_url(workspace: str, lakehouse: str, rel_path: str, query: str) -> str:
    rel = rel_path.lstrip("/")
    return f"https://{ONELAKE_HOST}/{workspace}/{lakehouse}/{rel}?{query}"


def _ssl_ctx() -> ssl.SSLContext:
    return ssl.create_default_context(cafile=certifi.where())


def http_request(method: str, url: str, token: str, data: bytes | None = None, headers: dict | None = None) -> tuple[int, bytes]:
    h = {
        "Authorization": f"Bearer {token}",
        "x-ms-version": "2020-10-02",
    }
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, method=method, data=data, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=600, context=_ssl_ctx()) as resp:
            return resp.getcode(), resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--file",
        default=os.path.join(os.path.dirname(__file__), "..", "data", "raw", "healthcare_dataset.csv"),
        help="Local CSV path",
    )
    ap.add_argument(
        "--remote",
        default="Files/bronze/healthcare_dataset.csv",
        help="Path inside Lakehouse (Files/...)",
    )
    ap.add_argument("--workspace", default=os.environ.get("FABRIC_WORKSPACE_ID", DEFAULT_WORKSPACE))
    ap.add_argument("--lakehouse", default=os.environ.get("FABRIC_LAKEHOUSE_ID", DEFAULT_LAKEHOUSE))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    path = os.path.abspath(args.file)
    if not os.path.isfile(path):
        print(f"Missing file: {path}", file=sys.stderr)
        return 1

    size = os.path.getsize(path)
    print(f"Local: {path} ({size} bytes)")
    print(f"Remote: {args.remote}  workspace={args.workspace[:8]}… lakehouse={args.lakehouse[:8]}…")

    if args.dry_run:
        print("Dry run — exiting")
        return 0

    token = get_storage_token()

    # 1) Create empty file
    create_url = onelake_url(args.workspace, args.lakehouse, args.remote, "resource=file")
    code, body = http_request(
        "PUT",
        create_url,
        token,
        None,
        {"Content-Length": "0"},
    )
    if code not in (200, 201):
        print(f"Create file failed HTTP {code}: {body[:500]!r}", file=sys.stderr)
        return 1
    print(f"Create file: HTTP {code}")

    # 2) Append chunks
    position = 0
    with open(path, "rb") as f:
        while True:
            chunk = f.read(CHUNK)
            if not chunk:
                break
            n = len(chunk)
            append_url = onelake_url(
                args.workspace,
                args.lakehouse,
                args.remote,
                f"action=append&position={position}",
            )
            code, body = http_request(
                "PATCH",
                append_url,
                token,
                chunk,
                {"Content-Length": str(n), "Content-Type": "application/octet-stream"},
            )
            if code not in (202, 200):
                print(f"Append @ {position} failed HTTP {code}: {body[:500]!r}", file=sys.stderr)
                return 1
            position += n
            print(f"  append: {position} / {size} bytes")

    # 3) Flush
    flush_url = onelake_url(
        args.workspace,
        args.lakehouse,
        args.remote,
        f"action=flush&position={position}",
    )
    code, body = http_request("PATCH", flush_url, token, None, {"Content-Length": "0"})
    if code not in (200, 201):
        print(f"Flush failed HTTP {code}: {body[:500]!r}", file=sys.stderr)
        return 1
    print(f"Flush: HTTP {code} — done ({position} bytes)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
