# Changelog

La fuente de verdad son los tags y `git-cliff`. Resumen:

## [2.0.0] — 2026-09-14
- Renombrado a `keybackcon` ("Keyboard Backlight Controls"), repo
  `Iniciativas-Alexendros/keybackcon`, App ID `org.iniciativas.keybackcon`.
- CLI migrado a Cargo por módulos (`lamp/color/state/animation/cli`), cero
  dependencias, mismos comandos + alias `bright/auto/anim`, rutas nuevas con
  migración heredada `kbd-rgb`.
- GUI rediseñada: mesa de luz con light-stage, filtros + tono propio,
  intensidad −/+, movimiento Fijar/Respirar/Arcoíris, estado vivo, toasts,
  atajos y respeto a `gtk-enable-animations`.
- Packaging (`packaging/`), icono, `scripts/install.sh` idempotente y
  `scripts/smoke.sh`; systemd/udev/desktop con el nombre nuevo.
- CI (fmt+clippy+test+smoke) y release por tag con binario adjunto.
