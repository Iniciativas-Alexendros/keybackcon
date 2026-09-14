# Decisiones (ADR breves)

## 1. Nombre: `keybackcon` / "Keyboard Backlight Controls"
Un solo nombre corto para binario, repo y App ID (`org.iniciativas.keybackcon`);
el nombre largo solo en display/docs/ventana. Rutas nuevas
(`keybackcon/state`, `keybackcon/animation.pid`) con lectura heredada de
`kbd-rgb/*`. Motivo: fin del baile de nombres, migración sin romper a nadie.

## 2. Cargo con cero dependencias
Estructura `src/` por módulos + `cargo test/clippy/fmt` en CI. Motivo:
compilación reproducible y binario estático pequeño; el ioctl cabe en
unas líneas sin crates.

## 3. Instancia única vía pidfile validado
`animation` escribe su pid; antes de señalizar se valida con `kill(pid,0)`
y `/proc/<pid>/cmdline` conteniendo `keybackcon` o `kbd-rgb`. La reserva es
atómica (`create_new`, sin truncar): si el pidfile ya existe se re-valida
—vivo → "ya hay una animación en marcha (pid N)", obsoleto → se reclama en
≤3 intentos—. Motivo: evita matar procesos reciclados y el "teclado loco"
(dos escritores).

## 4. Brillo por escala RGB persistente
Sin canal de brillo en el firmware, el porcentaje escala el color base y
se persiste junto al color. Motivo: `brightness` sobrevive a reinicios y a
`stop`, y la animación lo relee cada 500 ms.

## 5. GUI: mesa de luz con light-stage
Una columna, hero con vista previa fiel (`scale(base,pct)`, breathe 4 s,
rainbow), sin numeración decorativa. Motivo: el trabajo es "fijar luz en
<2 s"; la vista previa elimina el prueba-error contra el hardware.

## 6. Transporte HID abstracto y parada limpia
`lamp.rs` separa el rasgo `HidTransport` de `HidRaw` (único FFI ioctl) para
probar construcción/parseo de informes sin hardware; la petición ioctl
codifica la longitud real del buffer. `animation` captura SIGTERM/SIGINT con
`signal()` y solo escribe un `AtomicBool` async-signal-safe, restaura el color
base al parar y, si el teclado se desconecta, borra su pidfile y sale con
error. Motivo: ciclo de vida determinista y auditable sin crates.

## 7. CLI estructurada sin dependencias
`cli.rs` modela los comandos como un `enum Command` (`Help`, `Version`,
`Info`, `Set`, `Off`, `Brightness`, `FirmwareEffects`, `Animation`, `Stop`)
poblado por un `parse(&[String])` manual, y cada comando tiene su `cmd_*`.
Los fallos viajan como `error::Error { Usage, Invalid, Io }` (`Display` +
`std::error::Error` + `From<io::Error>`) y `color::ColorError` conserva el
mensaje del color. Motivo: mantener la identidad de cero dependencias
(ADR 2) que `clap`/`thiserror` romperían, con el mismo texto en español y los
mismos códigos de salida (2 uso, 1 error).

## 8. Protocolo centralizado en `src/protocol.rs`
Los bytes del cable (firma `05 59 09 01 A1 01`, IDs 1/5/6, longitudes 23/10
y mínimo 19, offsets de `LampCount` 1–2 y `LampArrayKind` 15–18, bytes de
autónomo e intensidad `0xff`, codificación `HIDIOCGFEATURE`/
`HIDIOCSFEATURE`) junto con sus constructores (`color_report`,
`autonomous_report`), parser (`parse_attrs`) y el constructor ioctl validado
(`hid_ioctl_request`, rechaza 0 o > `u16::MAX`) viven en `protocol.rs`;
`lamp.rs` solo los consume. Motivo: un cambio de protocolo toca un único
archivo, los tests de bytes exactos quedan junto a las constantes y
desaparecen los literales mágicos duplicados en el transporte.

## 9. GUI por subproceso, sin FFI (cdylib aplazada)
`gui/control_panel.py` sigue hablando con el CLI por subproceso
  (`set`/`brightness`/`animation`/`stop`) y leyendo state/pidfile para la
  vista previa; no se toca. Se descarta por ahora exponer el CLI como cdylib
  con FFI. Motivo: mantiene la identidad de cero dependencias (ADR 2) y una
  única fuente de verdad; el CLI sigue siendo el único dueño del hardware
  (ADR 3) y no aparecen dos escritores; el GUI ya maneja timeouts y diálogos de
  error sobre texto estable; y no se añade superficie FFI/ABI frágil que
  compilar y versionar sin ganancia funcional. Trade-off aceptado: la
  matemática de vista previa (`scale`, HSV, breathe) está duplicada en Rust y
  Python; se asume para no arrastrar GTK/Python al binario y queda documentado
  en este ADR y en `docs/ARCHITECTURE.md`. La decoupling cdylib/FFI queda
  deliberadamente aplazada (sin fecha) hasta que la duplicación cause
  divergencias reales.

## 10. Rustdoc, pedantic y benchmarks/property tests sin dependencias
El crate documenta con `//!`/`///` bajo `missing_docs`, activa
`clippy::pedantic` con `#[allow]` puntuales donde un cambio de tipos alteraría
la aritmética (HSV, casts acotados de la animación) o el despacho del CLI, mide
con `examples/bench_colors.rs` (`std::time::Instant` + `std::hint::black_box`)
en lugar de `criterion`, y cubre invariantes con un xorshift64 determinista de
semilla fija en los módulos de test en lugar de `proptest`. El ejemplo incluye
los módulos con `#[path]` (con `#![allow(dead_code)]`) porque el paquete
publica un binario, no una `lib`. Motivo: mantener la identidad de cero
dependencias (ADR 2) sin renunciar a calidad medible; `criterion` y `proptest`
arrastrarían árboles de dependencias desproporcionados para unas pocas
operaciones puras. Trade-off aceptado: los benchmarks dan tiempo medio (no
percentiles) y las property tests usan un generador propio de 64 bits;
suficiente para las invariantes actuales y reproducible en CI.

## 11. Cota `HID_IOCTL_MAX_LEN` en el ioctl
`hid_ioctl_request` rechaza 0 y `>0x3FFF` (`HID_IOCTL_MAX_LEN`): el campo size solo
tiene 14 bits (`_IOC_SIZEBITS`, `include/uapi/asm-generic/ioctl.h`); antes aceptaba
hasta `u16::MAX` truncando con `& 0x3fff`. Motivo: fallar en construcción en vez de
pedir al kernel otra longitud; 1/10/23 codifican idéntico.
