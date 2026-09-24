# Desarrollo

Checklist ejecutable (en orden):

- [ ] `cargo test -- --test-threads=1` — 27 tests (los de pid usan XDG_RUNTIME_DIR temporal)
- [ ] `cargo clippy --all-targets -- -D warnings`
- [ ] `cargo fmt --check`
- [ ] `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps`
- [ ] `./scripts/smoke.sh` — binario + GUI + packaging
- [ ] `python3 -m py_compile gui/*.py`
- [ ] `./scripts/install.sh` — instala en ~/.local + udev (sudo) + unidades de usuario

## Calidad

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
La versión vive en `Cargo.toml`; el tag `vX.Y.Z` debe coincidir (lo
verifica el workflow de release).

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
