"""Smoke tests for the offline pipeline (no API keys required)."""
import pytest


def test_pipeline_produces_valid_graph(spec_root):
    """Offline pipeline produces a valid GraphArtifact."""
    from synapse_engine.pipeline import run_pipeline

    graph, related = run_pipeline(
        "privatlån upp till 800 000",
        spec_root=spec_root,
        target=20,
    )
    assert "seed" in graph
    assert "nodes" in graph
    assert "edges" in graph
    assert "clusters" in graph
    assert "legend" in graph
    assert len(graph["nodes"]) == 20


def test_pipeline_related_queries(spec_root):
    """Pipeline produces a valid RelatedQueriesOutput."""
    from synapse_engine.pipeline import run_pipeline

    graph, related = run_pipeline(
        "privatlån upp till 800 000",
        spec_root=spec_root,
        target=15,
    )
    assert "seed" in related
    assert "selected" in related
    assert len(related["selected"]) == 15
    # Check ranking
    ranks = [s["rank"] for s in related["selected"]]
    assert ranks == list(range(1, 16))


def test_pipeline_seed_structure(spec_root):
    """Seed node has required fields."""
    from synapse_engine.pipeline import run_pipeline

    graph, _ = run_pipeline("casino online", spec_root=spec_root, target=10)
    seed = graph["seed"]
    assert "id" in seed
    assert "phrase" in seed
    assert "x" in seed
    assert "y" in seed
    assert "intent" in seed
    assert "perspective" in seed
    assert 0.0 <= seed["x"] <= 1.0
    assert 0.0 <= seed["y"] <= 1.0


def test_pipeline_node_fields(spec_root):
    """Each node has all required fields."""
    from synapse_engine.pipeline import run_pipeline

    graph, _ = run_pipeline("casino online", spec_root=spec_root, target=10)
    for node in graph["nodes"]:
        assert "id" in node
        assert "phrase" in node
        assert "x" in node
        assert "y" in node
        assert "cluster_id" in node
        assert "intent" in node
        assert "perspective" in node
        assert "confidence" in node
        assert "provenance" in node
        assert 0.0 <= node["x"] <= 1.0
        assert 0.0 <= node["y"] <= 1.0
        assert 0.0 <= node["confidence"] <= 1.0


def test_pipeline_cluster_count(spec_root):
    """Pipeline produces a reasonable number of clusters."""
    from synapse_engine.pipeline import run_pipeline

    graph, _ = run_pipeline("privatlån upp till 800 000", spec_root=spec_root, target=30)
    clusters = graph["clusters"]
    assert 2 <= len(clusters) <= 8
    # Each cluster has a centroid
    for c in clusters:
        assert "centroid" in c
        assert "x" in c["centroid"]
        assert "y" in c["centroid"]
