import math
import os
import sys

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
    from gui.client import KeybackconError
except ImportError:
    try:
        from .client import KeybackconError
    except ImportError:
        from client import KeybackconError

try:
    from gui.brightness import avanzar, pct_a_nivel, pct_de_nivel
except ImportError:
    try:
        from .brightness import avanzar, pct_a_nivel, pct_de_nivel
    except ImportError:
        from brightness import avanzar, pct_a_nivel, pct_de_nivel


class TrayUnavailable(Exception):
    pass


try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3, Gtk, GLib
    import cairo
except Exception as exc:
    raise TrayUnavailable(
        "AyatanaAppIndicator3 0.1 no disponible: %s" % exc
    ) from exc


MODES = ("fijar", "breathe", "rainbow", "off")
BRIGHT_STEP = 5


def _normalize_hex(color_hex):
    try:
        h = str(color_hex).strip().lstrip("#").lower()
        if len(h) != 6:
            return "ffffff"
        int(h, 16)
        return h
    except Exception:
        return "ffffff"


def _normalize_mode(mode):
    if mode in MODES:
        return mode
    return "fijar"


def _clamp_brightness(value):
    try:
        v = int(value)
    except Exception:
        v = 100
    return max(0, min(100, v))


def _hex_to_rgb(h):
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def _hsv_to_rgb(h, s, v):
    c = v * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    return r + m, g + m, b + m


def _cache_dir():
    base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    path = os.path.join(base, "keybackcon")
    os.makedirs(path, exist_ok=True)
    return path


def render_tray_icon(color_hex, mode):
    color_hex = _normalize_hex(color_hex)
    mode = _normalize_mode(mode)
    path = os.path.join(_cache_dir(), "tray-%s-%s.png" % (color_hex, mode))
    size = 64
    cx = cy = size / 2.0
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surface)
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.paint()
    ctx.set_operator(cairo.OPERATOR_OVER)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    if mode == "off":
        ctx.set_source_rgb(0.16, 0.18, 0.22)
        ctx.arc(cx, cy, 20, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgb(0.55, 0.58, 0.65)
        ctx.set_line_width(2.5)
        ctx.arc(cx, cy, 20, 0, 2 * math.pi)
        ctx.stroke()
        ctx.set_source_rgba(0.95, 0.94, 0.90, 0.9)
        ctx.set_line_width(3.5)
        ctx.move_to(cx - 10, cy + 10)
        ctx.line_to(cx + 10, cy - 10)
        ctx.stroke()
    else:
        r, g, b = _hex_to_rgb(color_hex)
        if mode == "breathe":
            ctx.set_source_rgba(r, g, b, 0.25)
            ctx.arc(cx, cy, 26, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(r, g, b, 0.55)
            ctx.set_line_width(2.0)
            ctx.arc(cx, cy, 23, 0, 2 * math.pi)
            ctx.stroke()
        if mode == "rainbow":
            for i in range(6):
                hr, hg, hb = _hsv_to_rgb(i * 60.0, 1.0, 1.0)
                ctx.set_source_rgb(hr, hg, hb)
                ctx.set_line_width(4.0)
                a0 = math.radians(i * 60 + 4)
                a1 = math.radians((i + 1) * 60 - 4)
                ctx.arc(cx, cy, 24.5, a0, a1)
                ctx.stroke()
        ctx.set_source_rgb(r, g, b)
        ctx.arc(cx, cy, 20, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.9)
        ctx.set_line_width(2.5)
        ctx.arc(cx, cy, 20, 0, 2 * math.pi)
        ctx.stroke()
        ctx.set_source_rgba(1, 1, 1, 0.18)
        ctx.arc(cx - 6, cy - 7, 6, 0, 2 * math.pi)
        ctx.fill()
    surface.write_to_png(path)
    return path


class TrayIndicator:
    def __init__(self, client, on_toggle_window, on_preferences=None, on_about=None):
        self._client = client
        self._on_toggle_window = on_toggle_window
        self._on_preferences = on_preferences
        self._on_about = on_about
        self._mode = "fijar"
        self._color = "ffffff"
        self._brightness = 100
        try:
            color, pct = client.get_state_file()
            self._color = _normalize_hex(color)
            self._brightness = pct_de_nivel(pct_a_nivel(pct))
        except Exception:
            pass
        self._pending = []
        self._visible = True
        self._indicator = AyatanaAppIndicator3.Indicator.new(
            "keybackcon",
            "keybackcon",
            AyatanaAppIndicator3.IndicatorCategory.HARDWARE,
        )
        self._indicator.set_title("keybackcon")
        self._indicator.set_status(AyatanaAppIndicator3.IndicatorStatus.ACTIVE)
        self._build_menu()
        self._render_icon()
        try:
            self._indicator.connect("scroll-event", self._on_scroll)
        except Exception:
            pass
        for signal in ("activate", "activate-event"):
            try:
                self._indicator.connect(signal, self._on_activate_signal)
                break
            except Exception:
                continue
        try:
            GLib.timeout_add_seconds(2, self._tick)
        except Exception:
            pass

    def _build_menu(self):
        menu = Gtk.Menu()
        self._open_item = Gtk.MenuItem.new_with_label(_("Abrir ventana"))
        self._open_item.connect("activate", self._ui_open)
        menu.append(self._open_item)
        menu.append(Gtk.SeparatorMenuItem())
        self._fijar_item = Gtk.MenuItem.new_with_label(_("Fijar color"))
        self._fijar_item.connect("activate", self._do_fijar)
        menu.append(self._fijar_item)
        self._breathe_item = Gtk.MenuItem.new_with_label(_("Respirar"))
        self._breathe_item.connect(
            "activate", lambda *a: self._do_animation("breathe")
        )
        menu.append(self._breathe_item)
        self._rainbow_item = Gtk.MenuItem.new_with_label(_("Arcoíris"))
        self._rainbow_item.connect(
            "activate", lambda *a: self._do_animation("rainbow")
        )
        menu.append(self._rainbow_item)
        self._off_item = Gtk.MenuItem.new_with_label(_("Apagar"))
        self._off_item.connect("activate", self._do_off)
        menu.append(self._off_item)
        menu.append(Gtk.SeparatorMenuItem())
        self._bright_up_item = Gtk.MenuItem.new_with_label(_("Subir brillo"))
        self._bright_up_item.connect(
            "activate", lambda *a: self._do_brightness(BRIGHT_STEP)
        )
        menu.append(self._bright_up_item)
        self._bright_down_item = Gtk.MenuItem.new_with_label(_("Bajar brillo"))
        self._bright_down_item.connect(
            "activate", lambda *a: self._do_brightness(-BRIGHT_STEP)
        )
        menu.append(self._bright_down_item)
        menu.append(Gtk.SeparatorMenuItem())
        self._prefs_item = Gtk.MenuItem.new_with_label(_("Preferencias"))
        if self._on_preferences is None:
            self._prefs_item.set_sensitive(False)
        else:
            self._prefs_item.connect("activate", self._ui_preferences)
        menu.append(self._prefs_item)
        self._about_item = Gtk.MenuItem.new_with_label(_("Acerca de"))
        if self._on_about is None:
            self._about_item.set_sensitive(False)
        else:
            self._about_item.connect("activate", self._ui_about)
        menu.append(self._about_item)
        self._quit_item = Gtk.MenuItem.new_with_label(_("Salir"))
        self._quit_item.connect("activate", self._ui_quit)
        menu.append(self._quit_item)
        menu.show_all()
        self._menu = menu
        self._indicator.set_menu(menu)
        try:
            self._indicator.set_secondary_activate_target(self._open_item)
        except Exception:
            pass

    def _safe(self, fn):
        try:
            fn()
        except KeybackconError:
            self._pending.append(fn)
        except Exception as exc:
            print("keybackcon tray: %s" % exc, file=sys.stderr)

    def _tick(self):
        if self._pending:
            rest = []
            for fn in self._pending:
                try:
                    fn()
                except KeybackconError:
                    rest.append(fn)
                except Exception as exc:
                    print("keybackcon tray: %s" % exc, file=sys.stderr)
            self._pending = rest
        return True

    def _render_icon(self):
        try:
            path = render_tray_icon(self._color, self._mode)
        except Exception as exc:
            print("keybackcon tray: %s" % exc, file=sys.stderr)
            return
        try:
            self._indicator.set_icon_full(path, "keybackcon")
        except Exception:
            try:
                self._indicator.set_icon(path)
            except Exception:
                pass

    def _ui_open(self, *args):
        try:
            self._on_toggle_window()
        except Exception:
            pass

    def _on_activate_signal(self, *args):
        self._ui_open()

    def _ui_preferences(self, *args):
        try:
            self._on_preferences()
        except Exception:
            pass

    def _ui_about(self, *args):
        try:
            self._on_about()
        except Exception:
            pass

    def _ui_quit(self, *args):
        self.quit()

    def _do_fijar(self, *args):
        color = self._color
        self._mode = "fijar"
        self._render_icon()
        self._safe(lambda: (self._client.stop(), self._client.set_color(color)))

    def _do_animation(self, mode):
        self._mode = _normalize_mode(mode)
        self._render_icon()
        self._safe(lambda: self._client.animation(self._mode))

    def _do_off(self, *args):
        self._mode = "off"
        self._render_icon()
        self._safe(lambda: self._client.off())

    def _do_brightness(self, delta):
        try:
            nivel = avanzar(self._brightness, delta)
        except Exception:
            nivel = 3
        try:
            target = pct_de_nivel(nivel)
        except Exception:
            target = 100
        self._brightness = target
        self._safe(lambda: self._client.set_brightness(target))

    def _on_scroll(self, _indicator, steps, _orientation, *args):
        try:
            delta = 1 if int(steps) > 0 else -1
        except Exception:
            return True
        self._do_brightness(delta)
        return True

    def set_visible(self, visible):
        self._visible = bool(visible)
        try:
            if self._visible:
                self._indicator.set_status(
                    AyatanaAppIndicator3.IndicatorStatus.ACTIVE
                )
            else:
                self._indicator.set_status(
                    AyatanaAppIndicator3.IndicatorStatus.PASSIVE
                )
        except Exception:
            pass

    def update_state(self, mode: str, color_hex: str, brightness: int):
        self._mode = _normalize_mode(mode)
        self._color = _normalize_hex(color_hex)
        try:
            self._brightness = pct_de_nivel(pct_a_nivel(brightness))
        except Exception:
            self._brightness = _clamp_brightness(brightness)
        self._render_icon()

    def quit(self):
        try:
            self._client.stop()
        except Exception:
            pass
        try:
            self._indicator.set_status(
                AyatanaAppIndicator3.IndicatorStatus.PASSIVE
            )
        except Exception:
            pass
        try:
            if Gtk.main_level() > 0:
                Gtk.main_quit()
        except Exception:
            pass
        os._exit(0)
