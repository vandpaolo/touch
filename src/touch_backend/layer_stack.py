"""The Layer Stack — a part as an ordered list of build123d layers (ADR-0012).

A part is **not** a flat op history any more; it is a *stack* of `Layer`s, each
a build123d code block that transforms the previous solid::

    body_0 = f_0()            # the first layer creates geometry
    body_1 = f_1(body_0)      # each subsequent layer transforms the previous
    ...
    body_N = f_N(body_{N-1})

`emit(stack)` threads them into one runnable build123d script, carrying the
solid through the module-scope variable ``body`` (the same export variable the
T0-T5 adapter and ADR-0004 use), and ending in ``export_step(body, ...)``.

Two layer kinds share one representation — a layer's authoritative, hashable
content is always its ``source`` (a build123d block operating on ``body``):

- **template** — a recognised v0 op (box / cylinder / sphere / chamfer); its
  ``source`` is *generated* from ``template`` + ``params`` at construction, and
  the parametric metadata is retained so the FE can render an editable card
  (F40). The recognizer that runs the inverse direction is Day 4.
- **code** — freeform build123d, inlined **verbatim** (the long tail: gears,
  lofts, patterns). ``template``/``params`` are empty.

This module owns the model and emission only. The deterministic fold +
per-layer cache (`rebuild`, `input_hash`/`output_hash`) is Day 2; provenance,
recognition, the shared-document mutation API + compare-and-swap, and
selection-scoped emission land in later days. Append-only in v0 (ADR-0012).
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Literal

from touch_backend._generated.protocol import Selection
from touch_backend.mesh_cache import MeshCache

if TYPE_CHECKING:
    from touch_backend.tessellate import Mesh

LayerKind = Literal["template", "code"]
Template = Literal["box", "cylinder", "sphere", "chamfer"]

# The module-scope build123d variable every layer reads/reassigns. Kept equal to
# the T0-T5 export variable (ADR-0004) so recognised-template snippets are
# byte-compatible with the adapter's output (eases Day 4 recognition + Day 7
# `.touch` migration).
_BODY = "body"

# Selection-scoped layers (a chamfer that targets a finder-resolved face) emit
# `resolve_face(...)`, so the preamble imports it unconditionally (matching the
# T0-T5 operation adapter). It is import-cheap — OCP loads lazily inside it.
_PREAMBLE = "from build123d import *\nfrom touch_backend.finder import resolve_face"
_EXPORT = f'export_step({_BODY}, "part.step")'


class LayerStackError(Exception):
    """A layer could not be built or a stack could not be emitted."""


class StaleRevisionError(LayerStackError):
    """A mutation's expected revision didn't match the stack head (CAS reject, N16).

    The caller re-reads the head and re-plans; the stack is left untouched.
    """

    def __init__(self, expected: int, head: int) -> None:
        self.expected = expected
        self.head = head
        super().__init__(f"stale revision: expected {expected}, head is {head}")


# Content address of the empty input solid — the input_hash of the first layer.
_BASE_HASH = hashlib.sha256(b"").hexdigest()


@dataclass(frozen=True)
class RebuildResult:
    """Outcome of folding the stack to a tessellated mesh."""

    mesh: Mesh
    revision: int
    cache_hit: bool
    # Index of the first layer whose cumulative result was not already cached
    # (the fold's resume point); None on a full cache hit. `executed_layers` is
    # 0 on a hit and len(layers) on a miss — v0 rebuilds the whole stack from
    # clean state on any miss so a given state has one canonical face ordering
    # (the within-session capture, ADR-0011); the cache makes revisiting any
    # previously-built state (undo / redo / reopen) free.
    first_dirty: int | None
    executed_layers: int


@dataclass(frozen=True)
class Layer:
    """One edit in a part: a build123d block transforming the previous solid.

    `source` is the single source of truth for emission and (Day 2) content
    hashing. `input_hash`/`output_hash` are populated by the fold (Day 2) and
    are `None` until then.
    """

    id: str
    kind: LayerKind
    source: str
    template: Template | None = None
    params: dict[str, float | str | bool] = field(default_factory=dict)
    selection: Selection | None = None
    input_hash: str | None = None
    output_hash: str | None = None

    @classmethod
    def from_template(
        cls,
        template: Template,
        params: dict[str, float | str | bool],
        *,
        id: str,
        selection: Selection | None = None,
    ) -> Layer:
        """A recognised parametric layer; its source is generated from params."""
        source = _emit_template(template, params)
        return cls(
            id=id,
            kind="template",
            source=source,
            template=template,
            params=dict(params),
            selection=selection,
        )

    @classmethod
    def from_code(
        cls,
        source: str,
        *,
        id: str,
        selection: Selection | None = None,
    ) -> Layer:
        """A freeform build123d layer; `source` is inlined verbatim."""
        if not source.strip():
            raise LayerStackError(f"code layer {id!r} has empty source")
        return cls(id=id, kind="code", source=source, selection=selection)


@dataclass
class LayerStack:
    """The active part: an ordered list of `Layer`s + a monotonic revision.

    The mutation API (add / delete-last) and compare-and-swap on `revision`
    are Day 5; v0 is append-only (ADR-0012/0013).
    """

    layers: list[Layer] = field(default_factory=list)
    revision: int = 0

    def add_layer(self, layer: Layer, *, expect_rev: int) -> int:
        """Append a layer (compare-and-swap on `expect_rev`); return the new revision.

        Append-only (ADR-0012): the layer goes on the top of the stack. Rejects
        with `StaleRevisionError` if the head has moved since the caller read it
        (N16), leaving the stack untouched. The caller builds the `Layer`
        (classifying code vs template via `templates.recognize`).
        """
        self._cas(expect_rev)
        self.layers = [*self.layers, layer]
        self.revision += 1
        return self.revision

    def delete_last(self, *, expect_rev: int) -> Layer:
        """Remove and return the top layer (compare-and-swap on `expect_rev`).

        The only deletion in v0 (append-only); rejects a stale revision (N16) or
        an empty stack without mutating.
        """
        self._cas(expect_rev)
        if not self.layers:
            raise LayerStackError("delete_last on an empty stack")
        *rest, removed = self.layers
        self.layers = rest
        self.revision += 1
        return removed

    def _cas(self, expect_rev: int) -> None:
        if expect_rev != self.revision:
            raise StaleRevisionError(expect_rev, self.revision)

    def rebuild(
        self, *, build: Callable[[str], Mesh], cache: MeshCache
    ) -> RebuildResult:
        """Fold the stack to a tessellated mesh, content-addressed cache in front.

        `build(source) -> Mesh` is the geometry step (the Executor subprocess +
        tessellate, injected so this module stays OCP-free and unit-testable).
        A rebuild whose emitted source is already cached returns instantly with
        no `build` call; otherwise the whole stack is built once (each layer's
        code runs exactly once) and the result cached.
        """
        if not self.layers:
            raise LayerStackError("empty stack: nothing to build")
        self._assign_hashes()
        source = emit(self)
        key = MeshCache.key(source)
        cached = cache.get(key)
        if cached is not None:
            return RebuildResult(cached, self.revision, True, None, 0)
        first_dirty = self._first_dirty(cache)
        mesh = build(source)
        cache.put(key, mesh)
        return RebuildResult(mesh, self.revision, False, first_dirty, len(self.layers))

    def _assign_hashes(self) -> None:
        """Populate each layer's chained ``(input_hash, output_hash)``.

        A layer's output is a pure function of its input solid + its source, so
        ``output_hash = H(input_hash, source)`` and the next layer's input is
        this output. The chain is the per-layer content address the fold and
        provenance (Day 3) key on.
        """
        prev = _BASE_HASH
        rehashed: list[Layer] = []
        for layer in self.layers:
            digest = hashlib.sha256(f"{prev}\n{layer.source}".encode()).hexdigest()
            rehashed.append(replace(layer, input_hash=prev, output_hash=digest))
            prev = digest
        self.layers = rehashed

    def _first_dirty(self, cache: MeshCache) -> int:
        """Index of the first layer whose cumulative prefix isn't cached.

        Probes each prefix's emitted-source key against the cache; the first
        gap is the fold's resume point. All-cached returns ``len(layers)``.
        """
        for k in range(1, len(self.layers) + 1):
            prefix = LayerStack(self.layers[:k])
            if cache.get(MeshCache.key(emit(prefix))) is None:
                return k - 1
        return len(self.layers)


def emit(stack: LayerStack) -> str:
    """Render the whole stack as one runnable build123d script (deterministic).

    Same stack in → byte-identical source out: no clock, no environment, params
    formatted by explicit key. The fold (Day 2) re-uses this for partial
    rebuilds; for now it always emits the full stack.
    """
    if not stack.layers:
        raise LayerStackError("empty stack: nothing to emit")
    sections = [_PREAMBLE]
    for layer in stack.layers:
        header = f"# layer {layer.id} ({layer.kind}"
        header += f":{layer.template})" if layer.template else ")"
        sections.append(f"{header}\n{layer.source.strip()}")
    sections.append(_EXPORT)
    return "\n\n".join(sections) + "\n"


# ---------- recognised-template emitters (thread `body`) -------------------
#
# Kept deliberately small and exact (ADR-0012: "keep template recognition dumb")
# and byte-aligned with the T0-T5 adapter's per-kind output. Selection-scoped
# emission (a chamfer that targets one finder-resolved face/edge, F45) is Day 9;
# v0 chamfer is all-edges, matching the adapter.


def _fmt(value: float | str | bool) -> str:
    """Format a numeric param as build123d source (10 -> "10.0", like the adapter)."""
    return repr(float(value))


def _is_truthy(value: float | str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return isinstance(value, str) and value.strip().lower() == "true"


def _emit_box(p: dict[str, float | str | bool]) -> str:
    dims = f"{_fmt(p['length'])}, {_fmt(p['width'])}, {_fmt(p['height'])}"
    if _is_truthy(p.get("centered")):
        align = "align=(Align.CENTER, Align.CENTER, Align.CENTER)"
        return f"{_BODY} = Box({dims}, {align})"
    return f"{_BODY} = Box({dims})"


def _emit_cylinder(p: dict[str, float | str | bool]) -> str:
    radius, height = _fmt(p["radius"]), _fmt(p["height"])
    axis = p.get("axis")
    if isinstance(axis, str) and axis.lower() == "x":
        return f"{_BODY} = Cylinder({radius}, {height}, rotation=(0, 90, 0))"
    if isinstance(axis, str) and axis.lower() == "y":
        return f"{_BODY} = Cylinder({radius}, {height}, rotation=(90, 0, 0))"
    return f"{_BODY} = Cylinder({radius}, {height})"


def _emit_sphere(p: dict[str, float | str | bool]) -> str:
    return f"{_BODY} = Sphere({_fmt(p['radius'])})"


def _emit_chamfer(p: dict[str, float | str | bool]) -> str:
    return f"{_BODY} = chamfer({_BODY}.edges(), {_fmt(p['distance'])})"


_TEMPLATE_DISPATCH = {
    "box": _emit_box,
    "cylinder": _emit_cylinder,
    "sphere": _emit_sphere,
    "chamfer": _emit_chamfer,
}


def _emit_template(template: Template, params: dict[str, float | str | bool]) -> str:
    emitter = _TEMPLATE_DISPATCH.get(template)
    if emitter is None:
        raise LayerStackError(f"unknown template {template!r}")
    try:
        return emitter(params)
    except KeyError as missing:
        raise LayerStackError(
            f"template {template!r} missing required param {missing}"
        ) from missing
