import os
import shutil
import tempfile
import unittest
from unittest import mock

from gui import theme


class EntornoConfig:
    def __init__(self):
        self._prev = os.environ.get("XDG_CONFIG_HOME")
        self.tmp = tempfile.mkdtemp(prefix="kbc-test-config-")
        os.environ["XDG_CONFIG_HOME"] = self.tmp

    def restaurar(self):
        if self._prev is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._prev
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestTema(unittest.TestCase):
    def setUp(self):
        self.env = EntornoConfig()
        theme._schema_cache.clear()
        # Los tests cubren la vía de archivo; GSettings depende de si el
        # schema está instalado en la máquina, así que se aísla.
        self._sin_gsettings = mock.patch.object(
            theme, "lookup_settings", return_value=None
        )
        self._sin_gsettings.start()

    def tearDown(self):
        self._sin_gsettings.stop()
        theme._schema_cache.clear()
        self.env.restaurar()

    def test_default_system_sin_nada(self):
        self.assertEqual(theme.get_theme(), "system")

    def test_roundtrip_archivo(self):
        self.assertEqual(theme.set_theme("dark"), "dark")
        self.assertEqual(theme.get_theme(), "dark")
        theme.set_theme("LIGHT")  # mayúsculas: se normaliza
        self.assertEqual(theme.get_theme(), "light")

    def test_valor_invalido_ca_a_system(self):
        self.assertEqual(theme.set_theme("neon"), "system")
        self.assertEqual(theme.get_theme(), "system")

    def test_valor_invalido_en_archivo_ignorado(self):
        path = os.path.join(self.env.tmp, "keybackcon", "theme")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("chicle\n")
        self.assertEqual(theme.get_theme(), "system")

    def test_lookup_settings_con_schema_inexistente_devuelve_none(self):
        # Un schema que no existe en ningún sistema siempre da None.
        self._sin_gsettings.stop()
        try:
            theme._schema_cache.clear()
            self.assertIsNone(
                theme.lookup_settings("org.iniciativas.keybackcon.inexistente")
            )
        finally:
            theme._schema_cache.clear()
            self._sin_gsettings.start()


if __name__ == "__main__":
    unittest.main()
