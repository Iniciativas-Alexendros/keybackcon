# keybackcon (npm)

Keyboard Backlight Controls — control RGB del teclado AERO X16 vía HID
LampArray, sin dependencias. Este paquete instala el binario precompilado
(Linux x86_64/arm64) y configura automáticamente la regla udev y las unidades
systemd de usuario.

```sh
npm install -g keybackcon
```

El postinstalador:

- instala la regla udev de acceso al hidraw (vía `sudo`/`pkexec`; se omite con
  `KEYBACKCON_SKIP_UDEV=1 npm install -g keybackcon` o si ya existe);
- instala las unidades `keybackcon.service` (restaura tu color al iniciar
  sesión) y `keybackcon-animation@.service` en `~/.config/systemd/user` y las
  recarga con `systemctl --user daemon-reload`.

Fuente, GUI GTK, .deb y AUR: https://github.com/Soluciones-Alexendros/keybackcon
