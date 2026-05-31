from __future__ import annotations

import os
import tomllib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, Final

# Default values for every Config field. The Config dataclass declares
# the same defaults; this table is the source of truth used by load().
_DEFAULTS: Final[dict[str, Any]] = {
    "out_root": Path("output"),
    "max_iterations": 1,
    "exec_timeout_s": 30.0,
    "model": "claude-opus-4-7",
    "verbosity": 0,
    "sanity_enabled": True,
    # WS server (F19). Bind localhost only in v0 (ADR-0005); port is
    # configurable (0 = let the OS pick an ephemeral port, used in tests).
    "ws_host": "127.0.0.1",
    "ws_port": 8765,
}

# TOUCH_BACKEND_<FIELD_UPPER> -> field name.
_ENV_PREFIX: Final[str] = "TOUCH_BACKEND_"


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in {"1", "true", "yes", "on"}:
            return True
        if v in {"0", "false", "no", "off"}:
            return False
    raise ValueError(f"cannot coerce {value!r} to bool")


def _coerce_path(value: Any) -> Path:
    if isinstance(value, Path):
        return value
    return Path(str(value))


_COERCERS: Final[dict[str, Callable[[Any], Any]]] = {
    "out_root": _coerce_path,
    "max_iterations": lambda v: int(v),
    "exec_timeout_s": lambda v: float(v),
    "model": lambda v: str(v),
    "verbosity": lambda v: int(v),
    "sanity_enabled": _coerce_bool,
    "ws_host": lambda v: str(v),
    "ws_port": lambda v: int(v),
}


@dataclass(frozen=True)
class Config:
    out_root: Path = Path("output")
    max_iterations: int = 1
    exec_timeout_s: float = 30.0
    model: str = "claude-opus-4-7"
    verbosity: int = 0
    sanity_enabled: bool = True
    ws_host: str = "127.0.0.1"
    ws_port: int = 8765

    @staticmethod
    def load(
        cli_overrides: Mapping[str, Any] | None = None,
        *,
        pyproject_path: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> Config:
        """Build a Config by merging defaults <- pyproject <- env <- CLI.

        Later sources override earlier ones. Unknown keys at any layer
        are ignored (so a stray [tool.touch_backend] entry won't blow up).
        """
        merged: dict[str, Any] = dict(_DEFAULTS)
        merged.update(_from_pyproject(pyproject_path))
        merged.update(_from_env(env if env is not None else os.environ))
        merged.update(_filter_known(cli_overrides or {}))

        coerced = {name: _COERCERS[name](value) for name, value in merged.items()}
        return Config(**coerced)


def _known_fields() -> set[str]:
    return {f.name for f in fields(Config)}


def _filter_known(d: Mapping[str, Any]) -> dict[str, Any]:
    known = _known_fields()
    return {k: v for k, v in d.items() if k in known}


def _from_env(env: Mapping[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in _known_fields():
        key = f"{_ENV_PREFIX}{name.upper()}"
        if key in env:
            out[name] = env[key]
    return out


def _from_pyproject(path: Path | None) -> dict[str, Any]:
    p = path if path is not None else Path("pyproject.toml")
    if not p.exists():
        return {}
    with p.open("rb") as fh:
        data = tomllib.load(fh)
    section = data.get("tool", {}).get("touch_backend", {})
    if not isinstance(section, dict):
        return {}
    return _filter_known(section)
