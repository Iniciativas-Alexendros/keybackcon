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

- `lamp.rs` — localiza el hidraw por descriptor (firma `05 59 09 01 A1 01`),
  abre con RW, reportes `get_feature`/`set_feature`, `attrs()` (LampCount),
  `autonomous(on)` (reporte 6), `color(rgb)` (reporte 5, zona única).
- `color.rs` — `Rgb`, 11 predefinidos, `parse_color` (nombre/hex/`#hex`),
  `scale` (brillo por escala RGB: el firmware declara `IntensityLevelCount=1`,
  no hay canal de brillo), `hsv`, `to_hex`.
- `state.rs` — `state_file()` nuevo (`keybackcon/state`) con lectura
  heredada (`kbd-rgb/state`); `load_state` tolerante, `save_state`, `apply`
  (apaga autónomo → color → persiste).
- `animation.rs` — pidfile nuevo + dos rutas heredadas; valida con
  `kill(pid,0)` + `/proc/<pid>/cmdline` (limpia obsoletos/reciclados);
  `stop_animation()` señaliza SIGTERM y espera; `run_animation(mode, fps)`
  relee el estado cada 500 ms para que el brillo siga respondiendo.
- `cli.rs` — comandos `info/set/off/brightness|bright/firmware-effects|auto/
  animation|anim/stop`, `--help/--version`. Todo lo que cambia el color
  detiene primero la animación: una sola escritora, nunca "teclado loco".

## GUI (`gui/control_panel.py`)

Mesa de luz de una columna: hero light-stage (`DrawingArea` con bloom según
`scale(base, pct)`; previsualiza breathe 4 s / rainbow en local), filtros
circulares + tono propio, intensidad con slider y −/+, movimiento
Fijar/Respirar/Arcoíris, estado vivo (pidfile + `info`). Respeta
`gtk-enable-animations`, avisa con `ToastOverlay` y atajos
(Ctrl+1…9, +/−).
