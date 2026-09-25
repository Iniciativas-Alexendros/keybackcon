import unittest

from gui.colors import COLORES, hex_to_rgb, hsv_to_rgb, scale_rgb


class TestColores(unittest.TestCase):
    def test_hex_to_rgb_primarios(self):
        self.assertEqual(hex_to_rgb("ff0000"), (1.0, 0.0, 0.0))
        self.assertEqual(hex_to_rgb("00ff00"), (0.0, 1.0, 0.0))
        self.assertEqual(hex_to_rgb("0000ff"), (0.0, 0.0, 1.0))
        self.assertEqual(hex_to_rgb("000000"), (0.0, 0.0, 0.0))

    def test_hex_to_rgb_acepta_almohadilla(self):
        self.assertEqual(hex_to_rgb("#ffffff"), (1.0, 1.0, 1.0))

    def test_scale_rgb_limites(self):
        self.assertEqual(scale_rgb("ff7800", 0), (0.0, 0.0, 0.0))
        r, g, b = scale_rgb("ff7800", 100)
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(g, 0x78 / 255.0)
        self.assertAlmostEqual(b, 0.0)

    def test_scale_rgb_redondeo(self):
        r, _g, _b = scale_rgb("ffffff", 50)
        # 255*0.5 = 127.5 → redondeo a 128/255.
        self.assertAlmostEqual(r, 128 / 255.0, places=5)

    def test_hsv_primarios_en_rango(self):
        for h, esperado in ((0, (1, 0, 0)), (120, (0, 1, 0)), (240, (0, 0, 1))):
            r, g, b = hsv_to_rgb(h, 1.0, 1.0)
            self.assertAlmostEqual(r, esperado[0])
            self.assertAlmostEqual(g, esperado[1])
            self.assertAlmostEqual(b, esperado[2])

    def test_hsv_sin_saturacion_es_gris(self):
        r, g, b = hsv_to_rgb(200.0, 0.0, 0.5)
        self.assertAlmostEqual(r, 0.5)
        self.assertAlmostEqual(g, 0.5)
        self.assertAlmostEqual(b, 0.5)

    def test_hsv_salida_siempre_en_rango(self):
        for h in range(0, 360, 13):
            for s in (0.0, 0.5, 1.0):
                for v in (0.0, 0.5, 1.0):
                    r, g, b = hsv_to_rgb(float(h), s, v)
                    for canal in (r, g, b):
                        self.assertGreaterEqual(canal, 0.0)
                        self.assertLessEqual(canal, 1.0)

    def test_colores_presets_bien_formados(self):
        self.assertGreaterEqual(len(COLORES), 8)
        for nombre, hexv in COLORES:
            self.assertTrue(nombre)
            self.assertEqual(len(hexv), 6)
            int(hexv, 16)  # lanza ValueError si no es hex


if __name__ == "__main__":
    unittest.main()
