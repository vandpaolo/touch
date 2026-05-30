"""F3 Worker shim.

Selects the adapter for the active backend and delegates ``Intent ->
backend source`` translation. In v0 only the build123d adapter is wired;
NX-Open journal emission is a v0.1 deliverable, surfaced here as a stub
so the public API matches the eventual two-backend shape.
"""

from __future__ import annotations

from touch_backend.adapters import build123d_target
from touch_backend.intent import Intent


def emit_code(intent: Intent) -> str:
    """Emit build123d Python source for ``intent``.

    Delegates to ``touch_backend.adapters.build123d_target.emit``.
    """
    return build123d_target.emit(intent)


def emit_journal(intent: Intent) -> str:
    """Emit NX Open journal source for ``intent``.

    Not implemented in v0; v0.1 adds the NX backend.
    """
    raise NotImplementedError("v0.1: NX journal emission not implemented")
