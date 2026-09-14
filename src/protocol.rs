//! Fuente única del protocolo HID `LampArray` en el cable: constantes,
//! construcción de informes y peticiones ioctl. `lamp.rs` solo consume.

use std::io;

use crate::color::Rgb;

/// Firma del descriptor de un `LampArray`: `Usage Page LampArray` (`0x05
/// 0x59`), `Usage LampArray` (`0x09 0x01`) y `Collection Application` (`0xA1
/// 0x01`). USB HID Usage Tables v1.4 §26.
pub const DEVICE_SIGNATURE: &[u8] = &[0x05, 0x59, 0x09, 0x01, 0xA1, 0x01];

/// Subruta sysfs del descriptor de informes del hidraw.
pub const REPORT_DESCRIPTOR_SUBPATH: &str = "device/report_descriptor";

/// ID del informe de atributos (`get_feature`).
pub const REPORT_ID_ATTRS: u8 = 1;
/// ID del informe de color por zona (`set_feature`).
pub const REPORT_ID_COLOR: u8 = 5;
/// ID del informe de efectos autónomos (`set_feature`).
pub const REPORT_ID_AUTONOMOUS: u8 = 6;

/// Longitud del informe de atributos que se solicita.
pub const ATTRS_REPORT_LEN: usize = 23;
/// Longitud mínima aceptada al parsear el informe de atributos.
pub const ATTRS_MIN_LEN: usize = 19;
/// Longitud del informe de color.
pub const COLOR_REPORT_LEN: usize = 10;

/// Offset de `LampCount` (u16 LE) en el informe de atributos.
pub const ATTRS_LAMP_COUNT_OFFSET: usize = 1;
/// Offset de `LampArrayKind` (u32 LE) en el informe de atributos.
pub const ATTRS_LAMP_KIND_OFFSET: usize = 15;

/// Nº de zonas del informe de color (el teclado expone una).
pub const COLOR_ZONE_COUNT: u8 = 1;
/// Intensidad máxima (último byte del informe de color).
pub const COLOR_INTENSITY_MAX: u8 = 0xff;

/// Byte de efectos autónomos activados.
pub const AUTONOMOUS_ON: u8 = 1;
/// Byte de efectos autónomos desactivados.
pub const AUTONOMOUS_OFF: u8 = 0;

/// Número de `HIDIOCGFEATURE` en `include/uapi/linux/hidraw.h`.
pub const HIDIOCGFEATURE_NR: u64 = 0x07;
/// Número de `HIDIOCSFEATURE` en `include/uapi/linux/hidraw.h`.
pub const HIDIOCSFEATURE_NR: u64 = 0x06;
/// Tipo ioctl `'H'` (hidraw).
pub const HID_IOCTL_TYPE: u64 = 0x48;
/// Bits de dirección `_IOC_WRITE | _IOC_READ` de `_IOWR`.
pub const HID_IOCTL_DIR: u64 = 0xC000_0000;

/// Codifica una petición `_IOWR` de HID con la longitud real del informe;
/// rechaza 0 y longitudes mayores que `u16::MAX`.
pub fn hid_ioctl_request(nr: u64, len: usize) -> io::Result<u64> {
    if len == 0 || len > u16::MAX as usize {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            format!("longitud de informe inválida: {len}"),
        ));
    }
    Ok(HID_IOCTL_DIR | ((len as u64) << 16) | (HID_IOCTL_TYPE << 8) | (nr & 0xff))
}

/// Extrae `LampCount` y `LampArrayKind` del informe de atributos.
pub(crate) fn parse_attrs(buf: &[u8]) -> io::Result<(u16, u32)> {
    if buf.len() < ATTRS_MIN_LEN {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            format!("informe de atributos demasiado corto: {} bytes", buf.len()),
        ));
    }
    Ok((
        u16::from_le_bytes([
            buf[ATTRS_LAMP_COUNT_OFFSET],
            buf[ATTRS_LAMP_COUNT_OFFSET + 1],
        ]),
        u32::from_le_bytes([
            buf[ATTRS_LAMP_KIND_OFFSET],
            buf[ATTRS_LAMP_KIND_OFFSET + 1],
            buf[ATTRS_LAMP_KIND_OFFSET + 2],
            buf[ATTRS_LAMP_KIND_OFFSET + 3],
        ]),
    ))
}

/// Informe de color para la zona completa `0..=count-1`.
pub(crate) fn color_report(count: u16, (r, g, b): Rgb) -> [u8; COLOR_REPORT_LEN] {
    let first = 0u16.to_le_bytes();
    let last = count.saturating_sub(1).to_le_bytes();
    [
        REPORT_ID_COLOR,
        COLOR_ZONE_COUNT,
        first[0],
        first[1],
        last[0],
        last[1],
        r,
        g,
        b,
        COLOR_INTENSITY_MAX,
    ]
}

/// Informe de efectos autónomos `[6, on]`.
pub(crate) fn autonomous_report(on: bool) -> [u8; 2] {
    [
        REPORT_ID_AUTONOMOUS,
        if on { AUTONOMOUS_ON } else { AUTONOMOUS_OFF },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Generador xorshift64 determinista: sustituye a `proptest` sin dependencias.
    struct Xorshift64(u64);

    impl Xorshift64 {
        fn next(&mut self) -> u64 {
            let mut x = self.0;
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            self.0 = x;
            x
        }

        fn next_u8(&mut self) -> u8 {
            u8::try_from(self.next() >> 56).unwrap()
        }
    }

    fn attrs_buf(count: u16, kind: u32) -> Vec<u8> {
        let mut b = vec![0u8; ATTRS_REPORT_LEN];
        b[ATTRS_LAMP_COUNT_OFFSET..=ATTRS_LAMP_COUNT_OFFSET + 1]
            .copy_from_slice(&count.to_le_bytes());
        b[ATTRS_LAMP_KIND_OFFSET..ATTRS_LAMP_KIND_OFFSET + 4].copy_from_slice(&kind.to_le_bytes());
        b
    }

    #[test]
    fn parse_attrs_lee_campos_le_y_rechaza_corto() {
        assert_eq!(
            parse_attrs(&attrs_buf(1, 0x1122_3344)).unwrap(),
            (1, 0x1122_3344)
        );
        assert_eq!(parse_attrs(&attrs_buf(3, 7)).unwrap(), (3, 7));
        assert!(parse_attrs(&attrs_buf(1, 0)[..10]).is_err());
    }

    #[test]
    fn hid_ioctl_request_codifica_longitud_y_rechaza_invalidas() {
        let r = hid_ioctl_request(HIDIOCGFEATURE_NR, 23).unwrap();
        assert_eq!(r >> 30, 0b11);
        assert_eq!((r >> 16) & 0x3fff, 23);
        assert_eq!((r >> 8) & 0xff, HID_IOCTL_TYPE);
        assert_eq!(r & 0xff, HIDIOCGFEATURE_NR);
        assert!(hid_ioctl_request(HIDIOCSFEATURE_NR, 0).is_err());
        assert!(hid_ioctl_request(HIDIOCSFEATURE_NR, 0x1_0000).is_err());
    }

    #[test]
    fn color_report_invariantes_de_campos() {
        for count in [0u16, 1, 2, 100, u16::MAX] {
            let r = color_report(count, (0x12, 0x34, 0x56));
            assert_eq!(r.len(), COLOR_REPORT_LEN);
            assert_eq!(r[0], REPORT_ID_COLOR);
            assert_eq!(r[1], COLOR_ZONE_COUNT);
            assert_eq!(u16::from_le_bytes([r[2], r[3]]), 0);
            assert_eq!(u16::from_le_bytes([r[4], r[5]]), count.saturating_sub(1));
            assert_eq!(r[6..9], [0x12, 0x34, 0x56]);
            assert_eq!(r[COLOR_REPORT_LEN - 1], COLOR_INTENSITY_MAX);
            assert_eq!(COLOR_INTENSITY_MAX, 0xff);
        }
    }

    #[test]
    fn hid_ioctl_request_codifica_todas_las_longitudes() {
        let mut rng = Xorshift64(0x0123_4567_89ab_cdef);
        for len in 1..=usize::from(u16::MAX) {
            let nr = u64::from(rng.next_u8());
            let r = hid_ioctl_request(nr, len).unwrap();
            assert_eq!(r >> 30, 0b11);
            assert_eq!(
                (r >> 16) & 0x3fff,
                u64::try_from(len).unwrap() & 0x3fff,
                "campo size del ioctl para len={len}"
            );
            assert_eq!((r >> 8) & 0xff, HID_IOCTL_TYPE);
            assert_eq!(r & 0xff, nr & 0xff);
        }
        for len in [1usize, 10, 23] {
            let r = hid_ioctl_request(HIDIOCGFEATURE_NR, len).unwrap();
            assert_eq!((r >> 16) & 0x3fff, u64::try_from(len).unwrap());
        }
        assert!(hid_ioctl_request(HIDIOCGFEATURE_NR, 0).is_err());
        assert!(hid_ioctl_request(HIDIOCGFEATURE_NR, 0x1_0000).is_err());
    }
}
