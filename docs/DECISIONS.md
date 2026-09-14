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
y `/proc/<pid>/cmdline` conteniendo `keybackcon` o `kbd-rgb`. Motivo:
evita matar procesos reciclados y el "teclado loco" (dos escritores).

## 4. Brillo por escala RGB persistente
Sin canal de brillo en el firmware, el porcentaje escala el color base y
se persiste junto al color. Motivo: `brightness` sobrevive a reinicios y a
`stop`, y la animación lo relee cada 500 ms.

## 5. GUI: mesa de luz con light-stage
Una columna, hero con vista previa fiel (`scale(base,pct)`, breathe 4 s,
rainbow), sin numeración decorativa. Motivo: el trabajo es "fijar luz en
<2 s"; la vista previa elimina el prueba-error contra el hardware.
