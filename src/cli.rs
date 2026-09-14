use std::io::{self, Write};

use crate::animation;
use crate::color::{parse_color, PRESETS};
use crate::lamp::Lamp;
use crate::state;

pub const BIN: &str = "keybackcon";

pub fn usage() -> ! {
    eprintln!(
        "uso: {BIN} <comando>\n\
         \n  Keyboard Backlight Controls — una zona, instancia única de animación\n\
         \n  info                     información del dispositivo (nº de lámparas, ruta hidraw)\n  set <color>              asigna color — hex 'ff6400' o nombre de predefinido\n  off                      apaga (el estado se conserva)\n  brightness <+N|-N|N>     brillo — escala RGB, persistente (alias: bright)\n  firmware-effects on|off  efectos del firmware (alias: auto)\n  animation <breathe|rainbow> [--fps N]\n                           animación en primer plano; instancia única (alias: anim)\n  stop                     detiene la animación y restaura el color base\n  --help, -h               muestra esta ayuda\n  --version, -V            muestra la versión\n\
         \npredefinidos: {}",
        PRESETS
            .iter()
            .map(|(n, _)| *n)
            .collect::<Vec<_>>()
            .join(", ")
    );
    std::process::exit(2)
}

pub fn run() -> io::Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        usage();
    }
    let (base, pct) = state::load_state();
    match args[0].as_str() {
        "--help" | "-h" | "help" => usage(),
        "--version" | "-V" => {
            println!("{} {}", BIN, env!("CARGO_PKG_VERSION"));
            return Ok(());
        }
        "info" => {
            let path = Lamp::find()?;
            let l = Lamp::open()?;
            let (count, kind) = l.attrs()?;
            println!("dispositivo : {}", path.display());
            println!("nº lámparas : {count}");
            println!(
                "tipo        : {kind} (lo que declara el firmware; en este modelo es engañoso)"
            );
            println!(
                "estado      : #{:02x}{:02x}{:02x} @ %{pct}",
                base.0, base.1, base.2
            );
        }
        "set" => {
            let c = parse_color(args.get(1).unwrap_or(&String::new()))
                .map_err(|e| io::Error::new(io::ErrorKind::InvalidInput, e))?;
            animation::stop_animation();
            state::apply(&Lamp::open()?, c, pct)?;
        }
        "off" => {
            animation::stop_animation();
            let l = Lamp::open()?;
            l.autonomous(false)?;
            l.color((0, 0, 0))?;
        }
        "brightness" | "bright" => {
            let a = args.get(1).map(String::as_str).unwrap_or("");
            let new = if let Some(d) = a.strip_prefix('+') {
                pct.saturating_add(d.parse::<u32>().unwrap_or(10))
            } else if let Some(d) = a.strip_prefix('-') {
                pct.saturating_sub(d.parse::<u32>().unwrap_or(10))
            } else {
                a.parse::<u32>().map_err(|_| {
                    io::Error::new(io::ErrorKind::InvalidInput, "el brillo debe ser un número")
                })?
            }
            .clamp(0, 100);
            animation::stop_animation();
            state::apply(&Lamp::open()?, base, new)?;
            println!("brillo: %{new}");
        }
        "firmware-effects" | "auto" => {
            let on = matches!(args.get(1).map(String::as_str), Some("on"));
            animation::stop_animation();
            Lamp::open()?.autonomous(on)?;
        }
        "animation" | "anim" => {
            let mode = args.get(1).cloned().unwrap_or_else(|| "breathe".into());
            if mode != "breathe" && mode != "rainbow" {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidInput,
                    format!("modo desconocido: '{mode}' (válidos: breathe, rainbow)"),
                ));
            }
            let fps: u64 = args
                .iter()
                .position(|a| a == "--fps")
                .and_then(|i| args.get(i + 1))
                .and_then(|s| s.parse().ok())
                .unwrap_or(60)
                .clamp(1, 240);
            animation::run_animation(&mode, fps)?;
        }
        "stop" => {
            if animation::stop_animation() {
                state::apply(&Lamp::open()?, base, pct)?;
                println!("animación detenida; color base restaurado");
            } else {
                println!("no hay ninguna animación en marcha");
            }
        }
        _ => usage(),
    }
    Ok(())
}

pub fn main() {
    if let Err(e) = run() {
        let _ = writeln!(io::stderr(), "{BIN}: {e}");
        std::process::exit(1);
    }
}
