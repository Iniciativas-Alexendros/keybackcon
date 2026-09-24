# Contribuir a keybackcon

### Propósito de este documento

- **Objetivos:** Explicar setup, flujo de rama/PR y reglas locales para contribuir sin romper el protocolo HID ni la identidad de cero dependencias.
- **Estructura:** Idioma → setup → flujo de trabajo → comprobaciones antes del PR → reglas.
- **Contenido a integrar según contexto:** Adapta Cargo, GUI y `make` de este repo. No copies un flujo npm/pnpm ni crates de HID ajenos. Un cambio de `src/protocol.rs` exige ADR.

Idioma: este fichero, `README.md` y `docs/guides|runbooks` en español.

Lee también [AGENTS.md](AGENTS.md), [ARCHITECTURE.md](ARCHITECTURE.md) y [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Setup

```bash
# Rust ≥ 1.87 (MSRV) + rustfmt + clippy
# Python 3 (GUI; py_compile no necesita GTK en CI)
make lint && make test
```

Detalle en [`docs/guides/desarrollo.md`](docs/guides/desarrollo.md).

## Flujo de trabajo

Rama `feat/*` / `fix/*` / `docs/*` / `chore/*` → PR → squash → merge a `main`. Los tags `vX.Y.Z` los lanza el mantenedor; `release.yml` publica artefactos.

## Antes de un PR

```bash
make validate
```

Equivale a `lint` + `test` + `smoke`. El job `build` del CI es `cargo build --release`.

## Reglas

- Tocar `src/protocol.rs`, ioctl o informes HID → ADR en [`docs/architecture/decisions/DECISIONS.md`](docs/architecture/decisions/DECISIONS.md).
- No añadas crates al CLI (ADR 2) sin confirmación.
- Coverage: no hay gate `llvm-cov`; no lo inventes. Los 27 tests + smoke son el contrato.
- No commitear `target/`, `__pycache__/`, `TASKS.md` ni secretos.
- Nuevos comandos CLI → documentar en `README.md` y, si cambia el contrato, ADR.
- Vulnerabilidades: [SECURITY.md](SECURITY.md), no un issue público.
