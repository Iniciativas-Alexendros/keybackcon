<!-- canon-managed: true -->

### Propósito de este documento

- **Objetivos:** Plantilla de PR para describir el cambio y exigir lint, tests, smoke y jobs `quality` / `test` / `build` / `smoke`.
- **Estructura:** Qué cambia → checklist (make, docs, artefactos, CI).
- **Contenido a integrar según contexto:** Adapta el checklist a Cargo y `scripts/smoke.sh`. No copies plantillas de otro paquete. Si el PR toca HID/`protocol.rs`, enlaza un ADR.

## Qué cambia

<!-- feat/fix/docs + alcance en una o dos frases -->

## Checklist

- [ ] `make lint`
- [ ] `make test`
- [ ] `make smoke` (o `make validate`)
- [ ] Docs actualizadas (`README.md` y ADR si toca protocolo, CLI o empaquetado)
- [ ] Sin artefactos (`target/`, `__pycache__/`) ni secretos
- [ ] CI `quality` / `test` / `build` / `smoke` en verde
