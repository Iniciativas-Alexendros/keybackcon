import os
import tempfile
import unittest

from gui import compat


OS_RELEASES = {
    "ubuntu": 'ID=ubuntu\nID_LIKE="debian"\n',
    "arch": 'ID=arch\nID_LIKE=""\n',
    "manjaro": 'ID=manjaro\nID_LIKE="arch"\n',
    "fedora": 'ID=fedora\nID_LIKE=""\n',
    "opensuse": 'ID=opensuse-tumbleweed\nID_LIKE="suse opensuse"\n',
    "desconocida": 'ID=mi distro\nID_LIKE=""\n',
}


def _con_os_release(contenido):
    tmp = tempfile.NamedTemporaryFile("w", suffix="-os-release", delete=False)
    tmp.write(contenido)
    tmp.close()
    return tmp.name


class TestCompat(unittest.TestCase):
    def test_familia_detectada(self):
        for nombre, contenido in OS_RELEASES.items():
            ruta = _con_os_release(contenido)
            try:
                fam = compat.familia_paquetes(ruta)
                if nombre in ("ubuntu",):
                    self.assertEqual(fam, "apt", nombre)
                elif nombre in ("arch", "manjaro"):
                    self.assertEqual(fam, "pacman", nombre)
                elif nombre == "fedora":
                    self.assertEqual(fam, "dnf", nombre)
                elif nombre == "opensuse":
                    self.assertEqual(fam, "zypper", nombre)
                else:
                    self.assertIsNone(fam, nombre)
            finally:
                os.unlink(ruta)

    def test_sugerencia_por_familia(self):
        casos = {
            "ubuntu": compat.PAQUETES["bandeja"]["apt"],
            "arch": compat.PAQUETES["bandeja"]["pacman"],
            "fedora": compat.PAQUETES["bandeja"]["dnf"],
        }
        for distro, paquetes in casos.items():
            ruta = _con_os_release(OS_RELEASES[distro])
            try:
                sug = compat.sugerencia_instalacion("bandeja", os_release=ruta)
                for pkg in paquetes:
                    self.assertIn(pkg, sug, distro)
                self.assertTrue(
                    sug.startswith("sudo"), "%s: %s" % (distro, sug)
                )
            finally:
                os.unlink(ruta)

    def test_sugerencia_desconocida_no_crash(self):
        ruta = _con_os_release(OS_RELEASES["desconocida"])
        try:
            sug = compat.sugerencia_instalacion("gui", os_release=ruta)
            self.assertIn("gestor de paquetes", sug)
        finally:
            os.unlink(ruta)

    def test_os_release_ausente(self):
        self.assertIsNone(compat.familia_paquetes("/no/existe/os-release"))


if __name__ == "__main__":
    unittest.main()
