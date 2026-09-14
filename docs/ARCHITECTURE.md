# Arquitectura

`keybackcon` habla directamente con el teclado vía hidraw, sin demonios ni dependencias.

```
┌──────────────┐   ioctl HIDIOCGFEATURE / HIDIOCSFEATURE   ┌────────────┐
│ keybackcon   │  ──────────────────────────────────────▶  │ /dev/hidrawN│
│ (Rust, 0 deps)│   LampArray, Usage Page 0x59, reportes    │ AERO X16    │
└──────────────┘   1/5/6: atributos, color, autónomo       └────────────┘
       │ state: ~/.local/state/keybackcon/state  ("ff7800 60")
       │ pidfile: $XDG_RUNTIME_DIR/keybackcon/animation.pid
       ▼
┌──────────────┐   subprocess: set / brightness / animation / stop
│ control_panel│   + lectura de state/pidfile para vista previa y estado
│ (GTK4/Adwaita)│
└──────────────┘
```

## Módulos del CLI (`src/`)

- `protocol.rs` — fuente única del protocolo LampArray en el cable (USB HID
  Usage Tables v1.4 §26; codificación ioctl de `include/uapi/linux/hidraw.h`):
  firma del descriptor `05 59 09 01 A1 01` y subruta sysfs
  `device/report_descriptor`, IDs 1/5/6, longitudes 23/10 (mínimo aceptado
  19), offsets de `LampCount` (u16 LE, 1–2) y `LampArrayKind` (u32 LE, 15–18),
  bytes de autónomo e intensidad `0xff`, `hid_ioctl_request`
  (`HIDIOCGFEATURE`/`HIDIOCSFEATURE`, tipo `'H'` `0x48`, dirección
  `0xC000_0000`; rechaza longitud 0 o > `u16::MAX`) y los constructores/parser
  de informes (`parse_attrs`, `color_report`, `autonomous_report`).
- `lamp.rs` — localiza el hidraw por la firma y la subruta de `protocol.rs`,
  abre con RW. El transporte vive tras el rasgo `HidTransport` (`HidRaw` es el
  único sitio con ioctl FFI), así los informes se construyen y parsean sin
  hardware; los errores nombran operación y ruta. `attrs()` (LampCount),
  `autonomous(on)` (reporte 6), `color(rgb)` (reporte 5, zona única) e
  `is_device_gone` (ENODEV/ENXIO/ENOENT → desconexión) consumen
  `protocol.rs`.
- `color.rs` — `Rgb`, 11 predefinidos, `parse_color` (nombre/hex/`#hex`,
  error tipado `ColorError` con el mensaje intacto), `scale` (brillo por
  escala RGB: el firmware declara `IntensityLevelCount=1`, no hay canal de
  brillo), `hsv`, `to_hex`.
- `state.rs` — `state_file()` nuevo (`keybackcon/state`) con lectura
  heredada (`kbd-rgb/state`); `load_state` tolerante, `save_state`, `apply`
  (apaga autónomo → color → persiste).
- `animation.rs` — pidfile nuevo + dos rutas heredadas; valida con
  `kill(pid,0)` + `/proc/<pid>/cmdline` (limpia obsoletos/reciclados).
  `run_animation` reserva el pidfile en exclusiva con `create_new` (no
  trunca): si existe, re-valida la animación viva o reclama el obsoleto
  (3 intentos). SIGTERM/SIGINT se capturan con `signal()` y solo marcan un
  `AtomicBool`; el bucle relee el estado cada 500 ms, y al parar restaura el
  color base y borra su pidfile solo si sigue siendo suyo. Si el teclado se
  desconecta limpia y sale con "el teclado parece haberse desconectado".
  `stop_animation()` señaliza SIGTERM y espera (≤1 s).
- `cli.rs` — modelo estructurado de comandos (`Command`, `Mode`,
  `BrightnessChange`) con parser manual sin dependencias: `parse(&[String])`
  valida y `run()` despacha a `cmd_info/cmd_set/cmd_off/cmd_brightness/
  cmd_firmware_effects/cmd_animation/cmd_stop`; `usage()` conserva texto y
  `exit 2`. Comandos `info/set/off/brightness|bright/firmware-effects|auto/
  animation|anim/stop`, `--help/--version`. Todo lo que cambia el color
  detiene primero la animación: una sola escritora, nunca "teclado loco".
- `error.rs` — `Error { Usage, Invalid(String), Io(io::Error) }` con
  `Display` + `std::error::Error` + `From<io::Error>`: `Usage` termina en
  `usage()` (exit 2) y el resto en `{BIN}: {e}` (exit 1).

## GUI (`gui/control_panel.py`)

Mesa de luz de una columna: hero light-stage (`DrawingArea` con bloom según
`scale(base, pct)`; previsualiza breathe 4 s / rainbow en local con
matemática duplicada respecto a `animation.rs`, ver ADR 9), filtros
circulares + tono propio, intensidad con slider y −/+, movimiento
Fijar/Respirar/Arcoíris, estado vivo (pidfile + `info`). Respeta
`gtk-enable-animations`, avisa con `ToastOverlay` y atajos
(Ctrl+1…9, +/−).
