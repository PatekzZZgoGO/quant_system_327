from utils.result_metadata import build_result_metadata, compute_config_hash, generate_run_id


def test_generate_run_id_has_prefix():
    run_id = generate_run_id("factor")
    assert run_id.startswith("factor_")


def test_compute_config_hash_is_stable():
    config = {"model": "simple_alpha", "top_n": 20, "weights": {"alpha": 1.0}}
    assert compute_config_hash(config) == compute_config_hash(dict(config))


def test_build_result_metadata_includes_required_fields():
    metadata = build_result_metadata(
        config={"model": "simple_alpha"},
        source_window={"start": "2024-01-01", "end": "2024-01-31"},
        universe_version="analysis_universe:limit=all:count=100",
        extra={"model": "simple_alpha"},
    )

    assert "run_id" in metadata
    assert metadata["version"] == "v1"
    assert "config_hash" in metadata
    assert "created_at" in metadata
    assert metadata["source_window"] == {"start": "2024-01-01", "end": "2024-01-31"}
    assert metadata["universe_version"] == "analysis_universe:limit=all:count=100"
    assert metadata["model"] == "simple_alpha"
