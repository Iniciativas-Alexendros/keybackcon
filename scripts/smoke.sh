#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail=0

say() { printf '%s\n' "$*"; }
ok() { say "  ok: $*"; }
bad() { say "  FALLO: $*"; fail=1; }

say "==> keybackcon smoke"
if [ ! -x "${REPO_DIR}/target/release/keybackcon" ]; then
  cargo build --release --manifest-path "${REPO_DIR}/Cargo.toml" >/dev/null
fi

if "${REPO_DIR}/target/release/keybackcon" --version >/dev/null; then
  ok "--version"
else
  bad "--version"
fi

if { "${REPO_DIR}/target/release/keybackcon" --help 2>&1 || true; } | grep -q "brightness"; then
  ok "--help menciona brightness"
else
  bad "--help"
fi

if python3 -m py_compile "${REPO_DIR}/gui/control_panel.py"; then
  ok "GUI compila"
else
  bad "GUI"
fi

if ! command -v desktop-file-validate >/dev/null 2>&1; then
  ok "desktop-file-validate no disponible, omitido"
elif desktop-file-validate "${REPO_DIR}/packaging/desktop/keybackcon.desktop"; then
  ok "desktop válido"
else
  bad "desktop"
fi

if grep -q 'TAG+="uaccess"' "${REPO_DIR}/packaging/udev/70-keybackcon.rules"; then
  ok "udev uaccess"
else
  bad "udev"
fi

if grep -q "ExecStart=%h/.local/bin/keybackcon" "${REPO_DIR}/packaging/systemd/keybackcon.service"; then
  ok "systemd service"
else
  bad "systemd"
fi

if grep -q "keybackcon animation" "${REPO_DIR}/packaging/systemd/keybackcon-animation@.service"; then
  ok "systemd anim"
else
  bad "systemd anim"
fi

if [ -f "${REPO_DIR}/assets/icons/keybackcon.svg" ]; then
  ok "icono"
else
  bad "icono"
fi

if [ "$fail" -ne 0 ]; then say "SMOKE: fallos detectados"; exit 1; fi
say "SMOKE: todo bien"
