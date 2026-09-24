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

### `protocol.rs` — fuente única del protocolo en el cable

Firma del descriptor `05 59 09 01 A1 01` y subruta sysfs
`device/report_descriptor`, IDs 1/5/6, longitudes 23/10 (mínimo aceptado
19), offsets de `LampCount` (u16 LE, 1–2) y `LampArrayKind` (u32 LE, 15–18),
bytes de autónomo e intensidad `0xff`, `hid_ioctl_request`
(`HIDIOCGFEATURE`/`HIDIOCSFEATURE`, tipo `'H'` `0x48`, dirección
`0xC000_0000`; rechaza longitud 0 o > `0x3FFF` = 16383, el máximo de los
14 bits de tamaño de `_IOC`) y los constructores/parser
de informes (`parse_attrs`, `color_report`, `autonomous_report`).
Ver especificación en [`PROTOCOL.md`](PROTOCOL.md).

### `lamp.rs` — localización y transporte HID

Localiza el hidraw por la firma y la subruta de `protocol.rs`, abre con RW.
El transporte vive tras el rasgo `HidTransport` (`HidRaw` es el único sitio
con ioctl FFI), así los informes se construyen y parsean sin hardware; los
errores nombran operación y ruta. `attrs()` (LampCount), `autonomous(on)`
(reporte 6), `color(rgb)` (reporte 5, zona única) e `is_device_gone`
(ENODEV/ENXIO/ENOENT → desconexión) consumen `protocol.rs`.

### `color.rs` — color y brillo

`Rgb`, 11 predefinidos, `parse_color` (nombre/hex/`#hex`, error tipado
`ColorError` con el mensaje intacto), `scale` (brillo por escala RGB: el
firmware declara `IntensityLevelCount=1`, no hay canal de brillo), `hsv`,
`to_hex`.

### `state.rs` — estado persistente

`state_file()` nuevo (`keybackcon/state`) con lectura heredada
(`kbd-rgb/state`); `load_state` tolerante, `save_state` atómica
(fichero temporal + `rename`, avisa en stderr si falla), `apply` (apaga
autónomo → color → persiste).

### `animation.rs` — animación exclusiva y parada limpia

Pidfile nuevo + dos rutas heredadas; valida con `kill(pid,0)`, el estado
`/proc/<pid>/stat` (los zombies cuentan como muertos: su cmdline queda vacío
pero su pid no reciclable identifica al escritor) y `/proc/<pid>/cmdline`
(limpia obsoletos/reciclados). `run_animation` señala primero la animación
anterior, instala SIGINT/SIGTERM y reserva el pidfile en exclusiva con
`create_new` *antes* de abrir el dispositivo: un fallo de claim no deja el
teclado sin modo autónomo ni con dos escritores. Si existe, re-valida la
animación viva o reclama el obsoleto (3 intentos). Los signos solo marcan un
`AtomicBool`; el bucle relee el estado cada 500 ms y `fps` se acota a
1–`MAX_FPS` (60); al parar restaura el color base y borra su pidfile solo si
sigue siendo suyo. Si el teclado se desconecta limpia y sale con "el teclado
parece haberse desconectado". `stop_animation()` señaliza SIGTERM y espera
(≤1 s): un zombie sin reaped devuelve `true` al instante (para que `stop`
restaure el color) y si el peer sobrevive al timeout se conserva su pidfile
en vez de arriesgar dos escritores.

### `cli.rs` — comandos y despacho

Modelo estructurado de comandos (`Command`, `Mode`, `BrightnessChange`) con
parser manual sin dependencias: `parse(&[String])` valida y `run()` despacha
a `cmd_info/cmd_set/cmd_off/cmd_brightness/cmd_firmware_effects/
cmd_animation/cmd_stop/cmd_restore`; `usage()` conserva texto y `exit 2`.
Comandos `info [--json]/set/off/brightness|bright/firmware-effects|auto/
animation|anim/stop/restore`, `--help/--version`. `info --json` imprime una
línea `{"version","device","lamps","kind","state","brightness"}` estable para
la GUI (el formato humano no es API). El parser rechaza argumentos extra y
`--fps` no numérico. Todo lo que cambia el color detiene primero la
animación: una sola escritora, nunca "teclado loco".

### `error.rs` — errores del CLI

`Error { Usage, Invalid(String), Io(io::Error) }` con `Display` +
`std::error::Error` + `From<io::Error>`: `Usage` termina en `usage()`
(exit 2) y el resto en `{BIN}: {e}` (exit 1).

## GUI (`gui/`)

Mesa de luz de una columna: hero light-stage (`DrawingArea` con bloom según
`scale(base, pct)`; previsualiza breathe 4 s / rainbow en local con
matemática duplicada respecto a `animation.rs`, ver ADR 9 en
[`DECISIONS.md`](DECISIONS.md)), filtros circulares + tono propio, intensidad
con slider continuo 0–100, movimiento Fijar/Respirar/Arcoíris, estado vivo
(pidfile + `info --json`, leído una vez y cacheado). El estado se sigue con
`Gio.FileMonitor` sobre el state file (nunca un subproceso por segundo);
las operaciones con diálogos (udev/pkexec) corren en hilos worker con
`GLib.idle_add`. Habla con el hardware solo vía subproceso al CLI.

La bandeja (`--tray`) es un proceso aparte (GTK3 + AyatanaAppIndicator3, por
incompatible con GTK4): menú con slider de brillo, predefinidos de color,
submenú de animaciones con modo activo marcado, Restaurar/Preferencias/Acerca
de/Salir; sincroniza su estado leyendo state/pidfile cada 2 s y lanza la
ventana como subproceso trackeado que mata y reaped al salir. El cierre es
limpio (sin `os._exit`), así `client.stop()` siempre se ejecuta.

## Flujos

| Flujo | Pasos |
|---|---|
| `set` / `off` / `brightness` | Detiene animación → autónomo off → emite color → persiste estado |
| `animation` | Detiene la anterior → reserva pidfile (`create_new`, 3 intentos) → abre dispositivo → bucle (relee estado cada 500 ms) → al parar restaura base y borra su pidfile |
| `stop` | Señaliza SIGTERM a la animación viva y espera (≤1 s); un zombie cuenta como "había animación" para restaurar el color; si el peer sobrevive, conserva el pidfile |
| `restore` | Lee estado guardado → `apply` (autónomo off → color) |
| GUI (vista previa y estado) | Invoca al CLI por subproceso + lee state/pidfile (nunca toca hidraw) |
