#!/usr/bin/env bash
set -euo pipefail
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DST="${HOME}/.local/bin"
UNIT_DST="${HOME}/.config/systemd/user"
DESK_DST="${HOME}/.local/share/applications"
ICON_DST="${HOME}/.local/share/icons/hicolor/scalable/apps"

echo "==> keybackcon: compilar (release)"
cargo build --release --manifest-path "${REPO_DIR}/Cargo.toml"

echo "==> keybackcon: instalar binario en ${BIN_DST}/keybackcon"
mkdir -p "${BIN_DST}"
install -m755 "${REPO_DIR}/target/release/keybackcon" "${BIN_DST}/keybackcon"

echo "==> keybackcon: instalar GUI en ${BIN_DST}/keybackcon-gui"
install -m755 "${REPO_DIR}/gui/control_panel.py" "${BIN_DST}/keybackcon-gui"

echo "==> keybackcon: instalar lanzador + icono"
mkdir -p "${DESK_DST}" "${ICON_DST}"
install -m644 "${REPO_DIR}/packaging/desktop/keybackcon.desktop" "${DESK_DST}/keybackcon.desktop"
install -m644 "${REPO_DIR}/assets/icons/keybackcon.svg" "${ICON_DST}/keybackcon.svg"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${DESK_DST}" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f "${HOME}/.local/share/icons/hicolor" || true
fi

echo "==> keybackcon: instalar unidades de usuario"
mkdir -p "${UNIT_DST}"
install -m644 "${REPO_DIR}/packaging/systemd/keybackcon.service" "${UNIT_DST}/keybackcon.service"
install -m644 "${REPO_DIR}/packaging/systemd/keybackcon-animation@.service" "${UNIT_DST}/keybackcon-animation@.service"
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload || true
  systemctl --user enable keybackcon.service || true
fi

if [ -f /etc/udev/rules.d/70-keybackcon.rules ]; then
  echo "==> keybackcon: regla udev ya presente, nada que hacer"
else
  echo "==> keybackcon: instalar regla udev (pide sudo)"
  sudo install -m644 "${REPO_DIR}/packaging/udev/70-keybackcon.rules" /etc/udev/rules.d/70-keybackcon.rules
  sudo udevadm control --reload
  sudo udevadm trigger --subsystem-match=hidraw || true
fi

echo "==> keybackcon: migrar estado heredado kbd-rgb (si existe)"
for d in "${XDG_STATE_HOME:-${HOME}/.local/state}" "${HOME}/.local/state"; do
  if [ -f "$d/kbd-rgb/state" ] && [ ! -f "$d/keybackcon/state" ]; then
    mkdir -p "$d/keybackcon"
    cp "$d/kbd-rgb/state" "$d/keybackcon/state"
    echo "    migrado $d/kbd-rgb/state -> $d/keybackcon/state"
    break
  fi
done

echo "OK: keybackcon instalado. Prueba con: keybackcon info"
