from __future__ import annotations

import json
from pathlib import Path

from synapse_engine import run_pipeline


def main() -> None:
    seed = "privatlån upp till 800 000"
    base = Path(__file__).resolve().parent
    spec_root = base / "spec"
    out_dir = base / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph, related = run_pipeline(seed_phrase=seed, language="sv", market="SE", spec_root=spec_root, target=50)

    (out_dir / "GraphArtifact.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "RelatedQueriesOutput.json").write_text(json.dumps(related, ensure_ascii=False, indent=2), encoding="utf-8")

    # Create a self-contained viewer HTML with the graph embedded as sample.
    viewer_src = spec_root / "05_visual" / "synapse-map-viewer.html"
    html = viewer_src.read_text(encoding="utf-8")
    # Replace the sample const (very simple replace)
    marker = "const sample ="
    start = html.find(marker)
    if start != -1:
        end = html.find(";\n\nconst svg", start)
        if end != -1:
            prefix = html[: start + len(marker)]
            suffix = html[end:]
            embedded = " " + json.dumps(graph, ensure_ascii=False)
            html = prefix + embedded + suffix

    (out_dir / "viewer.html").write_text(html, encoding="utf-8")

    print("Wrote:")
    print(" -", out_dir / "GraphArtifact.json")
    print(" -", out_dir / "RelatedQueriesOutput.json")
    print(" -", out_dir / "viewer.html")


if __name__ == "__main__":
    main()
