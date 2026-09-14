# Protocolo

USB HID Usage Tables v1.4, §26 "Lighting And Illumination Page"
(Usage Page `0x59`). Sin ingeniería inversa: el firmware expone un
LampArray estándar. La fuente única de los valores concretos (firma, IDs,
longitudes, offsets, bytes y codificación ioctl) en el código es
`src/protocol.rs`; `src/lamp.rs` solo consume sus constantes, parser y
constructores de informes.

- Firma de detección: el descriptor contiene `05 59 09 01 A1 01`
  (Usage Page LampArray, Usage LampArray, Collection Application).
- `get_feature(1, 23)` → atributos: `LampCount` en bytes 1–2 (aquí: 1),
  `LampArrayKind` en bytes 15–18 (el firmware declara un valor engañoso;
  se muestra tal cual con el aviso).
- `set_feature([5, 1, first_lo, first_hi, last_lo, last_hi, r, g, b, 0xff])`
  → color de la zona `first..=last` (aquí `0..=count-1`, una sola zona).
- `set_feature([6, on])` → efectos autónomos del firmware on/off.

## Por qué el brillo escala el RGB

El dispositivo declara `IntensityLevelCount=1`: no hay canal de brillo
separable. `brightness N` guarda un porcentaje 0–100 y reemite
`scale(base, pct)` con redondeo (`(v*pct+50)/100`). El estado persiste
como `"<hex> <pct>"`, p. ej. `ff7800 60`.
