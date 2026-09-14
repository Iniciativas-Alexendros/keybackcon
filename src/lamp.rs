use std::fs;
use std::io;
use std::os::unix::io::AsRawFd;

unsafe extern "C" {
    fn ioctl(fd: i32, request: u64, arg: *mut u8) -> i32;
}

fn hidioc(nr: u64, len: usize) -> u64 {
    0xC000_0000 | ((len as u64) << 16) | (0x48 << 8) | nr
}

pub struct Lamp {
    f: fs::File,
    count: u16,
}

impl Lamp {
    pub fn find() -> io::Result<std::path::PathBuf> {
        const SIG: &[u8] = &[0x05, 0x59, 0x09, 0x01, 0xA1, 0x01];
        let mut found: Vec<std::path::PathBuf> = Vec::new();
        for e in fs::read_dir("/sys/class/hidraw")? {
            let e = e?;
            let name = e.file_name().to_string_lossy().into_owned();
            if !name.starts_with("hidraw") {
                continue;
            }
            let desc = e.path().join("device/report_descriptor");
            if let Ok(d) = fs::read(&desc) {
                if d.windows(SIG.len()).any(|w| w == SIG) {
                    found.push(std::path::PathBuf::from(format!("/dev/{name}")));
                }
            }
        }
        found.sort();
        found.into_iter().next().ok_or_else(|| {
            io::Error::new(
                io::ErrorKind::NotFound,
                "no se encontró el dispositivo LampArray (¿está cargada la regla udev? mira con 'keybackcon info')",
            )
        })
    }

    pub fn open() -> io::Result<Self> {
        let path = Self::find()?;
        let f = fs::OpenOptions::new()
            .read(true)
            .write(true)
            .open(&path)
            .map_err(|e| {
                io::Error::new(
                    e.kind(),
                    format!(
                        "no se pudo abrir {}: {e} (puede que la regla udev uaccess no funcione)",
                        path.display()
                    ),
                )
            })?;
        let mut l = Lamp { f, count: 1 };
        l.count = l.attrs()?.0.max(1);
        Ok(l)
    }

    fn get_feature(&self, id: u8, len: usize) -> io::Result<Vec<u8>> {
        let mut buf = vec![0u8; len];
        buf[0] = id;
        let r = unsafe { ioctl(self.f.as_raw_fd(), hidioc(0x07, len), buf.as_mut_ptr()) };
        if r < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(buf)
    }

    fn set_feature(&self, buf: &mut [u8]) -> io::Result<()> {
        let r = unsafe {
            ioctl(
                self.f.as_raw_fd(),
                hidioc(0x06, buf.len()),
                buf.as_mut_ptr(),
            )
        };
        if r < 0 {
            return Err(io::Error::last_os_error());
        }
        Ok(())
    }

    pub fn attrs(&self) -> io::Result<(u16, u32)> {
        let b = self.get_feature(1, 23)?;
        Ok((
            u16::from_le_bytes([b[1], b[2]]),
            u32::from_le_bytes([b[15], b[16], b[17], b[18]]),
        ))
    }

    pub fn autonomous(&self, on: bool) -> io::Result<()> {
        self.set_feature(&mut [6u8, u8::from(on)])
    }

    pub fn color(&self, (r, g, b): crate::color::Rgb) -> io::Result<()> {
        let mut buf = [0u8; 10];
        buf[0] = 5;
        buf[1] = 1;
        buf[2..4].copy_from_slice(&0u16.to_le_bytes());
        buf[4..6].copy_from_slice(&(self.count - 1).to_le_bytes());
        buf[6] = r;
        buf[7] = g;
        buf[8] = b;
        buf[9] = 255;
        self.set_feature(&mut buf)
    }
}
