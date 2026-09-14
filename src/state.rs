//! Estado persistente (color base y porcentaje de brillo) en
//! `$XDG_STATE_HOME/keybackcon/state`, con lectura heredada de
//! `kbd-rgb/state`.

use std::fs;
use std::io;
use std::path::PathBuf;

use crate::color::{self, Rgb};
use crate::lamp::Lamp;

/// Ruta del estado nuevo (`$XDG_STATE_HOME/keybackcon/state`, o bajo
/// `~/.local/state`).
pub fn state_file() -> PathBuf {
    let base = std::env::var("XDG_STATE_HOME").unwrap_or_else(|_| {
        format!(
            "{}/.local/state",
            std::env::var("HOME").unwrap_or_else(|_| "/tmp".into())
        )
    });
    PathBuf::from(base).join("keybackcon/state")
}

fn legacy_state_file() -> PathBuf {
    let base = std::env::var("XDG_STATE_HOME").unwrap_or_else(|_| {
        format!(
            "{}/.local/state",
            std::env::var("HOME").unwrap_or_else(|_| "/tmp".into())
        )
    });
    PathBuf::from(base).join("kbd-rgb/state")
}

/// Carga `(color base, pct)` con lectura heredada de `kbd-rgb/state`;
/// valores por defecto: blanco y 100.
pub fn load_state() -> (Rgb, u32) {
    let raw = fs::read_to_string(state_file())
        .or_else(|_| fs::read_to_string(legacy_state_file()))
        .unwrap_or_default();
    let mut it = raw.split_whitespace();
    let c = it
        .next()
        .and_then(|s| color::parse_color(s).ok())
        .unwrap_or((255, 255, 255));
    let p = it
        .next()
        .and_then(|s| s.parse().ok())
        .unwrap_or(100u32)
        .clamp(0, 100);
    (c, p)
}

/// Persiste color base y porcentaje como `<hex> <pct>`.
pub fn save_state(rgb: Rgb, pct: u32) {
    let p = state_file();
    if let Some(d) = p.parent() {
        let _ = fs::create_dir_all(d);
    }
    let _ = fs::write(p, format!("{} {pct}\n", color::to_hex(rgb)));
}

/// Desactiva autónomos, escribe el color escalado y guarda el estado.
pub fn apply(l: &mut Lamp, base: Rgb, pct: u32) -> io::Result<()> {
    l.autonomous(false)?;
    l.color(color::scale(base, pct))?;
    save_state(base, pct);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn state_migra_desde_legado() {
        let _env = crate::TEST_ENV_LOCK
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        let tmp = std::env::temp_dir().join(format!("keybackcon-state-{}", std::process::id()));
        let _ = fs::remove_dir_all(&tmp);
        fs::create_dir_all(tmp.join("kbd-rgb")).unwrap();
        fs::write(tmp.join("kbd-rgb/state"), "ff7800 60\n").unwrap();
        // SAFETY: `TEST_ENV_LOCK` serializa todos los accesos al entorno de los
        // tests; este hilo tiene acceso exclusivo mientras dura la prueba.
        unsafe {
            std::env::set_var("XDG_STATE_HOME", &tmp);
        }
        let (c, p) = load_state();
        assert_eq!((c, p), ((255, 120, 0), 60));
        let _ = fs::remove_dir_all(&tmp);
        // SAFETY: el mismo acceso exclusivo del bloque anterior sigue vigente.
        unsafe {
            std::env::remove_var("XDG_STATE_HOME");
        }
    }
}
