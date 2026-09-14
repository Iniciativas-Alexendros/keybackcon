use std::fs;
use std::io;
use std::path::PathBuf;

use crate::color::{self, Rgb};
use crate::lamp::Lamp;

fn base_dir(var: &str, fallback: String) -> PathBuf {
    PathBuf::from(std::env::var(var).unwrap_or(fallback))
}

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

pub fn save_state(rgb: Rgb, pct: u32) {
    let p = state_file();
    if let Some(d) = p.parent() {
        let _ = fs::create_dir_all(d);
    }
    let _ = fs::write(p, format!("{} {pct}\n", color::to_hex(rgb)));
}

pub fn apply(l: &Lamp, base: Rgb, pct: u32) -> io::Result<()> {
    l.autonomous(false)?;
    l.color(color::scale(base, pct))?;
    save_state(base, pct);
    Ok(())
}

#[allow(dead_code)]
pub fn _base_dir_for_test() -> PathBuf {
    base_dir("XDG_STATE_HOME", "/tmp".into())
}
