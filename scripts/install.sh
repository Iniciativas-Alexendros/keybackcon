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
GUI_DST="${HOME}/.local/share/keybackcon/gui"
mkdir -p "${GUI_DST}"
install -m644 "${REPO_DIR}"/gui/*.py "${GUI_DST}/"
install -m755 "${REPO_DIR}/packaging/keybackcon-gui" "${BIN_DST}/keybackcon-gui"

echo "==> keybackcon: compilar traducciones (es)"
MO_SRC="${REPO_DIR}/po/es.po"
MO_BUILD="${REPO_DIR}/gui/locale/es/LC_MESSAGES/keybackcon.mo"
MO_DST="${HOME}/.local/share/locale/es/LC_MESSAGES/keybackcon.mo"
if command -v msgfmt >/dev/null 2>&1; then
  mkdir -p "$(dirname "${MO_BUILD}")"
  msgfmt -o "${MO_BUILD}" "${MO_SRC}"
  echo "    .mo generado en ${MO_BUILD}"
else
  echo "    aviso: msgfmt no disponible, se omite la compilación del .mo (la GUI usará el idioma por defecto)" >&2
fi
if [ -f "${MO_BUILD}" ]; then
  mkdir -p "$(dirname "${MO_DST}")"
  install -m644 "${MO_BUILD}" "${MO_DST}"
  echo "    locale instalado en ${MO_DST}"
else
  echo "    aviso: sin .mo compilado, se omite la instalación del locale" >&2
fi

echo "==> keybackcon: instalar schema GSettings"
SCHEMA_SRC="${REPO_DIR}/gui/org.iniciativas.keybackcon.gschema.xml"
SCHEMA_DST_DIR="${HOME}/.local/share/glib-2.0/schemas"
mkdir -p "${SCHEMA_DST_DIR}"
install -m644 "${SCHEMA_SRC}" "${SCHEMA_DST_DIR}/org.iniciativas.keybackcon.gschema.xml"
if command -v glib-compile-schemas >/dev/null 2>&1; then
  glib-compile-schemas "${SCHEMA_DST_DIR}" || true
else
  echo "    aviso: glib-compile-schemas no disponible, se omite la compilación de schemas" >&2
fi
# Nota: sin autostart global. El autostart es opt-in desde el diálogo de
# preferencias (gui/settings.py), que crea ~/.config/autostart/keybackcon-tray.desktop bajo demanda.

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

if [ "${KEYBACKCON_SKIP_UDEV:-0}" = "1" ]; then
  echo "==> keybackcon: regla udev omitida (KEYBACKCON_SKIP_UDEV=1)"
elif [ -f /etc/udev/rules.d/70-keybackcon.rules ]; then
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
