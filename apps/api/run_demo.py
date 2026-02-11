"""Run demo pipeline for two seeds and generate artifacts.

No API keys needed — runs in full offline mode.
"""
from __future__ import annotations

import json
from pathlib import Path

from synapse_engine import run_pipeline


DEMO_SEEDS = [
    {"seed": "casino online", "slug": "demo-casino", "target": 30},
    {"seed": "privatlån upp till 800 000", "slug": "demo-loan", "target": 30},
]


def embed_viewer(graph: dict, viewer_src: Path) -> str:
    """Create a self-contained viewer HTML with the graph embedded."""
    html = viewer_src.read_text(encoding="utf-8")
    marker = "const sample ="
    start = html.find(marker)
    if start != -1:
        end = html.find(";\n\nconst svg", start)
        if end != -1:
            prefix = html[: start + len(marker)]
            suffix = html[end:]
            embedded = " " + json.dumps(graph, ensure_ascii=False)
            html = prefix + embedded + suffix
    return html


def main() -> None:
    base = Path(__file__).resolve().parent
    spec_root = base / "spec"
    artifacts_dir = base / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    viewer_src = spec_root / "05_visual" / "synapse-map-viewer.html"

    for demo in DEMO_SEEDS:
        seed = demo["seed"]
        slug = demo["slug"]
        target = demo["target"]

        print(f"\n--- Running: {seed} (target={target}) ---")
        graph, related = run_pipeline(
            seed_phrase=seed,
            language="sv",
            market="SE",
            spec_root=spec_root,
            target=target,
        )

        # Save artifacts
        (artifacts_dir / f"{slug}.json").write_text(
            json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (artifacts_dir / f"{slug}-related.json").write_text(
            json.dumps(related, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Self-contained viewer
        if viewer_src.exists():
            html = embed_viewer(graph, viewer_src)
            (artifacts_dir / f"{slug}-viewer.html").write_text(html, encoding="utf-8")

        n_nodes = len(graph.get("nodes", []))
        n_clusters = len(graph.get("clusters", []))
        n_edges = len(graph.get("edges", []))
        print(f"  {n_nodes} nodes, {n_clusters} clusters, {n_edges} edges")
        print(f"  Saved: artifacts/{slug}.json")

    # Also write a single combined viewer (last seed) to out/ for backwards compat
    out_dir = base / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    graph, related = run_pipeline(
        seed_phrase="privatlån upp till 800 000",
        language="sv", market="SE", spec_root=spec_root, target=50,
    )
    (out_dir / "GraphArtifact.json").write_text(
        json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "RelatedQueriesOutput.json").write_text(
        json.dumps(related, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if viewer_src.exists():
        html = embed_viewer(graph, viewer_src)
        (out_dir / "viewer.html").write_text(html, encoding="utf-8")

    print(f"\nDone. Artifacts in: {artifacts_dir}")
    print(f"Legacy output in: {out_dir}")


if __name__ == "__main__":
    main()
