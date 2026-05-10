#!/usr/bin/env python3
"""
Render PNG proof images from captured JSON and OpenAPI (no Fabric UI login).
Output filenames match SCREENSHOTS.md for resume / portfolio consistency.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "screenshots"
JSON_STATS = ROOT / "outputs/01_api_proof/api_stats_response_2026-03-11.json"


def fig_text_page(lines: list[str], title: str, outfile: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    body = "\n".join(lines)
    ax.text(
        0.02,
        0.98,
        body,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        wrap=False,
    )
    fig.tight_layout()
    fig.savefig(outfile, bbox_inches="tight")
    plt.close(fig)


def render_api_stats() -> None:
    with open(JSON_STATS, encoding="utf-8") as f:
        stats = json.load(f)
    ds = stats["dataset"]
    cond = stats["clinical"]["conditions"]
    lines = [
        "GET /api/stats (captured JSON — synthetic dataset)",
        "",
        f"total_encounters: {ds['total_encounters']}",
        f"unique_patients: {ds['unique_patients']}",
        "",
        "clinical.conditions (6):",
    ]
    for k, v in sorted(cond.items(), key=lambda x: -x[1]):
        lines.append(f"  {k}: {v}")
    outfile = SCREEN / "healthcare-da-api-stats.png"
    fig_text_page(lines, "Healthcare API — stats proof", outfile)
    print("Wrote", outfile)


def render_fastapi_routes() -> None:
    """Parse OpenAPI from running app, or fall back to static route list."""
    openapi_path = ROOT / "openapi_snapshot.json"
    routes: list[str] = []
    if openapi_path.exists():
        with open(openapi_path, encoding="utf-8") as f:
            spec = json.load(f)
        paths = spec.get("paths") or {}
        for p in sorted(paths):
            methods = [m.upper() for m in paths[p] if m not in ("parameters",)]
            if methods:
                routes.append(f"  {', '.join(methods)}  {p}")
    else:
        routes = [
            "  GET  /",
            "  GET  /api/encounters",
            "  GET  /api/encounters/{encounter_id}",
            "  GET  /api/patients",
            "  GET  /api/doctors",
            "  GET  /api/hospitals",
            "  GET  /api/conditions",
            "  GET  /api/medications",
            "  GET  /api/insurance",
            "  GET  /api/stats",
            "  GET  /api/search",
        ]
    lines = [
        "FastAPI — 11 GET endpoints (OpenAPI /docs)",
        "",
        *routes,
        "",
        "Tip: run API locally then:",
        "  curl -s http://127.0.0.1:8000/openapi.json > openapi_snapshot.json",
        "  python3 scripts/render_proof_screenshots.py",
    ]
    outfile = SCREEN / "healthcare-da-fastapi-docs.png"
    fig_text_page(lines, "Healthcare API — route inventory", outfile)
    print("Wrote", outfile)


def _ascii_lines(text: str, max_lines: int = 28) -> list[str]:
    out: list[str] = []
    for line in text.splitlines()[:max_lines]:
        out.append(line.replace("\u2705", "[OK]").replace("\u26a0\ufe0f", "[!]"))
    return out


def render_fabric_workspace_summary() -> None:
    proof = ROOT / "outputs/03_bi_proof/semantic_model_validation_2026-03-11.md"
    text = proof.read_text(encoding="utf-8") if proof.exists() else "(missing proof file)"
    lines = [
        "Microsoft Fabric — workspace / semantic validation (script output)",
        "",
        *_ascii_lines(text, 25),
        "",
        "(Replace with browser screenshot of Fabric UI when convenient.)",
    ]
    outfile = SCREEN / "healthcare-da-fabric-workspace.png"
    fig_text_page(lines, "Fabric — semantic model check", outfile)
    print("Wrote", outfile)


def render_fabric_lakehouse_summary() -> None:
    proof = ROOT / "outputs/03_bi_proof/fabric_lakehouse_proof_2026-03-15.md"
    raw = proof.read_text(encoding="utf-8") if proof.exists() else "(missing proof file)"
    lines: list[str] = [
        "Microsoft Fabric — lakehouse proof (markdown summary)",
        "",
    ]
    for line in raw.splitlines():
        if line.startswith("**Location:**") and "abfss://" in line:
            lines.append("**Location:** (OneLake path redacted in image — see repo .md for full)")
            continue
        lines.append(line.replace("\u2705", "[OK]"))
        if len(lines) > 32:
            break
    lines.append("")
    lines.append("(Replace with lakehouse UI screenshot when convenient.)")
    outfile = SCREEN / "healthcare-da-fabric-lakehouse.png"
    fig_text_page(lines, "Fabric — lakehouse + table", outfile)
    print("Wrote", outfile)


def try_fetch_openapi() -> None:
    """Best-effort: if API is up, refresh openapi snapshot."""
    try:
        out = subprocess.run(
            ["curl", "-sS", "--max-time", "2", "http://127.0.0.1:8000/openapi.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip().startswith("{"):
            (ROOT / "openapi_snapshot.json").write_text(out.stdout, encoding="utf-8")
            print("Refreshed openapi_snapshot.json from running API")
    except OSError:
        pass


def main() -> int:
    SCREEN.mkdir(parents=True, exist_ok=True)
    try_fetch_openapi()
    render_api_stats()
    render_fastapi_routes()
    render_fabric_workspace_summary()
    render_fabric_lakehouse_summary()
    return 0


if __name__ == "__main__":
    sys.exit(main())
