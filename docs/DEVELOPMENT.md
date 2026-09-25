# Desarrollo

Checklist ejecutable (en orden):

- [ ] `cargo test -- --test-threads=1` — 33 tests (los de pid usan XDG_RUNTIME_DIR temporal)
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] `cargo fmt --check`
- [ ] `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps`
- [ ] `python3 -m unittest discover -s gui/tests` — 47 tests de la GUI (sin display ni hardware)
- [ ] `./scripts/smoke.sh` — binario + GUI + packaging + tests unitarios
- [ ] `python3 -m py_compile gui/*.py`
- [ ] `./scripts/install.sh` — instala en ~/.local + udev (sudo) + unidades de usuario

Validación sobre el hardware real (teclado AERO X16 conectado; captura antes
el estado con `keybackcon info --json` y restaúralo al terminar con
`keybackcon set <hex> && keybackcon brightness <pct>`):

- [ ] `keybackcon info` y `keybackcon info --json` detectan el dispositivo
- [ ] `set` con hex y con nombre de predefinido; `brightness` con valores
      límite (0, 1, 99, 100) y relativos (`+5`, `-5`)
- [ ] `off` apaga y `restore` reaplica color y brillo guardados
- [ ] `animation breathe --fps 30` arranca; `stop` tarda < 0,2 s y restaura
- [ ] `animation rainbow` en segundo plano + `stop` (idempotente: un segundo
      `stop` responde "no hay ninguna animación en marcha")
- [ ] `systemctl --user start/stop keybackcon-animation@breathe` anima y
      restaura al parar (ExecStopPost = `keybackcon stop`)
- [ ] `firmware-effects on`/`off` y volver al color guardado

## Calidad

- **Tests de la GUI** (`gui/tests/`, `unittest` de stdlib): `python3 -m
  unittest discover -s gui/tests`. Cubren `client` (con un binario fake en un
  directorio ejecutable — ojo: algunos `/tmp` son `noexec`), `colors`,
  `theme` (vía archivo, con GSettings aislado), `i18n`, `compat` (detección
  de distro con `/etc/os-release` emulado) y los helpers de la bandeja. Los
  tests de bandeja hacen skip si Gtk3/Ayatana faltan o si Gtk4 ya está
  cargado en el proceso (incompatibilidad GTK3/GTK4 documentada); en ese
  caso corren aislados: `python3 -m unittest gui.tests.test_tray_helpers`.
- **Lints**: `Cargo.toml` activa `missing_docs` y el grupo
  `clippy::pedantic`; deben quedar limpios con
  `cargo clippy --all-targets -- -D warnings` (incluidos ejemplos y tests)
  y sin warnings de rustc. Los pocos `#[allow]` puntuales (matemática HSV,
  casts acotados de la animación y despacho del CLI) existen donde un cambio
  de tipos alteraría el comportamiento.
- **Rustdoc**: `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps` valida los
  `//!` de módulo y los `///` de los elementos públicos. Los mensajes de cara
  al usuario están en español a propósito (identidad del proyecto, no i18n).
- **Benchmarks**: `cargo run --release --example bench_colors` imprime una
  tabla de ns/op de `parse_color`, `scale`, `hsv`, `to_hex` y los
  constructores de informes, usando solo `std::time::Instant` y
  `std::hint::black_box` (sin `criterion`, ver ADR 10 en
  [`DECISIONS.md`](DECISIONS.md)).
- **Property tests**: `src/color.rs` y `src/protocol.rs` incluyen pruebas
  pseudoaleatorias deterministas con un xorshift64 de semilla fija (sin
  `proptest`, ver ADR 10); corren con el resto de `cargo test`.

Commits convencionales (`feat:`, `fix:`, `docs:`…). El CHANGELOG se genera
con `git-cliff` (ver `cliff.toml`); no lo edites a mano en releases.
La versión canónica vive en `Cargo.toml` y está espejada en
`gui/__init__.py` (`__version__`) y `packaging/aur/PKGBUILD` (`pkgver`); el
workflow `.github/workflows/version.yml` las sincroniza automáticamente en
cada push a `main`: calcula el bump con `git-cliff --bumped-version` desde
los commits convencionales desde el último tag y, si hay bump, actualiza las
tres fuentes, regenera `CHANGELOG.md` y crea el commit `chore(release)` y el
tag `vX.Y.Z` (que dispara `release.yml`). El workflow de release verifica que
el tag coincida con las tres fuentes.

## Empaquetado y release

- **Debian/Ubuntu (`.deb`)**: `cargo install cargo-deb --locked && cargo deb`
  produce `target/debian/keybackcon_<versión>-1_amd64.deb` a partir de
  `[package.metadata.deb]` en `Cargo.toml`. Los scripts `postinst`/`prerm`
  viven en `packaging/debian/` y recargan udev/systemd; se instala con
  `sudo apt install ./keybackcon_*.deb`.
- **Arch Linux (AUR)**: `packaging/aur/PKGBUILD` compila con
  `cargo build --release --locked` e instala binario, GUI, lanzador, icono,
  regla udev, unidades de usuario y licencia. Antes de publicar hay que
  rellenar el mantenedor, calcular `sha256sums` (`updpkgsums`) y regenerar
  `.SRCINFO` (`makepkg --printsrcinfo`); ver `packaging/aur/README.md`.
- **GitHub Releases**: al empujar un tag `vX.Y.Z`,
  `.github/workflows/release.yml` publica el tarball
  `keybackcon-vX.Y.Z-linux-x86_64.tar.gz`, el `.deb`, un SBOM CycloneDX
  (`cargo-cyclonedx`), `SHA256SUMS` y una attestation de procedencia
  (`actions/attest-build-provenance`).
- **npm**: `.github/workflows/npm.yml` compila x86_64 y arm64 y publica el
  meta-paquete `keybackcon` (lanzador + postinstalador de regla udev y
  unidades systemd de usuario) junto a los paquetes de binario por
  plataforma `@keybackcon/linux-x64` y `@keybackcon/linux-arm64`. Las fuentes
  viven en `npm/`; el binario se copia en `npm/platforms/*/bin/` solo en CI
  (ignorado por git). Requiere el secret `NPM_TOKEN`. Prueba local con
  `npm pack` en `npm/` y en `npm/platforms/linux-x64/`.
