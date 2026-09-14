#!/usr/bin/env python3
"""Keyboard Backlight Controls — mesa de luz GTK4/Adwaita para keybackcon."""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gdk
import math
import os
import shutil
import subprocess

APP_ID = "org.iniciativas.keybackcon"
APP_TITLE = "Keyboard Backlight Controls"


def find_binary():
    for cand in (
        shutil.which("keybackcon"),
        os.path.expanduser("~/.local/bin/keybackcon"),
        shutil.which("kbd-rgb"),
        os.path.expanduser("~/.local/bin/kbd-rgb"),
    ):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return "keybackcon"


BIN = find_binary()


def state_paths():
    base = os.environ.get(
        "XDG_STATE_HOME", os.path.expanduser("~/.local/state")
    )
    return (
        os.path.join(base, "keybackcon/state"),
        os.path.join(base, "kbd-rgb/state"),
    )


def pid_paths():
    base = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return (
        os.path.join(base, "keybackcon/animation.pid"),
        os.path.join(base, "keybackcon/anim.pid"),
        os.path.join(base, "kbd-rgb/anim.pid"),
    )


COLORES = [
    ("Blanco", "ffffff"),
    ("Tungsteno", "ffb86b"),
    ("Naranja", "ff7800"),
    ("Rojo", "ff0000"),
    ("Rosa", "ff50a0"),
    ("Púrpura", "a000ff"),
    ("Ultravioleta", "7c6cff"),
    ("Azul", "0000ff"),
    ("Cian", "00ffff"),
    ("Verde", "00ff00"),
    ("Apagado", "000000"),
]

CSS = """
window {
  background-color: #12141a;
}
.display-font {
  font-family: 'Space Grotesk', 'Inter', system-ui, sans-serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #f2efe6;
}
.body-font {
  font-family: 'IBM Plex Sans', 'Cantarell', system-ui, sans-serif;
  color: #8a93a6;
}
.mono-font {
  font-family: 'IBM Plex Mono', 'JetBrains Mono', ui-monospace, monospace;
  font-feature-settings: 'tnum';
  color: #8a93a6;
}
.section-label {
  font-family: 'IBM Plex Sans', 'Cantarell', system-ui, sans-serif;
  font-weight: 600;
  font-size: 13px;
  letter-spacing: 0.04em;
  color: #f2efe6;
}
.section-hint {
  font-size: 12px;
  color: #8a93a6;
}
.light-stage-frame {
  background-color: #1e222d;
  border-radius: 18px;
  border: 1px solid rgba(242, 239, 230, 0.08);
}
.swatch-btn {
  border-radius: 999px;
  min-width: 44px;
  min-height: 44px;
  padding: 0;
  border: 2px solid rgba(242, 239, 230, 0.14);
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
  background-color: rgba(242, 239, 230, 0.12);
  border-radius: 999px;
  min-height: 8px;
}
.bright-scale highlight {
  background: linear-gradient(90deg, #7c6cff, #ffb86b);
  border-radius: 999px;
}
.bright-scale slider {
  background-color: #f2efe6;
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
  color: #12141a;
}
.status-dot-alive {
  color: #7c6cff;
}
.status-dot-idle {
  color: #8a93a6;
}
"""


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def scale_rgb(h, pct):
    r, g, b = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    f = lambda v: int(round(v * pct / 100.0))
    return f(r) / 255.0, f(g) / 255.0, f(b) / 255.0


def hsv_to_rgb(h, s, v):
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


def get_state():
    for path in state_paths():
        try:
            with open(path) as f:
                parts = f.read().split()
                color = parts[0].lstrip("#").lower()
                pct = int(parts[1]) if len(parts) > 1 else 100
                if len(color) != 6:
                    raise ValueError
                int(color, 16)
                return color, max(0, min(100, pct))
        except Exception:
            continue
    return "ffffff", 100


def animations_enabled():
    try:
        settings = Gtk.Settings.get_default()
        return bool(settings.get_property("gtk-enable-animations"))
    except Exception:
        return True


def animation_running():
    for path in pid_paths():
        try:
            with open(path) as f:
                pid = int(f.read().strip())
            if pid <= 0:
                continue
            os.kill(pid, 0)
            with open(f"/proc/{pid}/cmdline", "rb") as cf:
                cmd = cf.read().decode(errors="ignore")
            if "keybackcon" in cmd or "kbd-rgb" in cmd:
                return pid
            os.unlink(path)
        except Exception:
            continue
    return None


def device_info():
    try:
        out = subprocess.run(
            [BIN, "info"], capture_output=True, text=True, timeout=5
        )
        if out.returncode != 0:
            return None
        info = {}
        for line in out.stdout.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
        return info
    except Exception:
        return None


class MesaWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title(APP_TITLE)
        self.set_default_size(420, 640)

        color_hex, pct = get_state()
        self.cur_color = color_hex
        self.cur_pct = pct
        self.preview_mode = "fijar"
        self.preview_t0 = GLib.get_monotonic_time()
        self.anim_proc = None
        self._bright_source = None
        self.swatch_buttons = {}

        css = Gtk.CssProvider()
        css.load_from_data(CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        toolbar = Adw.ToolbarView()
        self.toast_overlay.set_child(toolbar)
        toolbar.add_top_bar(Adw.HeaderBar())

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        toolbar.set_content(scroll)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content.set_margin_top(20)
        content.set_margin_bottom(20)
        content.set_margin_start(20)
        content.set_margin_end(20)
        scroll.set_child(content)

        hero_title = Gtk.Label(label="Fija tu luz en dos toques")
        hero_title.add_css_class("display-font")
        hero_title.add_css_class("title-1")
        hero_title.set_wrap(True)
        content.append(hero_title)

        hero_sub = Gtk.Label(
            label="Lo que ves arriba es lo que brilla abajo: elige color, ajusta intensidad y listo."
        )
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
        self.stage.set_draw_func(self._draw_stage, None)
        stage_frame.set_child(self.stage)

        self.stage_caption = Gtk.Label(label="")
        self.stage_caption.add_css_class("mono-font")
        content.append(self.stage_caption)

        content.append(self._section("Elige tu luz", "Toca un filtro o crea tu propio tono."))
        flow = Gtk.FlowBox()
        flow.set_selection_mode(Gtk.SelectionMode.NONE)
        flow.set_homogeneous(True)
        flow.set_max_children_per_line(6)
        flow.set_row_spacing(10)
        flow.set_column_spacing(10)
        content.append(flow)

        for nombre, hexv in COLORES:
            btn = Gtk.Button()
            btn.set_tooltip_text(f"{nombre} · #{hexv}")
            btn.add_css_class("swatch-btn")
            btn.set_size_request(44, 44)
            r, g, b = hex_to_rgb(hexv)
            provider = Gtk.CssProvider()
            provider.load_from_data(
                f".sw-{hexv} {{ background-color: #{hexv}; }}".encode()
            )
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )
            btn.add_css_class(f"sw-{hexv}")
            btn.connect("clicked", self._on_color, hexv, nombre)
            flow.append(btn)
            self.swatch_buttons[hexv] = btn

        custom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        custom_row.append(Gtk.Label(label="Tu tono:"))
        try:
            dlg = Gtk.ColorDialog()
            self.custom_btn = Gtk.ColorDialogButton(dialog=dlg)
            self.custom_btn.connect("notify::rgba", self._on_custom)
        except Exception:
            self.custom_btn = Gtk.ColorButton()
            self.custom_btn.connect("color-set", self._on_custom_legacy)
        custom_row.append(self.custom_btn)
        content.append(custom_row)

        content.append(
            self._section("Cuánta luz quieres", "Desliza o usa − / + . Se guarda solo.")
        )
        brow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        minus = Gtk.Button(label="−")
        minus.connect("clicked", self._on_bright_step, -5)
        brow.append(minus)
        self.bright_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 5
        )
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

        content.append(
            self._section("Cómo se mueve", "Fija la luz o déjala respirar.")
        )
        seg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        seg.set_homogeneous(True)
        self.seg_buttons = {}
        for key, label in (
            ("fijar", "Fijar"),
            ("breathe", "Respirar"),
            ("rainbow", "Arcoíris"),
        ):
            b = Gtk.ToggleButton(label=label)
            b.add_css_class("segmented-btn")
            b.connect("toggled", self._on_mode, key)
            seg.append(b)
            self.seg_buttons[key] = b
        content.append(seg)

        stop_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.stop_btn = Gtk.Button(label="Parar movimiento")
        self.stop_btn.connect("clicked", self._on_stop)
        stop_row.append(self.stop_btn)
        content.append(stop_row)

        content.append(self._section("Qué está pasando", "Estado vivo del teclado."))
        self.status_dot = Gtk.Label(label="●")
        self.status_text = Gtk.Label(label="mirando el teclado…")
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
        GLib.timeout_add(33, self._tick_preview)
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

    def _run_cli(self, args, ok_msg=None):
        try:
            subprocess.run([BIN] + args, check=True, timeout=10)
            if ok_msg:
                self._toast(ok_msg)
            return True
        except FileNotFoundError:
            self._error(f"No encuentro el binario ({BIN}). Instálalo primero.")
        except subprocess.CalledProcessError as e:
            self._error(f"El teclado no respondió: {e}")
        except subprocess.TimeoutExpired:
            self._error("El teclado tardó demasiado en responder.")
        return False

    def _error(self, msg):
        dlg = Adw.AlertDialog.new("Algo no salió", msg)
        dlg.add_response("ok", "Entendido")
        dlg.set_default_response("ok")
        dlg.set_close_response("ok")
        dlg.present(self)
        self._toast(msg)

    def _mark_selected(self):
        for hexv, btn in self.swatch_buttons.items():
            if hexv == self.cur_color:
                btn.add_css_class("selected")
            else:
                btn.remove_css_class("selected")

    def _refresh_caption(self):
        name = next(
            (n for n, h in COLORES if h == self.cur_color), "Tu tono"
        )
        self.stage_caption.set_text(f"{name} · #{self.cur_color} · {self.cur_pct}%")
        self.bright_value.set_text(f"{self.cur_pct}%")

    def _draw_stage(self, area, ctx, w, h, _data):
        ctx.set_source_rgb(0x12 / 255, 0x14 / 255, 0x1A / 255)
        ctx.paint()

        t = (GLib.get_monotonic_time() - self.preview_t0) / 1_000_000.0
        animate = animations_enabled()
        if self.preview_mode == "rainbow" and animate:
            r, g, b = hsv_to_rgb((t * 45.0) % 360.0, 1.0, 1.0)
            k = self.cur_pct / 100.0
            r, g, b = r * k, g * k, b * k
        elif self.preview_mode == "breathe" and animate:
            k = (1 - math.cos(t * 2 * math.pi / 4.0)) / 2.0
            factor = (8.0 + k * 92.0) * (self.cur_pct / 100.0) / 100.0
            br, bg, bb = hex_to_rgb(self.cur_color)
            r, g, b = br * factor, bg * factor, bb * factor
        else:
            r, g, b = scale_rgb(self.cur_color, self.cur_pct)

        cx, cy = w / 2.0, h / 2.0 - 8
        for i, alpha in ((64, 0.10), (48, 0.16), (34, 0.28)):
            ctx.set_source_rgba(r, g, b, alpha)
            ctx.arc(cx, cy, i, 0, 2 * math.pi)
            ctx.fill()

        ctx.set_source_rgb(r, g, b)
        ctx.set_line_width(3)
        ctx.rectangle(cx - 72, cy - 22, 144, 44)
        ctx.stroke()
        for i in range(3):
            for j in range(8):
                x = cx - 60 + j * 17
                y = cy - 10 + i * 11
                ctx.rectangle(x, y, 10, 5)
                ctx.fill()

        ctx.set_source_rgba(0.95, 0.94, 0.90, 0.75)
        ctx.set_font_size(11)
        ctx.move_to(12, h - 12)
        try:
            ctx.show_text(f"#{self.cur_color} · {self.cur_pct}% · {self.preview_mode}")
        except Exception:
            pass

    def _tick_preview(self):
        self.stage.queue_draw()
        return GLib.SOURCE_CONTINUE

    def _tick_status(self):
        pid = animation_running()
        info = device_info()
        if pid:
            self.status_dot.set_text("●")
            self.status_dot.remove_css_class("status-dot-idle")
            self.status_dot.add_css_class("status-dot-alive")
            base = f"moviéndose (pid {pid})"
        else:
            self.status_dot.set_text("○")
            self.status_dot.remove_css_class("status-dot-alive")
            self.status_dot.add_css_class("status-dot-idle")
            base = "luz fija"
        if info:
            hid = info.get("dispositivo", "?")
            lamps = info.get("nº lámparas", info.get("n lámparas", "?"))
            self.status_text.set_text(f"{base} · {hid} · {lamps} zona(s)")
        else:
            self.status_text.set_text(f"{base} · sin teclado a la vista")
        return GLib.SOURCE_CONTINUE

    def _on_color(self, _btn, hexv, nombre):
        self.cur_color = hexv
        self.preview_t0 = GLib.get_monotonic_time()
        self._stop_child()
        if self._run_cli(["set", hexv], f"{nombre} aplicado"):
            self._mark_selected()
            self._refresh_caption()

    def _on_custom(self, btn, _pspec):
        rgba = btn.get_rgba()
        hexv = f"{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.cur_color = hexv
        self.preview_t0 = GLib.get_monotonic_time()
        self._stop_child()
        if self._run_cli(["set", hexv], f"Tu tono #{hexv} aplicado"):
            self._mark_selected()
            self._refresh_caption()

    def _on_custom_legacy(self, btn):
        rgba = btn.get_rgba()
        hexv = f"{int(rgba.red*255):02x}{int(rgba.green*255):02x}{int(rgba.blue*255):02x}"
        self.cur_color = hexv
        self._stop_child()
        if self._run_cli(["set", hexv], f"Tu tono #{hexv} aplicado"):
            self._mark_selected()
            self._refresh_caption()

    def _on_bright(self, scale):
        v = int(scale.get_value())
        self.cur_pct = v
        self._refresh_caption()
        if self._bright_source is not None:
            GLib.source_remove(self._bright_source)
        self._bright_source = GLib.timeout_add(150, self._apply_bright, v)

    def _on_bright_step(self, _btn, delta):
        v = max(0, min(100, self.cur_pct + delta))
        self.bright_scale.set_value(v)

    def _apply_bright(self, v):
        self._bright_source = None
        self._run_cli(["brightness", str(v)])
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
            self._stop_child()
            self._run_cli(["stop"])
            self._run_cli(["set", self.cur_color])
        else:
            self.preview_mode = key
            self.preview_t0 = GLib.get_monotonic_time()
            self._start_child(key)

    def _start_child(self, mode):
        self._stop_child()
        self._run_cli(["firmware-effects", "off"])
        try:
            self.anim_proc = subprocess.Popen([BIN, "animation", mode])
            self._toast(f"Movimiento {mode} en marcha")
        except FileNotFoundError:
            self._error(f"No encuentro el binario ({BIN}).")

    def _stop_child(self):
        if self.anim_proc is not None and self.anim_proc.poll() is None:
            self.anim_proc.terminate()
            try:
                self.anim_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.anim_proc.kill()
                self.anim_proc.wait()
        self.anim_proc = None

    def _on_stop(self, _btn):
        self._stop_child()
        self.preview_mode = "fijar"
        for b in self.seg_buttons.values():
            b.set_active(False)
        self.seg_buttons["fijar"].set_active(True)
        if self._run_cli(["stop"], "Luz fijada de nuevo"):
            self._run_cli(["set", self.cur_color])

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

    def _on_close(self, _widget):
        self._stop_child()
        color_hex, _ = get_state()
        try:
            subprocess.run([BIN, "set", color_hex], timeout=5)
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
