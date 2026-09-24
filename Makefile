.PHONY: lint test smoke build validate help

CARGO := cargo

##@ Calidad

lint: ## fmt, clippy, rustdoc y py_compile
	$(CARGO) fmt --check
	$(CARGO) clippy --all-targets -- -D warnings
	RUSTDOCFLAGS="-D warnings" $(CARGO) doc --no-deps
	python3 -m py_compile gui/*.py

test: ## Tests unitarios (hilos 1: pidfile)
	$(CARGO) test -- --test-threads=1

smoke: ## Binario, GUI y packaging
	bash scripts/smoke.sh

build: ## Binario release (artefacto)
	$(CARGO) build --release

validate: lint test smoke ## Fachada local = quality + test + smoke

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-12s\033[0m %s\n", $$1, $$2}'
