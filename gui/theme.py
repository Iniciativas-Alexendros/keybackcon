import os
try:
    import gi
    gi.require_version("Adw", "1")
    from gi.repository import Adw
except Exception:
    Adw = None


VALID_MODES = ("system", "light", "dark")
SCHEMA_ID = "org.iniciativas.keybackcon"
THEME_KEY = "theme"
_cached_settings = None


def _config_file():
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "keybackcon", "theme")


def _gsettings():
    global _cached_settings
    if _cached_settings is not None:
        return _cached_settings
    try:
        from gi.repository import Gio
        source = Gio.SettingsSchemaSource.get_default()
        if source is None:
            return None
        if source.lookup(SCHEMA_ID, True) is None:
            return None
        _cached_settings = Gio.Settings.new(SCHEMA_ID)
        return _cached_settings
    except Exception:
        return None


def get_theme() -> str:
    settings = _gsettings()
    if settings is not None:
        try:
            mode = settings.get_string(THEME_KEY).strip().lower()
            if mode in VALID_MODES:
                return mode
        except Exception:
            pass
    try:
        with open(_config_file()) as f:
            mode = f.read().strip().lower()
            if mode in VALID_MODES:
                return mode
    except Exception:
        pass
    return "system"


def _apply(mode):
    if Adw is None:
        return mode
    try:
        manager = Adw.StyleManager.get_default()
        if manager is None:
            return mode
        if mode == "light":
            manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif mode == "dark":
            manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
    except Exception:
        pass
    return mode


def set_theme(mode: str):
    normalized = (mode or "system").strip().lower()
    if normalized not in VALID_MODES:
        normalized = "system"
    try:
        path = _config_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(normalized + "\n")
    except Exception:
        pass
    settings = _gsettings()
    if settings is not None:
        try:
            settings.set_string(THEME_KEY, normalized)
            settings.sync()
        except Exception:
            pass
    return _apply(normalized)


def apply_saved_theme() -> str:
    return _apply(get_theme())
