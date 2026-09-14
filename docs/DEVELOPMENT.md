# Desarrollo

```sh
cargo test -- --test-threads=1   # 6 tests (los de pid usan XDG_RUNTIME_DIR temporal)
cargo clippy -- -D warnings
cargo fmt --check
./scripts/smoke.sh               # binario + GUI + packaging
python3 -m py_compile gui/control_panel.py
./scripts/install.sh             # instala en ~/.local + udev (sudo) + unidades de usuario
```

Commits convencionales (`feat:`, `fix:`, `docs:`…). El CHANGELOG se genera
con `git-cliff` (ver `cliff.toml`); no lo edites a mano en releases.
La versión vive en `Cargo.toml`; el tag `vX.Y.Z` debe coincidir (lo
verifica el workflow de release).
