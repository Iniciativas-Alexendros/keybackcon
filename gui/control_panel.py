#!/usr/bin/env python3
try:
    from gui.window import MesaWindow, main, on_activate, APP_ID, APP_TITLE
except ImportError:
    try:
        from window import MesaWindow, main, on_activate, APP_ID, APP_TITLE
    except ImportError:
        from .window import MesaWindow, main, on_activate, APP_ID, APP_TITLE
try:
    from gui.colors import COLORES, hex_to_rgb, scale_rgb, hsv_to_rgb
except ImportError:
    try:
        from colors import COLORES, hex_to_rgb, scale_rgb, hsv_to_rgb
    except ImportError:
        from .colors import COLORES, hex_to_rgb, scale_rgb, hsv_to_rgb
try:
    from gui.client import KeybackconClient, KeybackconError, find_binary, state_paths, pid_paths
except ImportError:
    try:
        from client import KeybackconClient, KeybackconError, find_binary, state_paths, pid_paths
    except ImportError:
        from .client import KeybackconClient, KeybackconError, find_binary, state_paths, pid_paths
try:
    from gui.preview import animations_enabled
except ImportError:
    try:
        from preview import animations_enabled
    except ImportError:
        from .preview import animations_enabled


BIN = find_binary()


def get_state():
    return KeybackconClient().get_state_file()


def animation_running():
    return KeybackconClient().animation_running()


def device_info():
    try:
        return KeybackconClient().info()
    except Exception:
        return None


if __name__ == "__main__":
    main()
