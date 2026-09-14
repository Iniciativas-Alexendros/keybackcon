//! Animación en primer plano (`breathe`/`rainbow`), instancia única y parada
//! limpia.
//!
//! El pidfile (`$XDG_RUNTIME_DIR/keybackcon/animation.pid`, con lectura de las
//! rutas heredadas `kbd-rgb/anim.pid` y `keybackcon/anim.pid`) se reserva con
//! `create_new` y se valida con `kill(pid, 0)` más `/proc/<pid>/cmdline`.
//! `SIGINT`/`SIGTERM` solo marcan un `AtomicBool`; al salir se restaura el
//! color base y se borra el pidfile propio. Si el teclado se desconecta, la
//! animación termina con `DEVICE_GONE_MSG`.

use std::fs;
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::{Duration, Instant};

use crate::color::{hsv, scale};
use crate::lamp::{is_device_gone, Lamp, DEVICE_GONE_MSG};
use crate::state;

// SAFETY: `signal` y `kill` son funciones de libc con ABI estable; el manejador
// registrado solo escribe en un AtomicBool (async-signal-safe) y los pids que
// recibe `kill` se validan contra /proc antes de señalizarlos.
unsafe extern "C" {
    fn signal(signum: i32, handler: extern "C" fn(i32)) -> usize;
    fn kill(pid: i32, sig: i32) -> i32;
}

const SIGINT: i32 = 2;
const SIGTERM: i32 = 15;
const MAX_CLAIM_ATTEMPTS: u32 = 3;

static STOP: AtomicBool = AtomicBool::new(false);

extern "C" fn on_stop_signal(_sig: i32) {
    STOP.store(true, Ordering::SeqCst);
}

fn install_signal_handlers() {
    // SAFETY: el manejador `on_stop_signal` es async-signal-safe (solo un store
    // atómico); se instala para los dos signos de parada y el proceso termina
    // sin restaurar los manejadores previos.
    unsafe {
        signal(SIGINT, on_stop_signal);
        signal(SIGTERM, on_stop_signal);
    }
}

/// Ruta del pidfile de la animación en `$XDG_RUNTIME_DIR` (o `/tmp`).
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

fn read_pid(path: &Path) -> Option<i32> {
    fs::read_to_string(path)
        .ok()?
        .trim()
        .parse()
        .ok()
        .filter(|pid: &i32| *pid > 0)
}

fn pid_alive_at(path: &Path) -> Option<i32> {
    let Some(pid) = read_pid(path) else {
        // Contenido vacío, no numérico o pid inválido: obsoleto.
        let _ = fs::remove_file(path);
        return None;
    };
    // SAFETY: `kill` con señal 0 no envía nada; solo consulta si el pid existe.
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

/// Devuelve el pid de una animación viva validada, incluida una ruta heredada.
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

/// Señaliza SIGTERM a la animación viva y espera hasta 1 s; `true` si había
/// una animación validada.
pub fn stop_animation() -> bool {
    let me = std::process::id().cast_signed();
    let pid = match animation_pid_alive() {
        Some(p) if p != me => p,
        _ => return false,
    };
    // SAFETY: `pid` acaba de validarse como un keybackcon vivo distinto de
    // este proceso; SIGTERM es la señal de parada pedida.
    unsafe {
        kill(pid, SIGTERM);
    }
    for _ in 0..20 {
        // SAFETY: consulta de existencia del mismo pid validado.
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

fn pid_owned_by(path: &Path, pid: i32) -> bool {
    read_pid(path) == Some(pid)
}

fn remove_own_pidfile(path: &Path, own: i32) {
    if pid_owned_by(path, own) {
        let _ = fs::remove_file(path);
    }
}

fn claim_pidfile(path: &Path, own: i32) -> io::Result<()> {
    for attempt in 0..MAX_CLAIM_ATTEMPTS {
        match fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
        {
            Ok(mut file) => {
                if let Err(e) = writeln!(file, "{own}") {
                    let _ = fs::remove_file(path);
                    return Err(io::Error::new(
                        e.kind(),
                        format!("no se pudo escribir {}: {e}", path.display()),
                    ));
                }
                return Ok(());
            }
            Err(e) if e.kind() == io::ErrorKind::AlreadyExists => {
                if let Some(pid) = pid_alive_at(path) {
                    return Err(io::Error::new(
                        io::ErrorKind::AlreadyExists,
                        format!("ya hay una animación en marcha (pid {pid})"),
                    ));
                }
                if attempt + 1 == MAX_CLAIM_ATTEMPTS {
                    break;
                }
            }
            Err(e) => {
                return Err(io::Error::new(
                    e.kind(),
                    format!("no se pudo crear {}: {e}", path.display()),
                ));
            }
        }
    }
    Err(io::Error::new(
        io::ErrorKind::AlreadyExists,
        format!(
            "no se pudo reservar {} tras {MAX_CLAIM_ATTEMPTS} intentos",
            path.display()
        ),
    ))
}

/// Ejecuta `mode` (`breathe`/`rainbow`) a `fps` (1–240) hasta que llega
/// SIGINT/SIGTERM o el teclado se desconecta.
pub fn run_animation(mode: &str, fps: u64) -> io::Result<()> {
    let mut lamp = Lamp::open()?;
    lamp.autonomous(false)?;
    stop_animation();

    let pf = pid_file();
    if let Some(d) = pf.parent() {
        fs::create_dir_all(d).map_err(|e| {
            io::Error::new(e.kind(), format!("no se pudo crear {}: {e}", d.display()))
        })?;
    }
    let own = std::process::id().cast_signed();
    claim_pidfile(&pf, own)?;
    STOP.store(false, Ordering::SeqCst);
    install_signal_handlers();

    let dt = Duration::from_micros(1_000_000 / fps.clamp(1, 240));
    let t0 = Instant::now();
    let (mut base, mut pct) = state::load_state();
    let mut refreshed = Instant::now();
    loop {
        if STOP.load(Ordering::SeqCst) {
            let (b, p) = state::load_state();
            let _ = lamp.color(scale(b, p));
            remove_own_pidfile(&pf, own);
            return Ok(());
        }
        if refreshed.elapsed() >= Duration::from_millis(500) {
            let (b, p) = state::load_state();
            base = b;
            pct = p;
            refreshed = Instant::now();
        }
        let t = t0.elapsed().as_secs_f64();
        let c = if mode == "rainbow" {
            scale(hsv((t * 45.0) % 360.0, 1.0, 1.0), pct)
        } else {
            let k = (1.0 - (t * std::f64::consts::TAU / 4.0).cos()) / 2.0;
            let factor = (8.0 + k * 92.0) * (f64::from(pct) / 100.0);
            #[allow(clippy::cast_possible_truncation, clippy::cast_sign_loss)]
            let pct_factor = factor.clamp(0.0, 100.0) as u32;
            scale(base, pct_factor)
        };
        if let Err(e) = lamp.color(c) {
            if is_device_gone(&e) {
                remove_own_pidfile(&pf, own);
                return Err(io::Error::new(e.kind(), DEVICE_GONE_MSG));
            }
            return Err(e);
        }
        std::thread::sleep(dt);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::process::CommandExt;
    use std::process::{Child, Command};
    use std::sync::MutexGuard;

    fn tmp_dir(tag: &str) -> (PathBuf, MutexGuard<'static, ()>) {
        let guard = crate::TEST_ENV_LOCK
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        let dir =
            std::env::temp_dir().join(format!("keybackcon-anim-{}-{tag}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        (dir, guard)
    }

    fn live_keybackcon_child() -> Child {
        // `spawn` no vuelve hasta que el hijo ha hecho exec, y arg0 garantiza
        // que /proc/<pid>/cmdline contiene "keybackcon" de inmediato.
        Command::new("sleep")
            .arg0("keybackcon-test")
            .arg("60")
            .spawn()
            .unwrap()
    }

    fn tmp_runtime(tag: &str) -> (PathBuf, MutexGuard<'static, ()>) {
        let guard = crate::TEST_ENV_LOCK
            .lock()
            .unwrap_or_else(std::sync::PoisonError::into_inner);
        let dir =
            std::env::temp_dir().join(format!("keybackcon-runtime-{}-{tag}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(dir.join("keybackcon")).unwrap();
        // SAFETY: `TEST_ENV_LOCK` serializa todos los accesos al entorno de los
        // tests; ningún otro test lee ni escribe variables mientras dura esto.
        unsafe {
            std::env::set_var("XDG_RUNTIME_DIR", &dir);
        }
        (dir, guard)
    }

    #[test]
    fn propiedad_del_pidfile_propio_y_ajeno() {
        let (dir, _env) = tmp_dir("propiedad");
        let p = dir.join("animation.pid");
        fs::write(&p, "4242").unwrap();
        assert!(pid_owned_by(&p, 4242));
        assert!(!pid_owned_by(&p, 4243));
        fs::write(&p, "no-numero").unwrap();
        assert!(!pid_owned_by(&p, 4243));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn limpieza_borra_solo_el_pidfile_propio() {
        let (dir, _env) = tmp_dir("limpieza");
        let p = dir.join("animation.pid");
        fs::write(&p, "4242").unwrap();
        remove_own_pidfile(&p, 9999);
        assert!(p.exists(), "no debe borrar un pidfile ajeno");
        remove_own_pidfile(&p, 4242);
        assert!(!p.exists(), "debe borrar su propio pidfile");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn claim_crea_el_pidfile_en_exclusiva() {
        let (dir, _env) = tmp_dir("claim");
        let p = dir.join("animation.pid");
        claim_pidfile(&p, 7777).unwrap();
        assert_eq!(fs::read_to_string(&p).unwrap().trim(), "7777");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn claim_falla_si_hay_una_animacion_viva() {
        let (dir, _env) = tmp_dir("claim-vivo");
        let p = dir.join("animation.pid");
        let mut child = live_keybackcon_child();
        let deadline = Instant::now() + Duration::from_secs(2);
        loop {
            let cmd =
                fs::read_to_string(format!("/proc/{}/cmdline", child.id())).unwrap_or_default();
            if cmd.contains("keybackcon") {
                break;
            }
            assert!(Instant::now() < deadline, "el hijo no llegó a ejecutarse");
            std::thread::sleep(Duration::from_millis(5));
        }
        fs::write(&p, child.id().to_string()).unwrap();
        let err = claim_pidfile(&p, 7777).unwrap_err();
        assert_eq!(err.kind(), io::ErrorKind::AlreadyExists);
        assert!(err.to_string().contains(&format!("pid {}", child.id())));
        let _ = child.kill();
        let _ = child.wait();
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn claim_reclama_un_pidfile_obsoleto() {
        let (dir, _env) = tmp_dir("claim-obsoleto");
        let p = dir.join("animation.pid");
        fs::write(&p, "2147483647").unwrap();
        claim_pidfile(&p, 7777).unwrap();
        assert_eq!(fs::read_to_string(&p).unwrap().trim(), "7777");
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn pidfile_obsoleto_no_mata_nada() {
        let (tmp, _env) = tmp_runtime("obsoleto");
        fs::write(tmp.join("keybackcon/animation.pid"), "2147483647").unwrap();
        assert!(!stop_animation());
        assert!(!tmp.join("keybackcon/animation.pid").exists());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn stop_animation_mata_proceso_vivo() {
        let (tmp, _env) = tmp_runtime("vivo");
        let mut child = live_keybackcon_child();
        let deadline = Instant::now() + Duration::from_secs(2);
        loop {
            let cmd =
                fs::read_to_string(format!("/proc/{}/cmdline", child.id())).unwrap_or_default();
            if cmd.contains("keybackcon") {
                break;
            }
            assert!(Instant::now() < deadline, "el hijo no llegó a ejecutarse");
            std::thread::sleep(Duration::from_millis(5));
        }
        fs::write(tmp.join("keybackcon/animation.pid"), child.id().to_string()).unwrap();
        assert!(stop_animation());
        let _ = child.wait();
        assert!(!tmp.join("keybackcon/animation.pid").exists());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn el_manejador_solo_marca_la_bandera_de_parada() {
        STOP.store(false, Ordering::SeqCst);
        assert!(!STOP.load(Ordering::SeqCst));
        on_stop_signal(SIGTERM);
        assert!(STOP.load(Ordering::SeqCst));
        on_stop_signal(SIGINT);
        assert!(STOP.load(Ordering::SeqCst));
        STOP.store(false, Ordering::SeqCst);
    }
}
