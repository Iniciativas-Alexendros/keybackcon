#!/usr/bin/env python3
import os
import sys

APP_ID = "org.iniciativas.keybackcon"

USAGE = """Uso: main.py [--tray] [-h | --help]

Keyboard Backlight Controls — ventana y bandeja del sistema.

Opciones:
  --tray      Arranca en la bandeja del sistema, sin ventana visible.
  -h, --help  Muestra esta ayuda y sale con código 0."""


def _fix_path():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    for path in (root, here):
        if path not in sys.path:
            sys.path.insert(0, path)


_fix_path()


def print_usage(out=None):
    stream = sys.stdout if out is None else out
    stream.write(USAGE + "\n")


def _setup_i18n():
    try:
        from gui.i18n import setup_i18n
    except ImportError:
        from i18n import setup_i18n
    return setup_i18n()


def _app_version():
    try:
        from gui import __version__ as version
        return version
    except ImportError:
        return "2.1.0"


def _load_client():
    try:
        from gui.client import KeybackconClient
    except ImportError:
        from client import KeybackconClient
    return KeybackconClient()


def _load_tray():
    try:
        from gui.tray import TrayIndicator, TrayUnavailable
    except ImportError:
        from tray import TrayIndicator, TrayUnavailable
    return TrayIndicator, TrayUnavailable


def _load_window():
    try:
        from gui.control_panel import MesaWindow
    except ImportError:
        from control_panel import MesaWindow
    return MesaWindow


def _open_preferences(parent=None, on_effects_changed=None):
    try:
        try:
            from gui.settings import SettingsDialog
        except ImportError:
            from settings import SettingsDialog
    except Exception as exc:
        print("keybackcon: preferencias no disponibles (%s)" % exc,
              file=sys.stderr)
        return False
    try:
        dialog = SettingsDialog(on_effects_changed=on_effects_changed)
        dialog.present(parent)
        return True
    except Exception as exc:
        print("keybackcon: no se pudieron abrir las preferencias (%s)" % exc,
              file=sys.stderr)
        return False


def _stop_client(client):
    try:
        client.stop()
    except Exception:
        pass


def _run_window():
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    MesaWindow = _load_window()
    app = Adw.Application(application_id=APP_ID)

    def on_activate(app):
        holder = {}

        def on_preferences():
            win = holder.get("win")
            if win is None:
                _open_preferences(None, None)
            else:
                win.open_preferences()

        win = MesaWindow(app, on_preferences=on_preferences)
        holder["win"] = win
        win.present()

    app.connect("activate", on_activate)
    return app.run(None)


def _run_tray():
    try:
        TrayIndicator, _TrayUnavailable = _load_tray()
    except Exception as exc:
        print("Aviso: bandeja no disponible (%s); abriendo ventana." % exc,
              file=sys.stderr)
        return _run_window()
    client = _load_client()
    try:
        MesaWindow = _load_window()
    except Exception as exc:
        print("Aviso: ventana GTK4 no disponible junto a la bandeja "
              "(%s); solo bandeja." % exc, file=sys.stderr)
        MesaWindow = None
    if MesaWindow is None:
        return _run_tray_only(client, TrayIndicator)
    return _run_tray_with_window(client, TrayIndicator, MesaWindow)


def _initial_tray_state(client):
    color, pct = "ffffff", 100
    try:
        color, pct = client.get_state_file()
    except Exception:
        pass
    mode = "fijar"
    try:
        if client.animation_running():
            mode = "breathe"
    except Exception:
        pass
    return mode, color, pct


def _run_tray_only(client, TrayIndicator):
    from gi.repository import Gtk, GLib

    window_proc = []

    def on_toggle_window(*args):
        window_proc[:] = [p for p in window_proc if p.poll() is None]
        if window_proc:
            return
        try:
            import subprocess

            here = os.path.dirname(os.path.abspath(__file__))
            window_proc.append(
                subprocess.Popen([sys.executable, os.path.join(here, "main.py")])
            )
        except Exception as exc:
            print("keybackcon: no se pudo abrir la ventana (%s)" % exc,
                  file=sys.stderr)

    def on_about(*args):
        try:
            dialog = Gtk.MessageDialog(
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.CLOSE,
                text="keybackcon %s" % _app_version(),
            )
            dialog.format_secondary_text("Keyboard Backlight Controls")
            dialog.run()
            dialog.destroy()
        except Exception:
            pass

    def on_preferences(*args):
        _open_preferences(None, None)

    tray = TrayIndicator(client, on_toggle_window, on_preferences, on_about)
    try:
        mode, color, pct = _initial_tray_state(client)
        tray.update_state(mode, color, pct)
    except Exception:
        pass

    def on_signal(*args):
        _stop_client(client)
        try:
            if Gtk.main_level() > 0:
                Gtk.main_quit()
        except Exception:
            pass
        return False

    try:
        import signal

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, sig, on_signal)
            except Exception:
                pass
    except Exception:
        pass
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    finally:
        _stop_client(client)
    return 0


def _run_tray_with_window(client, TrayIndicator, MesaWindow):
    import gi

    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Adw

    app = Adw.Application(application_id=APP_ID)
    state = {"window": None, "tray": None}

    def on_toggle_window(*args):
        win = state.get("window")
        if win is None:
            return
        try:
            if win.is_visible():
                win.hide()
            else:
                win.present()
        except Exception:
            pass

    def on_about(*args):
        win = state.get("window")
        try:
            dialog = Adw.AlertDialog.new(
                "keybackcon %s" % _app_version(),
                "Keyboard Backlight Controls",
            )
            dialog.add_response("ok", "Cerrar")
            dialog.set_default_response("ok")
            dialog.set_close_response("ok")
            if win is not None:
                dialog.present(win)
            else:
                dialog.present()
        except Exception:
            pass

    def on_preferences(*args):
        win = state.get("window")
        if win is None:
            _open_preferences(None, None)
        else:
            win.open_preferences()

    def on_activate(app):
        if state["window"] is None:
            win = MesaWindow(app, on_preferences=on_preferences)
            state["window"] = win

            def on_close(window, *args):
                if state.get("tray") is not None:
                    try:
                        window.hide()
                    except Exception:
                        pass
                    return True
                return False

            win.connect("close-request", on_close)
        if state["tray"] is None:
            tray = TrayIndicator(client, on_toggle_window, on_preferences, on_about)
            state["tray"] = tray
            try:
                mode, color, pct = _initial_tray_state(client)
                tray.update_state(mode, color, pct)
            except Exception:
                pass

    def on_shutdown(app, *args):
        _stop_client(client)

    app.connect("activate", on_activate)
    app.connect("shutdown", on_shutdown)
    return app.run(None)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if "-h" in args or "--help" in args:
        print_usage()
        return 0
    _setup_i18n()
    use_tray = "--tray" in args
    if not use_tray:
        return _run_window()
    return _run_tray()


if __name__ == "__main__":
    sys.exit(main())
