//! Estado persistente (color base y porcentaje de brillo) en
//! `$XDG_STATE_HOME/keybackcon/state`, con lectura heredada de
//! `kbd-rgb/state`.

use std::fs;
use std::io;
use std::path::PathBuf;

use crate::color::{self, Rgb};
use crate::lamp::Lamp;

fn state_base() -> String {
    std::env::var("XDG_STATE_HOME").unwrap_or_else(|_| {
        format!(
            "{}/.local/state",
            std::env::var("HOME").unwrap_or_else(|_| "/tmp".into())
        )
    })
}

/// Ruta del estado nuevo (`$XDG_STATE_HOME/keybackcon/state`, o bajo
/// `~/.local/state`).
pub fn state_file() -> PathBuf {
    PathBuf::from(state_base()).join("keybackcon/state")
}

fn legacy_state_file() -> PathBuf {
    PathBuf::from(state_base()).join("kbd-rgb/state")
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
///
/// La escritura es atómica (fichero temporal + `rename` en el mismo
/// directorio) para no dejar un estado a medias si el proceso muere a mitad
/// del guardado; los errores se avisan en stderr pero no abortan el comando.
pub fn save_state(rgb: Rgb, pct: u32) {
    let p = state_file();
    let Some(d) = p.parent() else {
        return;
    };
    if let Err(e) = fs::create_dir_all(d) {
        eprintln!("aviso: no se pudo crear {}: {e}", d.display());
        return;
    }
    let tmp = d.join(format!(".state-{}.tmp", std::process::id()));
    let content = format!("{} {pct}\n", color::to_hex(rgb));
    if let Err(e) = fs::write(&tmp, &content).and_then(|()| fs::rename(&tmp, &p)) {
        let _ = fs::remove_file(&tmp);
        eprintln!(
            "aviso: no se pudo guardar el estado en {}: {e}",
            p.display()
        );
    }
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

    #[test]
    fn save_state_es_atómico_y_load_state_lee_lo_guardado() {
        let _env = crate::TEST_ENV_LOCK
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        let tmp =
            std::env::temp_dir().join(format!("keybackcon-state-save-{}", std::process::id()));
        let _ = fs::remove_dir_all(&tmp);
        // SAFETY: `TEST_ENV_LOCK` serializa todos los accesos al entorno de los
        // tests; este hilo tiene acceso exclusivo mientras dura la prueba.
        unsafe {
            std::env::set_var("XDG_STATE_HOME", &tmp);
        }
        save_state((255, 120, 0), 60);
        assert_eq!(load_state(), ((255, 120, 0), 60));
        let entries: Vec<String> = fs::read_dir(tmp.join("keybackcon"))
            .unwrap()
            .map(|e| e.unwrap().file_name().to_string_lossy().into_owned())
            .collect();
        assert_eq!(entries, vec!["state"], "no debe quedar fichero temporal");
        let _ = fs::remove_dir_all(&tmp);
        // SAFETY: el mismo acceso exclusivo del bloque anterior sigue vigente.
        unsafe {
            std::env::remove_var("XDG_STATE_HOME");
        }
    }
}
