# Keyboard Backlight Controls (`keybackcon`)

[![CI](https://github.com/Iniciativas-Alexendros/keybackcon/actions/workflows/ci.yml/badge.svg)](https://github.com/Iniciativas-Alexendros/keybackcon/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Iniciativas-Alexendros/keybackcon)](https://github.com/Iniciativas-Alexendros/keybackcon/releases)
![Rust](https://img.shields.io/badge/rust-sin%20dependencias-orange)
![GTK4](https://img.shields.io/badge/GUI-GTK4%20%2B%20Adwaita-blue)
![License](https://img.shields.io/badge/licencia-MIT-green)

Fija la luz de tu teclado **AERO X16** en dos toques: elige color, ajusta
intensidad y listo. CLI en Rust sin dependencias (habla HID LampArray
directo) + mesa de luz GTK4 con vista previa fiel.

## Instalación

```sh
./scripts/install.sh
# instala keybackcon + keybackcon-gui en ~/.local/bin,
# regla udev (pide sudo una vez), unidades de usuario y lanzador
```

Sin script:

```sh
cargo build --release
install -m755 target/release/keybackcon ~/.local/bin/keybackcon
install -m755 gui/control_panel.py ~/.local/bin/keybackcon-gui
sudo install -m644 packaging/udev/70-keybackcon.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger --subsystem-match=hidraw
```

Descarga directa: cada [release](https://github.com/Iniciativas-Alexendros/keybackcon/releases)
trae `keybackcon-vX.Y.Z-linux-x86_64.tar.gz` con binario, GUI y packaging.

## Uso

```sh
keybackcon info                    # dispositivo, nº de lámparas, estado
keybackcon set ff7800              # hex, #hex o predefinido (red green blue cyan magenta yellow orange purple pink white off)
keybackcon brightness 60           # o +10 / -10  (alias: bright)
keybackcon off                     # apaga (conserva tu color)
keybackcon firmware-effects off    # cede el control al programa (alias: auto)
keybackcon animation breathe       # o rainbow, --fps N  (alias: anim)
keybackcon stop                    # para y restaura tu color
keybackcon-gui                     # mesa de luz gráfica
```

Atajos de la GUI: `Ctrl+1…9` cambia de filtro, `+`/`−` ajusta intensidad.

## Cómo funciona

- USB HID LampArray (Usage Page `0x59`), una zona (`LampCount=1`).
- El firmware no trae canal de brillo: `brightness` escala tu RGB y lo
  guarda (`~/.local/state/keybackcon/state`). Detalles en
  [`docs/PROTOCOL.md`](docs/PROTOCOL.md).
- Una sola animación a la vez (pidfile validado en
  `$XDG_RUNTIME_DIR/keybackcon/animation.pid`); cualquier `set/off/
  brightness` la detiene primero para que el teclado nunca se vuelva loco.
- Si vienes de `kbd-rgb`, tu color y brillo migran solos. Ver
  [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) y
  [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Problemas típicos

| Síntoma | Qué hacer |
|---|---|
| `no se encontró el dispositivo LampArray` | Revisa que el teclado esté conectado y la regla udev: `ls /dev/hidraw*`, `keybackcon info` |
| Permiso denegado en `/dev/hidraw*` | Reaplica udev (`sudo udevadm trigger`) y **vuelve a iniciar sesión** (uaccess) |
| La animación no para | `keybackcon stop`; si persiste, `systemctl --user stop 'keybackcon-animation@*'` |
| La GUI no encuentra el binario | `~/.local/bin` debe estar en tu `PATH` |

## Desarrollo

```sh
cargo test -- --test-threads=1
cargo clippy -- -D warnings
cargo fmt --check
./scripts/smoke.sh
```

Versión en `Cargo.toml`, tags `vX.Y.Z`, changelog con `git-cliff`.
Más en [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

Licencia MIT — ver [`LICENSE`](LICENSE).
