import pytest

from oracle import config


@pytest.fixture(autouse=True)
def traces_in_tmp(tmp_path, monkeypatch):
    """Tests must not fill the real traces/ folder (that one is evidence)."""
    monkeypatch.setattr(config, "TRACES", tmp_path / "traces")
