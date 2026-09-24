import os
import shutil
import signal
import subprocess
import time


def find_binary():
    for cand in (
        shutil.which("keybackcon"),
        os.path.expanduser("~/.local/bin/keybackcon"),
        shutil.which("kbd-rgb"),
        os.path.expanduser("~/.local/bin/kbd-rgb"),
    ):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return "keybackcon"


def udev_install_argv(src: str, dst: str) -> list[str]:
    """Construye el argv de pkexec sin interpolar rutas en el script."""
    script = (
        'install -m644 "$1" "$2" && '
        "udevadm control --reload && "
        "udevadm trigger --subsystem-match=hidraw"
    )
    return ["pkexec", "sh", "-c", script, "sh", src, dst]


def state_paths():
    base = os.environ.get("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
    return (
        os.path.join(base, "keybackcon/state"),
        os.path.join(base, "kbd-rgb/state"),
    )


def pid_paths():
    base = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
    return (
        os.path.join(base, "keybackcon/animation.pid"),
        os.path.join(base, "keybackcon/anim.pid"),
        os.path.join(base, "kbd-rgb/anim.pid"),
    )


class KeybackconError(Exception):
    message: str

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class KeybackconClient:
    def __init__(self, binary: str | None = None):
        self._bin = binary if binary else find_binary()
        self._proc = None

    def _run(self, args: list) -> subprocess.CompletedProcess:
        try:
            proc = subprocess.run(
                [self._bin] + args,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except FileNotFoundError:
            raise KeybackconError(
                f"No encuentro el binario ({self._bin}). Instálalo primero."
            )
        except subprocess.TimeoutExpired:
            raise KeybackconError("El teclado tardó demasiado en responder.")
        except OSError as e:
            raise KeybackconError(f"El teclado no respondió: {e}")
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            if err:
                raise KeybackconError(err)
            raise KeybackconError(
                f"El teclado no respondió (código {proc.returncode})."
            )
        return proc

    def _stop_child(self) -> None:
        proc = self._proc
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        self._proc = None

    def info(self) -> dict:
        proc = self._run(["info"])
        info: dict = {}
        for line in proc.stdout.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()
        return info

    def set_color(self, hex: str) -> None:
        self._run(["set", hex])

    def set_brightness(self, pct: int) -> None:
        self._run(["brightness", str(pct)])

    def animation(self, mode: str) -> None:
        self._stop_child()
        self._run(["firmware-effects", "off"])
        try:
            self._proc = subprocess.Popen([self._bin, "animation", mode])
        except FileNotFoundError:
            raise KeybackconError(
                f"No encuentro el binario ({self._bin}). Instálalo primero."
            )
        except OSError as e:
            raise KeybackconError(f"El teclado no respondió: {e}")

    def stop(self) -> str:
        self._stop_child()
        proc = self._run(["stop"])
        return proc.stdout.strip()

    def restore(self) -> str:
        self._stop_child()
        proc = self._run(["restore"])
        return proc.stdout.strip()

    def off(self) -> None:
        self._run(["off"])

    def firmware_effects(self, on: bool) -> None:
        self._run(["firmware-effects", "on" if on else "off"])

    def get_state_file(self) -> tuple[str, int]:
        for path in state_paths():
            try:
                with open(path) as f:
                    parts = f.read().split()
                    color = parts[0].lstrip("#").lower()
                    pct = int(parts[1]) if len(parts) > 1 else 100
                    if len(color) != 6:
                        raise ValueError
                    int(color, 16)
                    return color, max(0, min(100, pct))
            except Exception:
                continue
        return "ffffff", 100

    def animation_running(self) -> int | None:
        for path in pid_paths():
            try:
                with open(path) as f:
                    pid = int(f.read().strip())
                if pid <= 0:
                    continue
                os.kill(pid, 0)
                with open(f"/proc/{pid}/cmdline", "rb") as cf:
                    cmd = cf.read().decode(errors="ignore")
                if "keybackcon" in cmd or "kbd-rgb" in cmd:
                    return pid
                os.unlink(path)
            except Exception:
                continue
        return None
