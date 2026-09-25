import unittest

from gui import i18n


class TestI18n(unittest.TestCase):
    def test_setup_devuelve_idioma_soportado(self):
        self.assertEqual(i18n.setup_i18n("es"), "es")
        self.assertEqual(i18n.get_language(), "es")

    def test_codigo_con_region_y_mayusculas(self):
        self.assertEqual(i18n.setup_i18n("ES-ES"), "es")
        self.assertEqual(i18n.setup_i18n("en_US"), "en")

    def test_idioma_no_soportado_ca_a_es(self):
        self.assertEqual(i18n.setup_i18n("fr"), "es")

    def test_nulo_usa_el_locale_del_sistema(self):
        from unittest import mock

        with mock.patch("gui.i18n.locale.getdefaultlocale", return_value=("en_US", "UTF-8")):
            self.assertEqual(i18n.setup_i18n(None), "en")
        with mock.patch("gui.i18n.locale.getdefaultlocale", return_value=(None, None)):
            self.assertEqual(i18n.setup_i18n(None), "es")

    def test_normalize_code_directo(self):
        self.assertEqual(i18n._normalize_code("EN-gb"), "en")
        self.assertEqual(i18n._normalize_code(""), "es")
        self.assertEqual(i18n._normalize_code("pt_BR"), "es")

    def test_translation_object_con_gettext(self):
        i18n.setup_i18n("es")
        tr = i18n._translation
        self.assertTrue(hasattr(tr, "gettext"))
        # Identidad con msgid español (traducción actual es identidad).
        self.assertEqual(tr.gettext("Preferencias"), "Preferencias")


if __name__ == "__main__":
    unittest.main()
