NIVELES = [(1, "Mínimo", 10), (2, "Bajo", 30), (3, "Medio", 50), (4, "Alto", 75), (5, "Máximo", 100)]


def pct_de_nivel(n):
    try:
        v = int(n)
    except Exception:
        v = 3
    if v < 1:
        v = 1
    if v > 5:
        v = 5
    for nivel, _nombre, pct in NIVELES:
        if nivel == v:
            return pct
    return 50


def pct_a_nivel(pct):
    try:
        v = float(pct)
    except Exception:
        v = 100.0
    mejor = 1
    mejor_d = None
    for nivel, _nombre, p in NIVELES:
        d = abs(v - float(p))
        if mejor_d is None or d < mejor_d or (d == mejor_d and nivel > mejor):
            mejor = nivel
            mejor_d = d
    return mejor


def avanzar(pct, delta):
    try:
        d = int(delta)
    except Exception:
        d = 0
    try:
        v = float(pct)
    except Exception:
        v = 50.0
    pcs = sorted(p for _, _, p in NIVELES)
    if d > 0:
        superiores = [p for p in pcs if p > v]
        objetivo = min(superiores) if superiores else pcs[-1]
    elif d < 0:
        inferiores = [p for p in pcs if p < v]
        objetivo = max(inferiores) if inferiores else pcs[0]
    else:
        objetivo = v
    return pct_a_nivel(objetivo)
