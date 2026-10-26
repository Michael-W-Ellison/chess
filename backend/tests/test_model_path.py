"""
Which language model the backend loads (Settings.get_model_path): the user's own model at
MODEL_PATH, else the one that comes with the packaged app (BUNDLED_MODEL_PATH).
"""

from utils.config import Settings


def test_own_model_is_used_when_present(tmp_path):
    own, bundled = tmp_path / "own.gguf", tmp_path / "bundled.gguf"
    own.write_bytes(b"GGUF")
    bundled.write_bytes(b"GGUF")
    settings = Settings(MODEL_PATH=str(own), BUNDLED_MODEL_PATH=str(bundled))
    assert settings.get_model_path() == own.resolve()


def test_bundled_model_is_used_without_an_own_model(tmp_path):
    bundled = tmp_path / "bundled.gguf"
    bundled.write_bytes(b"GGUF")
    settings = Settings(MODEL_PATH=str(tmp_path / "missing.gguf"), BUNDLED_MODEL_PATH=str(bundled))
    assert settings.get_model_path() == bundled.resolve()


def test_missing_models_report_the_own_path(tmp_path):
    settings = Settings(MODEL_PATH=str(tmp_path / "missing.gguf"), BUNDLED_MODEL_PATH=str(tmp_path / "gone.gguf"))
    assert settings.get_model_path() == (tmp_path / "missing.gguf").resolve()
