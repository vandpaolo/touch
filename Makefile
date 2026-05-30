# touch_backend dev tooling.
# Secrets (F29): the dev Anthropic key lives SOPS-encrypted in
# secrets.env.sops.yaml; the plaintext .env is gitignored and never committed.

.PHONY: secrets-decrypt secrets-encrypt hooks ci

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
