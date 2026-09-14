# Hoja de ruta

- [x] v2.0.0 — Cargo por módulos, GUI mesa de luz, packaging, CI/release
- [x] v2.1.0 — auditoría integral: robustez HID, CLI estructurada sin dependencias, protocolo centralizado, calidad (rustdoc, pedantic, 24 tests) y empaquetado .deb/AUR preparado
- [ ] Probar en hardware AERO X16 cada comando + animaciones a 60 fps
- [x] Empaquetado en repo: metadata `cargo-deb`, `PKGBUILD` de AUR y release con `.deb` + SBOM + attestation
- [ ] Publicar `.deb` en GitHub Releases (el workflow ya lo construye al empujar el tag)
- [ ] Publicar en AUR (regenerar `sha256sums` con `updpkgsums` y generar `.SRCINFO` antes del push)
- [ ] Detección multi-zona si aparece firmware con `LampCount > 1`
- [ ] Modo "seguir escritorio" (leer acento GTK y aplicarlo) — solo si se pide
