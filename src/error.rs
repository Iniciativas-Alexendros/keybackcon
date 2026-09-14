//! Error del CLI: uso incorrecto, entrada inválida e I/O, con el texto que
//! `cli::main` imprime (exit 2 para uso, 1 para el resto).

use std::fmt;
use std::io;

/// Error de la ejecución del CLI.
#[derive(Debug)]
pub enum Error {
    /// Argumentos ausentes o desconocidos (exit 2).
    Usage,
    /// Entrada inválida con el mensaje ya listo para el usuario.
    Invalid(String),
    /// Fallo de E/S subyacente.
    Io(io::Error),
}

impl fmt::Display for Error {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Error::Usage => f.write_str("uso incorrecto"),
            Error::Invalid(msg) => f.write_str(msg),
            Error::Io(e) => write!(f, "{e}"),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Error::Io(e) => Some(e),
            Error::Usage | Error::Invalid(_) => None,
        }
    }
}

impl From<io::Error> for Error {
    fn from(e: io::Error) -> Self {
        Error::Io(e)
    }
}
