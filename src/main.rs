mod animation;
mod cli;
mod color;
mod lamp;
mod state;

fn main() {
    cli::main();
}

#[cfg(test)]
mod tests {
    use super::animation;
    use super::color::{hsv, parse_color, scale};
    use std::fs;
    use std::path::PathBuf;
    use std::process::Command;

    #[test]
    fn parse_acepta_presets_hex_y_almohadilla() {
        assert_eq!(parse_color("red").unwrap(), (255, 0, 0));
        assert_eq!(parse_color(" Cyan ").unwrap(), (0, 255, 255));
        assert_eq!(parse_color("#red").unwrap(), (255, 0, 0));
        assert_eq!(parse_color("ff6400").unwrap(), (255, 100, 0));
        assert_eq!(parse_color("FF6400").unwrap(), (255, 100, 0));
        assert_eq!(parse_color("#FF6400").unwrap(), (255, 100, 0));
        assert!(parse_color("fucsia").is_err());
        assert!(parse_color("fff").is_err());
        assert!(parse_color("").is_err());
    }

    #[test]
    fn scale_redondea_y_limita() {
        assert_eq!(scale((255, 255, 255), 100), (255, 255, 255));
        assert_eq!(scale((255, 120, 0), 50), (128, 60, 0));
        assert_eq!(scale((255, 255, 255), 0), (0, 0, 0));
        assert_eq!(scale((1, 1, 1), 50), (1, 1, 1));
    }

    #[test]
    fn hsv_primarios() {
        assert_eq!(hsv(0.0, 1.0, 1.0), (255, 0, 0));
        assert_eq!(hsv(120.0, 1.0, 1.0), (0, 255, 0));
        assert_eq!(hsv(240.0, 1.0, 1.0), (0, 0, 255));
        assert_eq!(hsv(0.0, 0.0, 1.0), (255, 255, 255));
    }

    fn tmp_runtime() -> PathBuf {
        let tmp = std::env::temp_dir().join(format!("keybackcon-test-{}", std::process::id()));
        let _ = fs::remove_dir_all(&tmp);
        fs::create_dir_all(tmp.join("keybackcon")).unwrap();
        unsafe {
            std::env::set_var("XDG_RUNTIME_DIR", &tmp);
        }
        tmp
    }

    #[test]
    fn pidfile_obsoleto_no_mata_nada() {
        let tmp = tmp_runtime();
        fs::write(tmp.join("keybackcon/animation.pid"), "2147483647").unwrap();
        assert!(!animation::stop_animation());
        assert!(!tmp.join("keybackcon/animation.pid").exists());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn stop_animation_mata_proceso_vivo() {
        let tmp = tmp_runtime();
        let mut child = Command::new("bash")
            .args(["-c", "exec -a keybackcon-test sleep 60"])
            .spawn()
            .unwrap();
        fs::write(tmp.join("keybackcon/animation.pid"), child.id().to_string()).unwrap();
        assert!(animation::stop_animation());
        let _ = child.wait();
        assert!(!tmp.join("keybackcon/animation.pid").exists());
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn state_migra_desde_legado() {
        let tmp = std::env::temp_dir().join(format!("keybackcon-state-{}", std::process::id()));
        let _ = fs::remove_dir_all(&tmp);
        fs::create_dir_all(tmp.join("kbd-rgb")).unwrap();
        fs::write(tmp.join("kbd-rgb/state"), "ff7800 60\n").unwrap();
        unsafe {
            std::env::set_var("XDG_STATE_HOME", &tmp);
        }
        let (c, p) = super::state::load_state();
        assert_eq!((c, p), ((255, 120, 0), 60));
        let _ = fs::remove_dir_all(&tmp);
        unsafe {
            std::env::remove_var("XDG_STATE_HOME");
        }
    }
}
