from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from maquette.config import Config


@pytest.fixture
def empty_pyproject(tmp_path: Path) -> Path:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname = 'unrelated'\n", encoding="utf-8")
    return p


def test_load_with_no_sources_returns_defaults(empty_pyproject: Path):
    cfg = Config.load({}, pyproject_path=empty_pyproject, env={})
    assert cfg == Config()
    assert cfg.out_root == Path("output")
    assert cfg.max_iterations == 1
    assert cfg.exec_timeout_s == 30.0
    assert cfg.model == "claude-opus-4-7"
    assert cfg.verbosity == 0
    assert cfg.sanity_enabled is True


def test_dataclass_defaults_match_load_defaults(empty_pyproject: Path):
    assert Config() == Config.load({}, pyproject_path=empty_pyproject, env={})


def test_cli_override_beats_default(empty_pyproject: Path):
    cfg = Config.load(
        {"model": "claude-haiku-4-5"},
        pyproject_path=empty_pyproject,
        env={},
    )
    assert cfg.model == "claude-haiku-4-5"


def test_env_override_beats_default(empty_pyproject: Path):
    cfg = Config.load(
        {},
        pyproject_path=empty_pyproject,
        env={"MAQUETTE_MAX_ITERATIONS": "5"},
    )
    assert cfg.max_iterations == 5


def test_pyproject_override_beats_default(tmp_path: Path):
    pyp = tmp_path / "pyproject.toml"
    pyp.write_text("[tool.maquette]\nmax_iterations = 7\n", encoding="utf-8")
    cfg = Config.load({}, pyproject_path=pyp, env={})
    assert cfg.max_iterations == 7


def test_env_beats_pyproject(tmp_path: Path):
    pyp = tmp_path / "pyproject.toml"
    pyp.write_text("[tool.maquette]\nmax_iterations = 7\n", encoding="utf-8")
    cfg = Config.load({}, pyproject_path=pyp, env={"MAQUETTE_MAX_ITERATIONS": "9"})
    assert cfg.max_iterations == 9


def test_cli_beats_env(empty_pyproject: Path):
    cfg = Config.load(
        {"max_iterations": 11},
        pyproject_path=empty_pyproject,
        env={"MAQUETTE_MAX_ITERATIONS": "9"},
    )
    assert cfg.max_iterations == 11


def test_cli_beats_pyproject_and_env(tmp_path: Path):
    pyp = tmp_path / "pyproject.toml"
    pyp.write_text("[tool.maquette]\nmax_iterations = 7\n", encoding="utf-8")
    cfg = Config.load(
        {"max_iterations": 13},
        pyproject_path=pyp,
        env={"MAQUETTE_MAX_ITERATIONS": "9"},
    )
    assert cfg.max_iterations == 13


def test_bool_coercion_from_env(empty_pyproject: Path):
    for env_val, expected in [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("yes", True),
        ("NO", False),
        ("On", True),
        ("off", False),
    ]:
        cfg = Config.load(
            {},
            pyproject_path=empty_pyproject,
            env={"MAQUETTE_SANITY_ENABLED": env_val},
        )
        assert cfg.sanity_enabled is expected, (env_val, expected)


def test_path_coercion_from_env(empty_pyproject: Path, tmp_path: Path):
    cfg = Config.load(
        {},
        pyproject_path=empty_pyproject,
        env={"MAQUETTE_OUT_ROOT": str(tmp_path / "runs")},
    )
    assert cfg.out_root == tmp_path / "runs"
    assert isinstance(cfg.out_root, Path)


def test_float_coercion_from_env(empty_pyproject: Path):
    cfg = Config.load(
        {},
        pyproject_path=empty_pyproject,
        env={"MAQUETTE_EXEC_TIMEOUT_S": "45.5"},
    )
    assert cfg.exec_timeout_s == 45.5


def test_unknown_keys_in_cli_overrides_ignored(empty_pyproject: Path):
    cfg = Config.load(
        {"flux_capacitor": "engaged"},
        pyproject_path=empty_pyproject,
        env={},
    )
    assert cfg == Config()


def test_unknown_keys_in_pyproject_ignored(tmp_path: Path):
    pyp = tmp_path / "pyproject.toml"
    pyp.write_text("[tool.maquette]\nflux_capacitor = 'engaged'\n", encoding="utf-8")
    cfg = Config.load({}, pyproject_path=pyp, env={})
    assert cfg == Config()


def test_missing_pyproject_path_is_silent(tmp_path: Path):
    cfg = Config.load({}, pyproject_path=tmp_path / "does-not-exist.toml", env={})
    assert cfg == Config()


def test_config_is_frozen():
    cfg = Config()
    with pytest.raises(FrozenInstanceError):
        cfg.model = "x"  # type: ignore[misc]
