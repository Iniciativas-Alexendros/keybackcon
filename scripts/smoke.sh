#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

say() { printf '%s\n' "$*"; }
ok() { say "  ok: $*"; }
bad() { say "  FALLO: $*"; fail=1; }

say "==> keybackcon smoke"
[ -x "${REPO_DIR}/target/release/keybackcon" ] || cargo build --release --manifest-path "${REPO_DIR}/Cargo.toml" >/dev/null

"${REPO_DIR}/target/release/keybackcon" --version >/dev/null && ok "--version" || bad "--version"
{ "${REPO_DIR}/target/release/keybackcon" --help 2>&1 || true; } | grep -q "brightness" && ok "--help menciona brightness" || bad "--help"
python3 -m py_compile "${REPO_DIR}/gui/control_panel.py" && ok "GUI compila" || bad "GUI"
command -v desktop-file-validate >/dev/null 2>&1 \
  && (desktop-file-validate "${REPO_DIR}/packaging/desktop/keybackcon.desktop" && ok "desktop válido" || bad "desktop") \
  || ok "desktop-file-validate no disponible, omitido"
grep -q 'TAG+="uaccess"' "${REPO_DIR}/packaging/udev/70-keybackcon.rules" && ok "udev uaccess" || bad "udev"
grep -q "ExecStart=%h/.local/bin/keybackcon" "${REPO_DIR}/packaging/systemd/keybackcon.service" && ok "systemd service" || bad "systemd"
grep -q "keybackcon animation" "${REPO_DIR}/packaging/systemd/keybackcon-animation@.service" && ok "systemd anim" || bad "systemd anim"
[ -f "${REPO_DIR}/assets/icons/keybackcon.svg" ] && ok "icono" || bad "icono"

if [ "$fail" -ne 0 ]; then say "SMOKE: fallos detectados"; exit 1; fi
say "SMOKE: todo bien"
