#!/usr/bin/env python3
"""Make PadMint's release downloads: Windows (Python included), macOS and Linux.

Usage: scripts/package-release.py OUTPUT_FOLDER
Writes PadMint-vX.Y.Z-windows.zip, -macos.zip, -linux.zip and SHA256SUMS,
then runs PadMint's own release gate on them (ZIP everywhere: the gate opens
ZIP archives only).
"""
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from padmint import __version__, gate  # noqa: E402

# Python's official embeddable package; digest from python.org's release page.
PYTHON = "3.13.15"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON}/python-{PYTHON}-embed-amd64.zip"
PYTHON_SHA256 = "d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf"


def payload():
    """(archive path, source path) for everything a player needs."""
    files = [ROOT / name for name in (
        "README.md", "STATUS.md", "STATUS-HISTORY.md",
        "docs/COMPATIBILITY.md", "docs/ADDING_A_GAME.md", "docs/DECISIONS.md",
        "docs/IPHONE_FROM_WINDOWS.md",
    )]
    # Sorted by name as text: Windows compares paths ignoring case, which would
    # put TargetConditionals.h elsewhere and change the ZIP's bytes.
    by_name = lambda path: path.name  # noqa: E731
    files += sorted((ROOT / "padmint").glob("*.py"), key=by_name) + [ROOT / "padmint/tools.lock.json"]
    # Headers the universal iPhone module pipeline adds to the open-source SDK.
    files += sorted((ROOT / "padmint/ios-sdk/include").glob("*.h"), key=by_name)
    files += sorted((ROOT / "catalog").glob("*.json"), key=by_name)
    return [(path.relative_to(ROOT).as_posix(), path) for path in files]


def add(bundle, name, data, executable=False):
    info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
    # Unix mode with the regular-file type bit: macOS's Archive Utility (what a
    # double-click in Finder uses) drops permissions stored without it, which
    # left PadMint.command unable to start (padmint#7).
    info.create_system = 3
    info.external_attr = (0o100755 if executable else 0o100644) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    bundle.writestr(info, data)


def windows_python():
    with urllib.request.urlopen(PYTHON_URL) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != PYTHON_SHA256:
        raise SystemExit(f"sha256 mismatch for {PYTHON_URL}")
    return zipfile.ZipFile(io.BytesIO(data))


# What a player sees after unzipping: the launcher, this note and one app folder.
START = {
    "PadMint.cmd": ("Double-click PadMint (PadMint.cmd).",
                    "If Windows says it protected your PC: More info, then Run anyway.",
                    "Haz doble clic en PadMint (PadMint.cmd). Si Windows dice que protegió tu PC: Más información, luego Ejecutar de todas formas.",
                    "Clique duas vezes em PadMint (PadMint.cmd). Se o Windows disser que protegeu o seu PC: Mais informações, depois Executar assim mesmo."),
    "PadMint.command": ("Double-click PadMint.command. Once, before that, run this in Terminal: xcode-select --install",
                        "The first time, macOS says Apple could not verify it: choose Done, then System Settings, Privacy & Security, Open Anyway.",
                        "Antes, una sola vez, ejecuta en Terminal: xcode-select --install. Luego haz doble clic en PadMint.command. La primera vez, macOS dice que Apple no pudo verificarlo: cierra el aviso y ve a Ajustes del Sistema, Privacidad y seguridad, Abrir igualmente.",
                        "Antes, uma única vez, execute no Terminal: xcode-select --install. Depois clique duas vezes em PadMint.command. Na primeira vez, o macOS diz que a Apple não pôde verificá-lo: feche o aviso e vá em Ajustes do Sistema, Privacidade e Segurança, Abrir Mesmo Assim."),
    "padmint.sh": ("In a terminal in this folder, run: sh padmint.sh",
                   "It needs Python 3.9 or newer and Git, for example: sudo apt install python3 git",
                   "En una terminal en esta carpeta, ejecuta: sh padmint.sh (necesita Python 3.9 o más nuevo y Git).",
                   "Num terminal nesta pasta, execute: sh padmint.sh (precisa do Python 3.9 ou mais novo e do Git)."),
}


def start_note(launcher):
    open_, warning, es, pt = START[launcher]
    lines = [
        "PadMint: start here", "",
        "1. " + open_, "   " + warning,
        "2. A small window opens and stays open: that is PadMint working. Your web browser",
        "   opens the PadMint page. If it doesn't, open the address the small window shows.",
        "3. On the page, choose your game and follow the steps. It tells you what it will",
        "   download before it starts, and how to install your copy when it finishes.",
        "   Close the small window when you are done.", "",
        "The app folder is PadMint itself: you don't need to open it.", "",
        "Guide: https://github.com/chrissotraidis/padmint#quick-start",
        "Help: https://discord.gg/xwHfUD2bxW", "",
        "Español: " + es + " Se abre una ventana pequeña (déjala abierta) y la página de PadMint en tu navegador: elige tu juego y sigue los pasos.",
        "",
        "Português: " + pt + " Abre uma janela pequena (deixe-a aberta) e a página do PadMint no seu navegador: escolha o seu jogo e siga os passos.",
        "",
    ]
    newline = "\r\n" if launcher.endswith(".cmd") else "\n"
    return newline.join(lines).encode("utf-8")


def make_zip(path, top, launcher, python=None):
    with zipfile.ZipFile(path, "w") as bundle:
        add(bundle, f"{top}/{launcher.name}", launcher.read_bytes(), executable=True)
        add(bundle, f"{top}/Start here.txt", start_note(launcher.name))
        for name, source in payload():
            add(bundle, f"{top}/app/{name}", source.read_bytes())
        if python is not None:
            for info in python.infolist():
                data = python.read(info)
                if info.filename.endswith("._pth"):
                    # The embedded Python also finds the padmint package beside it.
                    lines = data.decode().splitlines()
                    lines.insert(lines.index(".") + 1, "..")
                    data = ("\r\n".join(lines) + "\r\n").encode()
                add(bundle, f"{top}/app/python/{info.filename}", data)


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    top = f"PadMint-v{__version__}"
    launchers = ROOT / "launchers"
    made = [out / f"{top}-windows.zip", out / f"{top}-macos.zip", out / f"{top}-linux.zip"]
    make_zip(made[0], top, launchers / "PadMint.cmd", windows_python())
    make_zip(made[1], top, launchers / "PadMint.command")
    make_zip(made[2], top, launchers / "padmint.sh")
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in made)
    (out / "SHA256SUMS").write_bytes(sums.encode("utf-8"))
    print(sums, end="")
    return gate.audit(made, None)


if __name__ == "__main__":
    raise SystemExit(main())
