"""Tests de los helpers puros de la bandeja.

Importación condicional: en sistemas sin Gtk3/Ayatana/pycairo (p. ej. CI)
toda la clase se salta con skip.
"""
import os
import shutil
import tempfile
import unittest

try:
    from gui import tray

    DISPONIBLE = True
    FALTA = None
except Exception as exc:  # gi/Ayatana/cairo ausentes
    tray = None
    DISPONIBLE = False
    FALTA = str(exc)


@unittest.skipUnless(DISPONIBLE, "bandeja no importable aquí (%s)" % FALTA)
class TestHelpersBandeja(unittest.TestCase):
    def test_normalize_hex(self):
        self.assertEqual(tray._normalize_hex("FF7800"), "ff7800")
        self.assertEqual(tray._normalize_hex("#00ffff"), "00ffff")
        self.assertEqual(tray._normalize_hex("  AABBCC  "), "aabbcc")

    def test_normalize_hex_basura_es_blanco(self):
        for basura in ("", "12345", "1234567", "zzzzzz", None, "12 45"):
            self.assertEqual(tray._normalize_hex(basura), "ffffff", basura)

    def test_normalize_mode(self):
        self.assertEqual(tray._normalize_mode("breathe"), "breathe")
        self.assertEqual(tray._normalize_mode("off"), "off")
        self.assertEqual(tray._normalize_mode("nose"), "fijar")
        self.assertEqual(tray._normalize_mode(None), "fijar")

    def test_clamp_brightness(self):
        self.assertEqual(tray._clamp_brightness(150), 100)
        self.assertEqual(tray._clamp_brightness(-3), 0)
        self.assertEqual(tray._clamp_brightness("42"), 42)
        self.assertEqual(tray._clamp_brightness("abc"), 100)
        self.assertEqual(tray._clamp_brightness(None), 100)

    def test_render_icon_genera_png_por_modo(self):
        prev = os.environ.get("XDG_CACHE_HOME")
        tmp = tempfile.mkdtemp(prefix="kbc-test-cache-")
        os.environ["XDG_CACHE_HOME"] = tmp
        try:
            for modo in ("fijar", "breathe", "rainbow", "off"):
                ruta = tray.render_tray_icon("ff7800", modo)
                self.assertTrue(os.path.isfile(ruta), modo)
                with open(ruta, "rb") as f:
                    self.assertEqual(f.read(8), b"\x89PNG\r\n\x1a\n", modo)
        finally:
            if prev is None:
                os.environ.pop("XDG_CACHE_HOME", None)
            else:
                os.environ["XDG_CACHE_HOME"] = prev
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
