import os
try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw, Gio, Gtk
except Exception:
    Adw = None
    Gio = None
    Gtk = None
try:
    from gui.i18n import _
except ImportError:
    try:
        from .i18n import _
    except ImportError:
        try:
            from i18n import _
        except ImportError:
            def _(s):
                return s
try:
    from gui.theme import get_theme, set_theme
except ImportError:
    try:
        from .theme import get_theme, set_theme
    except ImportError:
        from theme import get_theme, set_theme
try:
    from gui import __version__ as APP_VERSION
except ImportError:
    try:
        from . import __version__ as APP_VERSION
    except ImportError:
        APP_VERSION = "2.2.0"


SCHEMA_ID = "org.iniciativas.keybackcon"
EFFECTS_KEY = "effects"
RESTORE_KEY = "restore-on-login"
REPO_URL = "https://github.com/Iniciativas-Alexendros/keybackcon"
AUTOSTART_NAME = "keybackcon-tray.desktop"
AUTOSTART_EXEC = "keybackcon-gui --tray"
_cached_settings = None


def get_settings():
    global _cached_settings
    if Gio is None:
        return None
    if _cached_settings is not None:
        return _cached_settings
    try:
        source = Gio.SettingsSchemaSource.get_default()
        if source is None:
            return None
        if source.lookup(SCHEMA_ID, True) is None:
            return None
        _cached_settings = Gio.Settings.new(SCHEMA_ID)
        return _cached_settings
    except Exception:
        return None


def _pref_file(name):
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "keybackcon", name)


def _read_bool_file(name, default):
    try:
        with open(_pref_file(name)) as f:
            text = f.read().strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off"):
            return False
    except Exception:
        pass
    return default


def _write_bool_file(name, value):
    try:
        path = _pref_file(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("true\n" if value else "false\n")
    except Exception:
        pass
    return bool(value)


def is_effects_enabled():
    settings = get_settings()
    if settings is not None:
        try:
            return bool(settings.get_boolean(EFFECTS_KEY))
        except Exception:
            pass
    return _read_bool_file("effects", True)


def set_effects_enabled(enabled):
    value = bool(enabled)
    settings = get_settings()
    if settings is not None:
        try:
            settings.set_boolean(EFFECTS_KEY, value)
            settings.sync()
        except Exception:
            pass
    return _write_bool_file("effects", value)


def is_restore_enabled():
    settings = get_settings()
    if settings is not None:
        try:
            return bool(settings.get_boolean(RESTORE_KEY))
        except Exception:
            pass
    return _read_bool_file("restore-on-login", True)


def set_restore_enabled(enabled):
    value = bool(enabled)
    settings = get_settings()
    if settings is not None:
        try:
            settings.set_boolean(RESTORE_KEY, value)
            settings.sync()
        except Exception:
            pass
    return _write_bool_file("restore-on-login", value)


def _autostart_file():
    base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    return os.path.join(base, "autostart", AUTOSTART_NAME)


def _autostart_content():
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=keybackcon\n"
        "Exec=%s\n"
        "Hidden=false\n"
        "X-GNOME-Autostart-enabled=true\n" % AUTOSTART_EXEC
    )


def is_autostart_enabled():
    try:
        with open(_autostart_file()) as f:
            content = f.read()
        if "Hidden=true" in content:
            return False
        return "Exec=%s" % AUTOSTART_EXEC in content
    except Exception:
        return False


def set_autostart_enabled(enabled):
    path = _autostart_file()
    if not enabled:
        try:
            os.unlink(path)
        except Exception:
            pass
        return False
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(_autostart_content())
    except Exception:
        return False
    return True


if Adw is not None:
    class SettingsDialog(Adw.PreferencesDialog):
        def __init__(self, on_effects_changed=None):
            super().__init__()
            self._on_effects_changed = on_effects_changed
            self.set_title(_("Preferencias"))
            self.add(self._appearance_page())
            self.add(self._behavior_page())
            self.add(self._about_page())

        def _appearance_page(self):
            page = Adw.PreferencesPage()
            page.set_title(_("Apariencia"))
            page.set_icon_name("preferences-desktop-theme-symbolic")
            group = Adw.PreferencesGroup()
            page.add(group)
            theme_row = Adw.ComboRow()
            theme_row.set_title(_("Tema"))
            theme_row.set_model(Gtk.StringList.new([_("Sistema"), _("Claro"), _("Oscuro")]))
            modes = ("system", "light", "dark")
            try:
                current = get_theme()
            except Exception:
                current = "system"
            if current not in modes:
                current = "system"
            theme_row.set_selected(modes.index(current))
            theme_row.connect("notify::selected", self._on_theme_changed)
            group.add(theme_row)
            effects_row = Adw.SwitchRow()
            effects_row.set_title(_("Efectos del escenario"))
            effects_row.set_subtitle(_("Partículas y animación en la vista previa."))
            try:
                effects_row.set_active(is_effects_enabled())
            except Exception:
                effects_row.set_active(True)
            effects_row.connect("notify::active", self._on_effects_toggled)
            group.add(effects_row)
            return page

        def _behavior_page(self):
            page = Adw.PreferencesPage()
            page.set_title(_("Comportamiento"))
            page.set_icon_name("preferences-system-symbolic")
            group = Adw.PreferencesGroup()
            page.add(group)
            autostart_row = Adw.SwitchRow()
            autostart_row.set_title(_("Arranque automático"))
            autostart_row.set_subtitle(_("Abrir en la bandeja al iniciar la sesión."))
            try:
                autostart_row.set_active(is_autostart_enabled())
            except Exception:
                autostart_row.set_active(False)
            autostart_row.connect("notify::active", self._on_autostart_toggled)
            group.add(autostart_row)
            restore_row = Adw.SwitchRow()
            restore_row.set_title(_("Restaurar color al iniciar"))
            restore_row.set_subtitle(_("Aplicar el último color al abrir."))
            try:
                restore_row.set_active(is_restore_enabled())
            except Exception:
                restore_row.set_active(True)
            restore_row.connect("notify::active", self._on_restore_toggled)
            group.add(restore_row)
            return page

        def _about_page(self):
            page = Adw.PreferencesPage()
            page.set_title(_("Acerca de"))
            page.set_icon_name("help-about-symbolic")
            group = Adw.PreferencesGroup()
            group.set_title("keybackcon")
            page.add(group)
            version_row = Adw.ActionRow()
            version_row.set_title(_("Versión"))
            version_row.add_suffix(Gtk.Label(label=APP_VERSION))
            group.add(version_row)
            license_row = Adw.ActionRow()
            license_row.set_title(_("Licencia"))
            license_row.add_suffix(Gtk.Label(label="MIT"))
            group.add(license_row)
            link_row = Adw.ActionRow()
            link_row.set_title(_("Código fuente"))
            link_row.set_subtitle(REPO_URL)
            link_row.set_activatable(True)
            link_row.connect("activated", self._on_repo_activated)
            group.add(link_row)
            return page

        def _on_theme_changed(self, row, _pspec):
            modes = ("system", "light", "dark")
            try:
                mode = modes[row.get_selected()]
            except Exception:
                return
            try:
                set_theme(mode)
            except Exception:
                pass

        def _on_effects_toggled(self, row, _pspec):
            try:
                enabled = bool(row.get_active())
            except Exception:
                return
            try:
                set_effects_enabled(enabled)
            except Exception:
                pass
            if self._on_effects_changed is not None:
                try:
                    self._on_effects_changed(enabled)
                except Exception:
                    pass

        def _on_autostart_toggled(self, row, _pspec):
            try:
                enabled = bool(row.get_active())
            except Exception:
                return
            try:
                set_autostart_enabled(enabled)
            except Exception:
                pass

        def _on_restore_toggled(self, row, _pspec):
            try:
                enabled = bool(row.get_active())
            except Exception:
                return
            try:
                set_restore_enabled(enabled)
            except Exception:
                pass

        def _on_repo_activated(self, _row):
            try:
                Gtk.show_uri(None, REPO_URL, 0)
            except Exception:
                pass
