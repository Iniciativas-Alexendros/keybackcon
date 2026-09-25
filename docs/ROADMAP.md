# Hoja de ruta

Próximos objetivos, ordenados por horizonte. Un objetivo solo entra aquí
cuando está listo para trabajar (criterio claro) o bloqueado (se indica por
qué). Los hitos ya logrados van al final como histórico.

## En curso — v2.3.0

Rediseño de la ventana (Adwaita) y la bandeja, `info --json`, parada de
animación sin bloqueos, distribución npm y autoversionado con git-cliff.
**Pendiente solo el push a `main`**: al llegar, `version.yml` genera el tag
v2.3.0, `release.yml` publica .deb/tarball/SBOM y `npm.yml` publica el
paquete npm (requiere el secret `NPM_TOKEN` configurado en el repo).

## Corto plazo

- [ ] **Publicar en AUR** — el `PKGBUILD` está listo; falta rellenar
      `sha256sums` reales (`updpkgsums`), generar `.SRCINFO`
      (`makepkg --printsrcinfo`) y subir con cuenta AUR. Bloqueado: cuenta.
- [ ] **Primer release npm real** — `npm install -g keybackcon` de prueba en
      una máquina limpia (Debian y Arch) validando el postinstalador.
      Bloqueado: `NPM_TOKEN` en GitHub Secrets.
- [ ] **CI: tests de la GUI** — la suite `gui/tests` ya corre en el job
      `gui-packaging`; añadir cobertura de `main.py` (D-Bus de control) con
      un bus de sesión de prueba si se ve útil.

## Medio plazo

- [ ] **RPM (spec + COPR)** o **Flatpak** — Flatpak queda limitado porque la
      regla udev necesita un paso manual fuera del sandbox; si se hace, hay
      que documentarlo. Decisión pendiente según demanda.
- [ ] **i18n real** — hoy los msgids son español con traducción identidad.
      Migrar msgids a inglés y tener `es.po`/`en.po` completos (decisión:
      migración completa vs. añadir `en.po` con msgids españoles).
- [ ] **Más teclados** — hacer configurables la firma del descriptor HID y
      la regla udev (VID/PID) vía variable de entorno o flag, si aparece
      demanda de otros modelos LampArray.

## Largo plazo / condicionado

- [ ] **Multi-zona** — solo si aparece firmware con `LampCount > 1`; el
      protocolo y la GUI ya separan "zona(s)" en la ficha del dispositivo.
- [ ] **Modo "seguir el escritorio"** — leer el color de acento del sistema
      y ofrecerlo como filtro. Solo si se pide (ver ADR pendiente).
- [ ] **Autostart vía unidad systemd del usuario** para la bandeja en vez
      del `.desktop` XDG, si se confirma que mejora el arranque en GNOME.

## Histórico

- [x] v2.0.0 — Cargo por módulos, GUI mesa de luz, packaging, CI/release
- [x] v2.1.0 — auditoría integral: robustez HID, CLI estructurada sin dependencias, protocolo centralizado, calidad y empaquetado .deb/AUR preparado
- [x] v2.2.0 — comando restore, lanzador GUI por paquete, GUI acabada y empaquetado al día
- [x] v2.2.1 — restore systemd `/usr/bin`, udev argv seguro, CLI endurecido, CI MSRV
- [x] v2.3.0 (código) — parada sin bloqueos (zombies), estado atómico, validación estricta, `info --json`, cap de FPS, semántica de stop unificada, bandeja rediseñada, ventana Adwaita con apertura instantánea desde la bandeja (control D-Bus), autoversionado git-cliff, publicación npm, tests unitarios de la GUI (47) y compatibilidad multi-distribución
