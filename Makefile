# touch_backend dev tooling.
# Secrets (F29): the dev Anthropic key lives SOPS-encrypted in
# secrets.env.sops.yaml; the plaintext .env is gitignored and never committed.

.PHONY: secrets-decrypt secrets-encrypt hooks codegen ci

# Generate protocol bindings from protocol/schema.json (the single source of truth):
# pydantic models for the backend + TS types for the frontend (ADR-0005). Commit the output.
codegen:
	datamodel-codegen \
	  --input protocol/schema.json --input-file-type jsonschema \
	  --output-model-type pydantic_v2.BaseModel \
	  --target-python-version 3.12 \
	  --use-union-operator --use-standard-collections \
	  --disable-timestamp --use-schema-description \
	  --output src/touch_backend/_generated/protocol.py
	npx --yes json-schema-to-typescript@15 protocol/schema.json \
	  --output protocol/generated/ts/protocol.ts
	@echo "regenerated: src/touch_backend/_generated/protocol.py + protocol/generated/ts/protocol.ts"

# Decrypt the committed secrets into a working dev .env (dotenv format).
secrets-decrypt:
	sops --decrypt --input-type yaml --output-type dotenv secrets.env.sops.yaml > .env
	@echo "wrote .env (gitignored)"

# Re-encrypt the local .env back into the committed secrets file.
secrets-encrypt:
	sops --encrypt --input-type dotenv --output-type yaml .env > secrets.env.sops.yaml
	@echo "wrote secrets.env.sops.yaml"

# Point git at the in-repo hooks (installs the plaintext-.env pre-commit guard).
hooks:
	git config core.hooksPath .githooks
	@echo "core.hooksPath -> .githooks"

# Full local CI gate (mirrors .github/workflows/ci.yml).
ci:
	ruff check src/ tests/
	ruff format --check src/ tests/
	pyright --pythonpath "$$(which python)" src/
	lint-imports
	pytest -q
