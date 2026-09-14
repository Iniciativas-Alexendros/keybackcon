use std::fs;
use std::io;
use std::path::PathBuf;
use std::time::{Duration, Instant};

use crate::color::{hsv, scale};
use crate::lamp::Lamp;
use crate::state;

unsafe extern "C" {
    fn kill(pid: i32, sig: i32) -> i32;
}

const SIGTERM: i32 = 15;

pub fn pid_file() -> PathBuf {
    let base = std::env::var("XDG_RUNTIME_DIR").unwrap_or_else(|_| "/tmp".into());
    PathBuf::from(base).join("keybackcon/animation.pid")
}

fn legacy_pid_files() -> Vec<PathBuf> {
    let base = std::env::var("XDG_RUNTIME_DIR").unwrap_or_else(|_| "/tmp".into());
    vec![
        PathBuf::from(&base).join("kbd-rgb/anim.pid"),
        PathBuf::from(&base).join("keybackcon/anim.pid"),
    ]
}

fn pid_alive_at(path: &PathBuf) -> Option<i32> {
    let pid: i32 = fs::read_to_string(path).ok()?.trim().parse().ok()?;
    if pid <= 0 {
        return None;
    }
    if unsafe { kill(pid, 0) } != 0 {
        let _ = fs::remove_file(path);
        return None;
    }
    let cmd = fs::read_to_string(format!("/proc/{pid}/cmdline")).unwrap_or_default();
    if cmd.contains("keybackcon") || cmd.contains("kbd-rgb") {
        Some(pid)
    } else {
        let _ = fs::remove_file(path);
        None
    }
}

pub fn animation_pid_alive() -> Option<i32> {
    if let Some(pid) = pid_alive_at(&pid_file()) {
        return Some(pid);
    }
    for legacy in legacy_pid_files() {
        if let Some(pid) = pid_alive_at(&legacy) {
            return Some(pid);
        }
    }
    None
}

pub fn stop_animation() -> bool {
    let me = std::process::id() as i32;
    let pid = match animation_pid_alive() {
        Some(p) if p != me => p,
        _ => return false,
    };
    unsafe {
        kill(pid, SIGTERM);
    }
    for _ in 0..20 {
        if unsafe { kill(pid, 0) } != 0 {
            break;
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    let _ = fs::remove_file(pid_file());
    for legacy in legacy_pid_files() {
        let _ = fs::remove_file(legacy);
    }
    true
}

pub fn run_animation(mode: &str, fps: u64) -> io::Result<()> {
    let lamp = Lamp::open()?;
    lamp.autonomous(false)?;
    stop_animation();
    if let Some(d) = pid_file().parent() {
        let _ = fs::create_dir_all(d);
    }
    let _ = fs::write(pid_file(), std::process::id().to_string());
    let dt = Duration::from_micros(1_000_000 / fps.clamp(1, 240));
    let t0 = Instant::now();
    let (mut base, mut pct) = state::load_state();
    let mut refreshed = Instant::now();
    loop {
        if refreshed.elapsed() >= Duration::from_millis(500) {
            let (b, p) = state::load_state();
            base = b;
            pct = p;
            refreshed = Instant::now();
        }
        let t = t0.elapsed().as_secs_f64();
        let c = match mode {
            "rainbow" => scale(hsv((t * 45.0) % 360.0, 1.0, 1.0), pct),
            _ => {
                let k = (1.0 - (t * std::f64::consts::TAU / 4.0).cos()) / 2.0;
                let factor = (8.0 + k * 92.0) * (pct as f64 / 100.0);
                scale(base, factor.clamp(0.0, 100.0) as u32)
            }
        };
        lamp.color(c)?;
        std::thread::sleep(dt);
    }
}
