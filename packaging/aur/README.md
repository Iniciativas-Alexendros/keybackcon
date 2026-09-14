# Paquete AUR de keybackcon

`PKGBUILD` para [Arch Linux](https://archlinux.org) (AUR) que compila
`keybackcon` y instala el binario, la GUI (`keybackcon-gui`), el lanzador, el
icono, la regla udev, las unidades de usuario de systemd y la licencia.

## Antes de publicar (obligatorio)

1. **Mantenedor**: ya configurado (`operaciones@alexendros.dev`). Si cambia,
   actualiza la primera línea de `PKGBUILD`.
2. **Sumas de verificación**: `sha256sums` está a `SKIP` a propósito hasta
   tener el tarball del tag publicado. Regénéralo con:

   ```sh
   updpkgsums
   ```

   (o descarga el tag y ejecuta `sha256sum keybackcon-2.1.0.tar.gz`).
3. **`.SRCINFO`**: es un fichero generado que el AUR exige en cada push.
   No se edita a mano:

   ```sh
   makepkg --printsrcinfo > .SRCINFO
   ```

4. **Prueba local** en un sistema Arch:

   ```sh
   makepkg -si
   keybackcon info
   keybackcon-gui
   ```

## Publicar en AUR

```sh
git clone ssh://aur@aur.archlinux.org/keybackcon.git
cp PKGBUILD .SRCINFO keybackcon/
cd keybackcon && git add PKGBUILD .SRCINFO && git commit -m "keybackcon 2.1.0-1" && git push
```

## Actualizar a una versión nueva

1. Cambia `pkgver` (y `pkgrel=1`).
2. Comprueba que el tag `v$pkgver` existe en GitHub.
3. `updpkgsums` y `makepkg --printsrcinfo > .SRCINFO`.
4. Prueba con `makepkg -si` y empuja `PKGBUILD` + `.SRCINFO` juntos.

## Notas

- `conflicts`/`replaces=('kbd-rgb')`: `keybackcon` sustituye al paquete
  anterior; el estado en `~/.local/state` se migra solo.
- Dependencias opcionales de la GUI (`keybackcon-gui`): `python-gobject`, `gtk4`, `libadwaita`, `libayatana-appindicator` (solo necesarias para el panel gráfico; el CLI funciona sin ellas; `libayatana-appindicator` solo para el indicador de bandeja).
- Compilación aislada con `cargo build --release --locked` (sin red extra) más `msgfmt` (`gettext`, en `makedepends`) para compilar el locale `es` (`/usr/share/locale/es/LC_MESSAGES/keybackcon.mo`); el schema GSettings va a `/usr/share/glib-2.0/schemas/` y lo recompilan los hooks de glib2/pacman (sin scriptlets propios).
