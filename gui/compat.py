"""Detección de distribución y sugerencias de paquetes.

Centraliza los nombres de paquete de la GUI por familia de gestor de
paquetes (apt/pacman/dnf/zypper) para que los mensajes de error y los
avisos de install.sh digan exactamente qué instalar en cada distro.
"""
import os

# rol -> familia -> paquetes que lo cubren
PAQUETES = {
    "gui": {
        "apt": ["python3", "python3-gi", "gir1.2-gtk-4.0", "gir1.2-adw-1"],
        "pacman": ["python-gobject", "gtk4", "libadwaita"],
        "dnf": ["python3-gobject", "gtk4", "libadwaita"],
        "zypper": ["python3-gobject", "gtk4", "libadwaita"],
    },
    "bandeja": {
        "apt": ["gir1.2-ayatanaappindicator3-0.1", "python3-cairo"],
        "pacman": ["libayatana-appindicator", "python-cairo"],
        "dnf": ["libayatana-appindicator-gtk3", "python3-cairo"],
        "zypper": ["libayatana-appindicator3-1", "python3-cairo"],
    },
    "herramientas": {
        "apt": ["gettext", "libglib2.0-bin"],
        "pacman": ["gettext", "glib2"],
        "dnf": ["gettext", "glib2"],
        "zypper": ["gettext", "glib2"],
    },
}

_CMD_INSTALAR = {
    "apt": "sudo apt install",
    "pacman": "sudo pacman -S",
    "dnf": "sudo dnf install",
    "zypper": "sudo zypper install",
}

_CLAVES_FAMILIA = {
    "apt": {"debian", "ubuntu", "linuxmint", "pop", "apt"},
    "pacman": {"arch", "manjaro", "endeavouros", "pacman"},
    "dnf": {"fedora", "rhel", "centos", "nobara", "dnf"},
    "zypper": {"opensuse", "suse", "tumbleweed", "zypper"},
}


def _familia_desde_contenido(contenido):
    data = {}
    for linea in contenido.splitlines():
        if "=" in linea:
            clave, _, valor = linea.partition("=")
            data[clave.strip()] = valor.strip().strip('"')
    ids = [data.get("ID", "").lower()]
    ids += data.get("ID_LIKE", "").lower().split()
    for familia, claves in _CLAVES_FAMILIA.items():
        if any(i in claves for i in ids if i):
            return familia
    return None


def familia_paquetes(os_release="/etc/os-release"):
    """Familia de gestor de paquetes ('apt', 'pacman', ...) o None."""
    try:
        with open(os_release, encoding="utf-8") as f:
            return _familia_desde_contenido(f.read())
    except OSError:
        return None


def sugerencia_instalacion(*roles, os_release="/etc/os-release"):
    """Comando concreto para instalar los paquetes de `roles` en esta distro."""
    fam = familia_paquetes(os_release)
    if fam is None:
        pkgs = sorted(
            {p for r in roles for por_fam in PAQUETES.get(r, {}).values() for p in por_fam}
        )
        return "instala con tu gestor de paquetes: " + " ".join(pkgs)
    pkgs = [p for r in roles for p in PAQUETES.get(r, {}).get(fam, [])]
    return "%s %s" % (_CMD_INSTALAR[fam], " ".join(pkgs))
