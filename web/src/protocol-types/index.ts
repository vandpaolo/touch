// web/protocol-types — the FE's single import point for the wire protocol.
//
// These types are GENERATED from protocol/schema.json (the cross-language
// source of truth). Do not hand-edit them and do not import the generated
// file directly elsewhere — always go through this module.
//
// Regenerate after any schema change:  `make codegen`  (repo root)
//   → emits protocol/generated/ts/protocol.ts  (aliased here as @protocol)
//   → and src/touch_backend/_generated/protocol.py (pydantic, for the backend)
//
// `export type *` keeps this a pure type re-export (no runtime emit), which
// satisfies verbatimModuleSyntax and the "no project-internal value imports"
// dependency rule for the generated boundary.
export type * from '@protocol'
