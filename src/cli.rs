//! Modelo estructurado de comandos y despacho del CLI.
//!
//! `parse` valida los argumentos y `run` despacha a los `cmd_*`; la ayuda, los
//! mensajes y los códigos de salida (2 uso, 1 error) se mantienen estables.
//! Todo comando que cambia el color detiene antes la animación para tener una
//! sola escritora.

use std::io::{self, Write};

use crate::animation;
use crate::color::{self, Rgb};
use crate::error::Error;
use crate::lamp::Lamp;
use crate::state;

/// Nombre del binario usado en la ayuda y en los errores.
pub const BIN: &str = "keybackcon";

/// Comando ya validado que `run` sabe ejecutar.
pub enum Command {
    /// Muestra la ayuda y termina con el código de uso (2).
    Help,
    /// Imprime nombre y versión.
    Version,
    /// Muestra dispositivo, lámparas, tipo y estado.
    Info,
    /// Fija el color base y lo persiste con el brillo actual.
    Set(Rgb),
    /// Apaga la zona sin perder el estado.
    Off,
    /// Ajusta el porcentaje de brillo y reaplica el color.
    Brightness(BrightnessChange),
    /// Activa o desactiva los efectos autónomos del firmware.
    FirmwareEffects(bool),
    /// Ejecuta una animación hasta que llega una señal.
    Animation {
        /// Modo de animación.
        mode: Mode,
        /// Fotogramas por segundo, ya acotados a 1–240.
        fps: u64,
    },
    /// Detiene la animación y restaura el color base.
    Stop,
}

/// Modo de animación en primer plano.
pub enum Mode {
    /// Respiración suave sobre el color base.
    Breathe,
    /// Ciclo de arcoíris completo.
    Rainbow,
}

impl Mode {
    fn as_str(&self) -> &'static str {
        match self {
            Mode::Breathe => "breathe",
            Mode::Rainbow => "rainbow",
        }
    }
}

/// Cambio pedido para el porcentaje de brillo.
pub enum BrightnessChange {
    /// Fija el porcentaje absoluto (acotado luego a 0–100).
    Set(u32),
    /// Suma `N` al porcentaje actual.
    Up(u32),
    /// Resta `N` al porcentaje actual.
    Down(u32),
}

/// Imprime la ayuda en stderr y sale con código 2.
pub fn usage() -> ! {
    eprintln!(
        "uso: {BIN} <comando>\n\
         \n  Keyboard Backlight Controls — una zona, instancia única de animación\n\
         \n  info                     información del dispositivo (nº de lámparas, ruta hidraw)\n  set <color>              asigna color — hex 'ff6400' o nombre de predefinido\n  off                      apaga (el estado se conserva)\n  brightness <+N|-N|N>     brillo — escala RGB, persistente (alias: bright)\n  firmware-effects on|off  efectos del firmware (alias: auto)\n  animation <breathe|rainbow> [--fps N]\n                           animación en primer plano; instancia única (alias: anim)\n  stop                     detiene la animación y restaura el color base\n  --help, -h               muestra esta ayuda\n  --version, -V            muestra la versión\n\
         \npredefinidos: {}",
        crate::color::PRESETS
            .iter()
            .map(|(n, _)| *n)
            .collect::<Vec<_>>()
            .join(", ")
    );
    std::process::exit(2)
}

/// Valida `args` (sin el nombre del binario) y construye el comando.
pub fn parse(args: &[String]) -> Result<Command, Error> {
    match args.first().map(String::as_str) {
        Some("--help" | "-h" | "help") => Ok(Command::Help),
        Some("--version" | "-V") => Ok(Command::Version),
        Some("info") => Ok(Command::Info),
        Some("set") => {
            let s = args.get(1).map_or("", String::as_str);
            let c = color::parse_color(s).map_err(|e| Error::Invalid(e.to_string()))?;
            Ok(Command::Set(c))
        }
        Some("off") => Ok(Command::Off),
        Some("brightness" | "bright") => {
            let a = args.get(1).map_or("", String::as_str);
            Ok(Command::Brightness(parse_brightness(a)?))
        }
        Some("firmware-effects" | "auto") => Ok(Command::FirmwareEffects(matches!(
            args.get(1).map(String::as_str),
            Some("on")
        ))),
        Some("animation" | "anim") => parse_animation(args),
        Some("stop") => Ok(Command::Stop),
        _ => Err(Error::Usage),
    }
}

fn parse_brightness(a: &str) -> Result<BrightnessChange, Error> {
    if let Some(d) = a.strip_prefix('+') {
        return Ok(BrightnessChange::Up(d.parse().unwrap_or(10)));
    }
    if let Some(d) = a.strip_prefix('-') {
        return Ok(BrightnessChange::Down(d.parse().unwrap_or(10)));
    }
    a.parse()
        .map(BrightnessChange::Set)
        .map_err(|_| Error::Invalid("el brillo debe ser un número".into()))
}

fn parse_animation(args: &[String]) -> Result<Command, Error> {
    let mode = args.get(1).cloned().unwrap_or_else(|| "breathe".into());
    let mode = match mode.as_str() {
        "breathe" => Mode::Breathe,
        "rainbow" => Mode::Rainbow,
        _ => {
            return Err(Error::Invalid(format!(
                "modo desconocido: '{mode}' (válidos: breathe, rainbow)"
            )))
        }
    };
    let fps: u64 = args
        .iter()
        .position(|a| a == "--fps")
        .and_then(|i| args.get(i + 1))
        .and_then(|s| s.parse().ok())
        .unwrap_or(60)
        .clamp(1, 240);
    Ok(Command::Animation { mode, fps })
}

/// Lee los argumentos reales y ejecuta el comando resultante.
pub fn run() -> Result<(), Error> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    match parse(&args)? {
        Command::Help => usage(),
        Command::Version => {
            println!("{} {}", BIN, env!("CARGO_PKG_VERSION"));
            Ok(())
        }
        Command::Info => cmd_info(),
        Command::Set(c) => cmd_set(c),
        Command::Off => cmd_off(),
        Command::Brightness(change) => cmd_brightness(change),
        Command::FirmwareEffects(on) => cmd_firmware_effects(on),
        Command::Animation { mode, fps } => cmd_animation(mode, fps),
        Command::Stop => cmd_stop(),
    }
}

fn cmd_info() -> Result<(), Error> {
    let (base, pct) = state::load_state();
    let path = Lamp::find()?;
    let mut l = Lamp::open()?;
    let (count, kind) = l.attrs()?;
    println!("dispositivo : {}", path.display());
    println!("nº lámparas : {count}");
    println!("tipo        : {kind} (lo que declara el firmware; en este modelo es engañoso)");
    println!(
        "estado      : #{:02x}{:02x}{:02x} @ %{pct}",
        base.0, base.1, base.2
    );
    Ok(())
}

fn cmd_set(c: Rgb) -> Result<(), Error> {
    let (_, pct) = state::load_state();
    animation::stop_animation();
    state::apply(&mut Lamp::open()?, c, pct)?;
    Ok(())
}

fn cmd_off() -> Result<(), Error> {
    animation::stop_animation();
    let mut l = Lamp::open()?;
    l.autonomous(false)?;
    l.color((0, 0, 0))?;
    Ok(())
}

#[allow(clippy::needless_pass_by_value)]
fn cmd_brightness(change: BrightnessChange) -> Result<(), Error> {
    let (base, pct) = state::load_state();
    let new = match change {
        BrightnessChange::Set(n) => n,
        BrightnessChange::Up(n) => pct.saturating_add(n),
        BrightnessChange::Down(n) => pct.saturating_sub(n),
    }
    .clamp(0, 100);
    animation::stop_animation();
    state::apply(&mut Lamp::open()?, base, new)?;
    println!("brillo: %{new}");
    Ok(())
}

fn cmd_firmware_effects(on: bool) -> Result<(), Error> {
    animation::stop_animation();
    Lamp::open()?.autonomous(on)?;
    Ok(())
}

#[allow(clippy::needless_pass_by_value)]
fn cmd_animation(mode: Mode, fps: u64) -> Result<(), Error> {
    animation::run_animation(mode.as_str(), fps)?;
    Ok(())
}

fn cmd_stop() -> Result<(), Error> {
    let (base, pct) = state::load_state();
    if animation::stop_animation() {
        state::apply(&mut Lamp::open()?, base, pct)?;
        println!("animación detenida; color base restaurado");
    } else {
        println!("no hay ninguna animación en marcha");
    }
    Ok(())
}

/// Punto de entrada: traduce el resultado a stderr y al código de salida
/// (2 para uso, 1 para el resto).
pub fn main() {
    match run() {
        Ok(()) => {}
        Err(Error::Usage) => usage(),
        Err(e) => {
            let _ = writeln!(io::stderr(), "{BIN}: {e}");
            std::process::exit(1);
        }
    }
}
