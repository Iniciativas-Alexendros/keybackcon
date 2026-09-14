pub type Rgb = (u8, u8, u8);

pub const PRESETS: &[(&str, Rgb)] = &[
    ("red", (255, 0, 0)),
    ("green", (0, 255, 0)),
    ("blue", (0, 0, 255)),
    ("cyan", (0, 255, 255)),
    ("magenta", (255, 0, 255)),
    ("yellow", (255, 255, 0)),
    ("orange", (255, 120, 0)),
    ("purple", (160, 0, 255)),
    ("pink", (255, 80, 160)),
    ("white", (255, 255, 255)),
    ("off", (0, 0, 0)),
];

pub fn parse_color(s: &str) -> Result<Rgb, String> {
    let t = s.trim().to_lowercase();
    let t = t.strip_prefix('#').unwrap_or(t.as_str());
    if let Some(&(_, c)) = PRESETS.iter().find(|(n, _)| *n == t) {
        return Ok(c);
    }
    if t.len() == 6 {
        if let Ok(v) = u32::from_str_radix(t, 16) {
            return Ok((
                ((v >> 16) & 0xFF) as u8,
                ((v >> 8) & 0xFF) as u8,
                (v & 0xFF) as u8,
            ));
        }
    }
    Err(format!(
        "no se pudo interpretar el color: '{s}' (usa hex 'ff6400' o un predefinido: {})",
        PRESETS
            .iter()
            .map(|(n, _)| *n)
            .collect::<Vec<_>>()
            .join(", ")
    ))
}

pub fn scale((r, g, b): Rgb, pct: u32) -> Rgb {
    let f = |v: u8| ((v as u32 * pct + 50) / 100).min(255) as u8;
    (f(r), f(g), f(b))
}

pub fn hsv(h: f64, s: f64, v: f64) -> Rgb {
    let c = v * s;
    let x = c * (1.0 - ((h / 60.0) % 2.0 - 1.0).abs());
    let m = v - c;
    let (r, g, b) = match h as u32 {
        0..=59 => (c, x, 0.0),
        60..=119 => (x, c, 0.0),
        120..=179 => (0.0, c, x),
        180..=239 => (0.0, x, c),
        240..=299 => (x, 0.0, c),
        _ => (c, 0.0, x),
    };
    let q = |t: f64| ((t + m) * 255.0 + 0.5) as u8;
    (q(r), q(g), q(b))
}

pub fn to_hex((r, g, b): Rgb) -> String {
    format!("{r:02x}{g:02x}{b:02x}")
}
