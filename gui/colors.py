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
