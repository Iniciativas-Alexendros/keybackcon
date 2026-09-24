#!/usr/bin/env python3
try:
    from gui import load, log_exc
except ImportError:  # ejecución directa: gui/ en sys.path
    import importlib
    import sys

    def load(nombre):
        return importlib.import_module(nombre)

    def log_exc(contexto):
        tipo, exc, _tb = sys.exc_info()
        print(f"keybackcon-gui: {contexto}: {tipo.__name__}: {exc}",
              file=sys.stderr)

_window = load("window")
MesaWindow = _window.MesaWindow
main = _window.main
on_activate = _window.on_activate
APP_ID = _window.APP_ID
APP_TITLE = _window.APP_TITLE
_colors = load("colors")
COLORES = _colors.COLORES
hex_to_rgb = _colors.hex_to_rgb
scale_rgb = _colors.scale_rgb
hsv_to_rgb = _colors.hsv_to_rgb
_client = load("client")
KeybackconClient = _client.KeybackconClient
KeybackconError = _client.KeybackconError
find_binary = _client.find_binary
state_paths = _client.state_paths
pid_paths = _client.pid_paths
animations_enabled = load("preview").animations_enabled


BIN = find_binary()


def get_state():
    return KeybackconClient().get_state_file()


def animation_running():
    return KeybackconClient().animation_running()


def device_info():
    try:
        return KeybackconClient().info()
    except Exception:
        log_exc("info del dispositivo")
        return None


if __name__ == "__main__":
    main()
