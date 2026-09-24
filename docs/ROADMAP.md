# Hoja de ruta

### Propósito de este documento

- **Objetivos:** Dejar visible qué está hecho (hasta 2.2.1) y qué queda (AUR, multi-zona).
- **Estructura:** Lista de hitos marcados y pendientes.
- **Contenido a integrar según contexto:** No copies un roadmap de otro producto. Los ADR y el protocolo no se mueven a este archivo.

- [x] v2.0.0 — Cargo por módulos, GUI mesa de luz, packaging, CI/release
- [x] v2.1.0 — auditoría integral: robustez HID, CLI estructurada sin dependencias, protocolo centralizado, calidad (rustdoc, pedantic, 24 tests) y empaquetado .deb/AUR preparado
- [x] Probar en hardware AERO X16 cada comando + animaciones a 60 fps
- [x] Empaquetado en repo: metadata `cargo-deb`, `PKGBUILD` de AUR y release con `.deb` + SBOM + attestation
- [x] Publicar `.deb` en GitHub Releases (el workflow ya lo construye al empujar el tag)
- [ ] Publicar en AUR (regenerar `sha256sums` con `updpkgsums` y generar `.SRCINFO` antes del push)
- [x] Icono en la barra superior de GNOME (indicador Ayatana): verificado visible junto al resto de iconos con la extensión AppIndicator
- [ ] Detección multi-zona si aparece firmware con `LampCount > 1`
- [ ] Modo "seguir escritorio" (leer acento GTK y aplicarlo) — solo si se pide
- [x] v2.2.0 — comando restore, lanzador GUI por paquete, GUI acabada y empaquetado al día
- [x] v2.2.1 — restore systemd `/usr/bin`, udev argv seguro, CLI endurecido, CI MSRV
