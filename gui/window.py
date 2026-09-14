import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk
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
    from gui.client import KeybackconClient, KeybackconError
except ImportError:
    try:
        from .client import KeybackconClient, KeybackconError
    except ImportError:
        from client import KeybackconClient, KeybackconError
try:
    from gui.colors import COLORES
except ImportError:
    try:
        from .colors import COLORES
    except ImportError:
        from colors import COLORES
try:
    from gui.preview import StagePreview, mode_label
except ImportError:
    try:
        from .preview import StagePreview, mode_label
    except ImportError:
        from preview import StagePreview, mode_label
try:
    from gui.theme import apply_saved_theme, set_theme, get_theme
except ImportError:
    try:
        from .theme import apply_saved_theme, set_theme, get_theme
    except ImportError:
        from theme import apply_saved_theme, set_theme, get_theme
try:
    from gui.settings import SettingsDialog, is_effects_enabled
except ImportError:
    try:
        from .settings import SettingsDialog, is_effects_enabled
    except ImportError:
        try:
            from settings import SettingsDialog, is_effects_enabled
        except ImportError:
            SettingsDialog = None

            def is_effects_enabled():
                return True


APP_ID = "org.iniciativas.keybackcon"
APP_TITLE = "Keyboard Backlight Controls"


BASE_CSS = """
.display-font {
  font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: @window_fg_color;
}
.body-font {
  font-family: 'IBM Plex Sans', 'Cantarell', system-ui, sans-serif;
  color: @window_fg_color;
}
.mono-font {
  font-family: 'IBM Plex Mono', 'JetBrains Mono', ui-monospace, monospace;
  font-feature-settings: 'tnum';
  color: alpha(@window_fg_color, 0.75);
}
.section-label {
  font-family: 'IBM Plex Sans', 'Cantarell', system-ui, sans-serif;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: @window_fg_color;
}
.section-hint {
  font-size: 12px;
  color: alpha(@window_fg_color, 0.65);
}
.light-stage-frame {
  background-color: @card_bg_color;
  border-radius: 18px;
  border: 1px solid alpha(@window_fg_color, 0.08);
}
.swatch-btn {
  border-radius: 999px;
  min-width: 44px;
  min-height: 44px;
  padding: 0;
  border: 2px solid alpha(@window_fg_color, 0.14);
}
.swatch-btn:hover {
  border-color: #ffb86b;
}
.swatch-btn.selected {
  border-color: #7c6cff;
  box-shadow: 0 0 0 2px rgba(124, 108, 255, 0.45);
}
.swatch-btn:focus-visible {
  outline: 2px solid #ffb86b;
  outline-offset: 2px;
}
.bright-scale trough {
  background-color: alpha(@window_fg_color, 0.12);
  border-radius: 999px;
  min-height: 8px;
}
.bright-scale highlight {
  background: linear-gradient(90deg, #7c6cff, #ffb86b);
  border-radius: 999px;
}
.bright-scale slider {
  background-color: @window_fg_color;
  border: 2px solid #ffb86b;
  border-radius: 999px;
  min-width: 20px;
  min-height: 20px;
}
.segmented-btn {
  border-radius: 999px;
  padding: 8px 16px;
  font-weight: 600;
}
.segmented-btn.suggested {
  background: linear-gradient(135deg, #7c6cff, #ffb86b);
  color: black;
}
.status-dot-alive {
  color: #7c6cff;
}
.status-dot-idle {
  color: alpha(@window_fg_color, 0.5);
}
"""


_CSS_PROVIDER = None
_CSS_LOADED = False


def _swatch_css():
    parts = []
    for _nombre, hexv in COLORES:
        parts.append(f".sw-{hexv} {{ background-color: #{hexv}; }}")
    return "\n".join(parts)


def _full_css():
    return BASE_CSS + "\n" + _swatch_css()


def _ensure_css():
    global _CSS_PROVIDER, _CSS_LOADED
    if _CSS_LOADED and _CSS_PROVIDER is not None:
        return _CSS_PROVIDER
    provider = Gtk.CssProvider()
    provider.load_from_data(_full_css().encode())
    try:
        display = Gdk.Display.get_default()
        if display is not None:
            Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    except Exception:
        pass
    _CSS_PROVIDER = provider
    _CSS_LOADED = True
    return provider


class MesaWindow(Adw.ApplicationWindow):
    @property
    def cur_color(self):
        return self._preview.color_hex

    @cur_color.setter
    def cur_color(self, value):
        self._preview.color_hex = value

    @property
    def cur_pct(self):
        return self._preview.pct

    @cur_pct.setter
    def cur_pct(self, value):
        self._preview.pct = value

    @property
    def preview_mode(self):
        return self._preview.mode

    @preview_mode.setter
    def preview_mode(self, value):
        self._preview.mode = value

    @property
    def preview_t0(self):
        return self._preview.t0

    @preview_t0.setter
    def preview_t0(self, value):
        self._preview.t0 = value

    def __init__(self, app, client=None, on_preferences=None):
        super().__init__(application=app)
        apply_saved_theme()
        self.set_title(_("Keyboard Backlight Controls"))
        self.set_default_size(420, 640)
        self._on_preferences = on_preferences
        if client is None:
            self._client = KeybackconClient()
        else:
            self._client = client
        try:
            color_hex, pct = self._client.get_state_file()
        except Exception:
            color_hex, pct = "ffffff", 100
        self._preview = StagePreview(color_hex, pct, "fijar")
        try:
            self._preview.set_effects_enabled(is_effects_enabled())
        except Exception:
            pass
        self._bright_source = None
        self.swatch_buttons = {}
        _ensure_css()
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)
        header = Adw.HeaderBar()
        prefs_button = Gtk.Button.new_from_icon_name("preferences-system-symbolic")
        prefs_button.set_tooltip_text(_("Preferencias"))
        prefs_button.connect("clicked", self._on_preferences_clicked)
        header.pack_end(prefs_button)
        toolbar.add_top_bar(header)
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scroll.set_child(content)
        hero_title = Gtk.Label(label=_("Fija tu luz en dos toques"))
        hero_title.add_css_class("display-font")
        hero_title.add_css_class("title-1")
        hero_title.set_wrap(True)
        content.append(hero_title)
        hero_sub = Gtk.Label(label=_("Lo que ves arriba es lo que brilla abajo: elige color, ajusta intensidad y listo."))
        hero_sub.add_css_class("body-font")
        hero_sub.set_wrap(True)
        content.append(hero_sub)
        stage_frame = Gtk.Frame()
        stage_frame.add_css_class("light-stage-frame")
        stage_frame.set_size_request(-1, 190)
        content.append(stage_frame)
        self.stage = Gtk.DrawingArea()
        self.stage.set_hexpand(True)
        self.stage.set_vexpand(True)
        stage_frame.set_child(self.stage)
        self._stage_tick_id = None
        self._stage_tick_id = self._preview.attach(self.stage, 16)
        try:
            self.connect("hide", self._on_stage_hide)
        except Exception:
            pass
        try:
            self.connect("show", self._on_stage_show)
        except Exception:
            pass
        try:
            self.connect("unmap", self._on_stage_hide)
        except Exception:
            pass
        try:
            self.connect("map", self._on_stage_show)
        except Exception:
            pass
        self.stage_caption = Gtk.Label(label="")
        self.stage_caption.add_css_class("mono-font")
        content.append(self.stage_caption)
        theme_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        theme_row.set_homogeneous(True)
        self.theme_buttons = {}
        try:
            current_theme = get_theme()
        except Exception:
            current_theme = "system"
        for tmode, tlabel in (("system", _("Sistema")), ("light", _("Claro")), ("dark", _("Oscuro"))):
            tb = Gtk.ToggleButton(label=tlabel)
            tb.add_css_class("segmented-btn")
            if tmode == current_theme:
                tb.set_active(True)
            tb.connect("toggled", self._on_theme, tmode)
            theme_row.append(tb)
            self.theme_buttons[tmode] = tb
        content.append(theme_row)
        content.append(self._section(_("Elige tu luz"), _("Toca un filtro o crea tu propio tono.")))
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_max_children_per_line(6)
        flow.set_row_spacing(10)
        flow.set_column_spacing(10)
        content.append(flow)
        for nombre, hexv in COLORES:
            btn = Gtk.Button()
            btn.set_tooltip_text(f"{_(nombre)} · #{hexv}")
            btn.add_css_class("swatch-btn")
            btn.set_size_request(44, 44)
            btn.add_css_class(f"sw-{hexv}")
            btn.connect("clicked", self._on_color, hexv, nombre)
            flow.append(btn)
            self.swatch_buttons[hexv] = btn
        custom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        custom_row.append(Gtk.Label(label=_("Tu tono:")))
        try:
            dlg = Gtk.ColorDialog()
            self.custom_btn = Gtk.ColorDialogButton(dialog=dlg)
            self.custom_btn.connect("notify::rgba", self._on_custom)
        except Exception:
            self.custom_btn = Gtk.ColorButton()
            self.custom_btn.connect("color-set", self._on_custom_legacy)
        custom_row.append(self.custom_btn)
        content.append(custom_row)
        content.append(self._section(_("Cuánta luz quieres"), _("Desliza o usa − / + . Se guarda solo.")))
        brow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        minus = Gtk.Button(label="−")
        minus.connect("clicked", self._on_bright_step, -5)
        brow.append(minus)
        self.bright_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        self.bright_scale.add_css_class("bright-scale")
        self.bright_scale.set_value(self.cur_pct)
        self.bright_scale.set_hexpand(True)
        self.bright_scale.set_draw_value(False)
        self.bright_scale.connect("value-changed", self._on_bright)
        brow.append(self.bright_scale)
        plus = Gtk.Button(label="+")
        plus.connect("clicked", self._on_bright_step, 5)
        brow.append(plus)
        self.bright_value = Gtk.Label(label=f"{self.cur_pct}%")
        self.bright_value.add_css_class("mono-font")
        self.bright_value.set_width_chars(5)
        brow.append(self.bright_value)
        content.append(brow)
        content.append(self._section(_("Cómo se mueve"), _("Fija la luz o déjala respirar.")))
        seg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        seg.set_homogeneous(True)
        self.seg_buttons = {}
        for key, label in (("fijar", _("Fijar")), ("breathe", _("Respirar")), ("rainbow", _("Arcoíris"))):
            b = Gtk.ToggleButton(label=label)
            b.add_css_class("segmented-btn")
            b.connect("toggled", self._on_mode, key)
            seg.append(b)
            self.seg_buttons[key] = b
        content.append(seg)
        stop_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.stop_btn = Gtk.Button(label=_("Parar movimiento"))
        self.stop_btn.connect("clicked", self._on_stop)
        stop_row.append(self.stop_btn)
        content.append(stop_row)
        content.append(self._section(_("Qué está pasando"), _("Estado vivo del teclado.")))
        self.status_dot = Gtk.Label(label="●")
        self.status_text = Gtk.Label(label=_("mirando el teclado…"))
        self.status_text.add_css_class("mono-font")
        self.status_text.set_xalign(0)
        self.status_text.set_hexpand(True)
        srow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        srow.append(self.status_dot)
        srow.append(self.status_text)
        content.append(srow)
        self.connect("close-request", self._on_close)
        key_ctl = Gtk.EventControllerKey()
        key_ctl.connect("key-pressed", self._on_key)
        self.add_controller(key_ctl)
        self._mark_selected()
        self._refresh_caption()
        GLib.timeout_add(1000, self._tick_status)
        self._tick_status()

    def _section(self, title, hint):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl = Gtk.Label(label=title)
        lbl.add_css_class("section-label")
        lbl.set_xalign(0)
        box.append(lbl)
        sub = Gtk.Label(label=hint)
        sub.add_css_class("section-hint")
        sub.set_xalign(0)
        box.append(sub)
        return box

    def _toast(self, msg):
        self.toast_overlay.add_toast(Adw.Toast.new(msg))

    def _error(self, msg):
        dlg = Adw.AlertDialog.new(_("Algo no salió"), msg)
        dlg.add_response("ok", _("Entendido"))
        dlg.set_default_response("ok")
        dlg.set_close_response("ok")
        dlg.present(self)
        self._toast(msg)

    def _run_set(self, hexv, ok_msg=None):
        try:
            self._client.set_color(hexv)
        except KeybackconError as e:
            self._error(e.message)
            return False
        except Exception as e:
            self._error(str(e))
            return False
        if ok_msg:
            self._toast(ok_msg)
        return True

    def _run_brightness(self, value):
        try:
            self._client.set_brightness(value)
        except KeybackconError as e:
            self._error(e.message)
            return False
        except Exception as e:
            self._error(str(e))
            return False
        return True

    def _run_stop(self, ok_msg=None):
        try:
            self._client.stop()
        except KeybackconError as e:
            self._error(e.message)
            return False
        except Exception as e:
            self._error(str(e))
            return False
        if ok_msg:
            self._toast(ok_msg)
        return True

    def _run_animation(self, mode):
        try:
            self._client.animation(mode)
        except KeybackconError as e:
            self._error(e.message)
            return False
        except Exception as e:
            self._error(str(e))
            return False
        self._toast(_("Movimiento {mode} en marcha").format(mode=mode_label(mode)))
        return True

    def _mark_selected(self):
        for hexv, btn in self.swatch_buttons.items():
            if hexv == self.cur_color:
                btn.add_css_class("selected")
            else:
                btn.remove_css_class("selected")

    def _refresh_caption(self):
        name = next((n for n, h in COLORES if h == self.cur_color), "Tu tono")
        self.stage_caption.set_text(f"{_(name)} · #{self.cur_color} · {self.cur_pct}%")
        self.bright_value.set_text(f"{self.cur_pct}%")

    def _tick_status(self):
        try:
            pid = self._client.animation_running()
        except Exception:
            pid = None
        try:
            info = self._client.info()
        except KeybackconError:
            info = None
        except Exception:
            info = None
        if pid:
            self.status_dot.set_text("●")
            self.status_dot.remove_css_class("status-dot-idle")
            self.status_dot.add_css_class("status-dot-alive")
            base = _("moviéndose (pid {pid})").format(pid=pid)
        else:
            self.status_dot.set_text("○")
            self.status_dot.remove_css_class("status-dot-alive")
            self.status_dot.add_css_class("status-dot-idle")
            base = _("luz fija")
        if info:
            hid = info.get("dispositivo", "?")
            lamps = info.get("nº lámparas", info.get("n lámparas", "?"))
            self.status_text.set_text(f"{base} · {hid} · {lamps} {_('zona(s)')}")
        else:
            self.status_text.set_text(f"{base} · {_('sin teclado a la vista')}")
        return GLib.SOURCE_CONTINUE

    def _on_color(self, _btn, hexv, nombre):
        self.cur_color = hexv
        self._preview.reset_clock()
        try:
            self._client._stop_child()
        except Exception:
            pass
        if self._run_set(hexv, _("{nombre} aplicado").format(nombre=_(nombre))):
            self._mark_selected()
            self._refresh_caption()

    def _on_custom(self, btn, _pspec):
        rgba = btn.get_rgba()
        hexv = f"{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.cur_color = hexv
        self._preview.reset_clock()
        try:
            self._client._stop_child()
        except Exception:
            pass
        if self._run_set(hexv, _("Tu tono #{hexv} aplicado").format(hexv=hexv)):
            self._mark_selected()
            self._refresh_caption()

    def _on_custom_legacy(self, btn):
        rgba = btn.get_rgba()
        hexv = f"{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.cur_color = hexv
        self._preview.reset_clock()
        try:
            self._client._stop_child()
        except Exception:
            pass
        if self._run_set(hexv, _("Tu tono #{hexv} aplicado").format(hexv=hexv)):
            self._mark_selected()
            self._refresh_caption()

    def _on_bright(self, scale):
        v = int(scale.get_value())
        self.cur_pct = v
        self._preview.set_brightness(v)
        self._refresh_caption()
        if self._bright_source is not None:
            GLib.source_remove(self._bright_source)
        self._bright_source = GLib.timeout_add(150, self._apply_bright, v)

    def _on_bright_step(self, _btn, delta):
        v = max(0, min(100, self.cur_pct + delta))
        self.bright_scale.set_value(v)

    def _apply_bright(self, v):
        self._bright_source = None
        self._run_brightness(v)
        return GLib.SOURCE_REMOVE

    def _on_mode(self, btn, key):
        if not btn.get_active():
            return
        for k, b in self.seg_buttons.items():
            if k != key:
                b.set_active(False)
        btn.add_css_class("suggested")
        for k, b in self.seg_buttons.items():
            if k != key:
                b.remove_css_class("suggested")
        if key == "fijar":
            self.preview_mode = "fijar"
            self._run_stop()
            self._run_set(self.cur_color)
        else:
            self.preview_mode = key
            self._preview.reset_clock()
            self._run_animation(key)

    def _on_stop(self, _btn):
        try:
            self._client._stop_child()
        except Exception:
            pass
        self.preview_mode = "fijar"
        for b in self.seg_buttons.values():
            b.set_active(False)
        self.seg_buttons["fijar"].set_active(True)
        if self._run_stop(_("Luz fijada de nuevo")):
            self._run_set(self.cur_color)

    def open_preferences(self):
        try:
            if SettingsDialog is None:
                return False
            dialog = SettingsDialog(on_effects_changed=self._preview.set_effects_enabled)
            dialog.present(self)
            return True
        except Exception:
            return False

    def _on_preferences_clicked(self, _button):
        handler = self._on_preferences
        if handler is not None:
            try:
                handler()
            except Exception:
                pass
            return
        self.open_preferences()

    def _on_theme(self, btn, mode):
        if not btn.get_active():
            return
        for k, b in self.theme_buttons.items():
            if k != mode:
                b.set_active(False)
        try:
            set_theme(mode)
        except Exception:
            pass

    def _on_key(self, _ctl, keyval, _keycode, state):
        if state & Gdk.ModifierType.CONTROL_MASK:
            if 49 <= keyval <= 57:
                idx = keyval - 49
                if idx < len(COLORES):
                    nombre, hexv = COLORES[idx]
                    self._on_color(None, hexv, nombre)
                    return True
        name = Gdk.keyval_name(keyval)
        if name in ("plus", "KP_Add", "equal"):
            self._on_bright_step(None, 5)
            return True
        if name in ("minus", "KP_Subtract"):
            self._on_bright_step(None, -5)
            return True
        return False

    def _on_stage_hide(self, *args):
        tick_id = getattr(self, "_stage_tick_id", None)
        if tick_id is not None:
            try:
                GLib.source_remove(tick_id)
            except Exception:
                pass
            self._stage_tick_id = None

    def _on_stage_show(self, *args):
        if getattr(self, "_stage_tick_id", None) is None:
            try:
                self._preview.reset_clock()
            except Exception:
                pass
            try:
                self._stage_tick_id = self._preview.attach(self.stage, 16)
            except Exception:
                self._stage_tick_id = None

    def _on_close(self, _widget):
        try:
            self._client._stop_child()
        except Exception:
            pass
        try:
            color_hex, _pct = self._client.get_state_file()
        except Exception:
            color_hex = "ffffff"
        try:
            self._client.set_color(color_hex)
        except Exception:
            pass
        return False


def on_activate(app):
    win = MesaWindow(app)
    win.present()


def main():
    app = Adw.Application(application_id=APP_ID)
    app.connect("activate", on_activate)
    app.run(None)


if __name__ == "__main__":
    main()
