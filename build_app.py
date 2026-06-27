#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC_DIR = ROOT / "src"
ENTRYPOINT = SRC_DIR / "main.py"
VENV_DIR = ROOT / "outreach_env"
APP_NAME = "B2BCI_APP"
DIST_DIR = ROOT / "dist"
WORK_DIR = ROOT / "build" / "pyinstaller"
SPEC_DIR = ROOT / "build" / "spec"
PYINSTALLER_CONFIG_DIR = ROOT / ".pyinstaller"
MPLCONFIG_DIR = ROOT / ".matplotlib"
XDG_CACHE_DIR = ROOT / ".cache"


def add_data_arg(source: Path, destination: str) -> str:
    separator = ";" if os.name == "nt" else ":"
    return f"{source}{separator}{destination}"


def venv_python() -> Path | None:
    candidates = [
        VENV_DIR / "bin" / "python",
        VENV_DIR / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def ensure_expected_python() -> None:
    target = venv_python()
    if target is None:
        return

    if Path(sys.prefix).resolve() == VENV_DIR.resolve():
        return

    print(f"Re-running with virtualenv interpreter: {target}", flush=True)
    result = subprocess.run([str(target), __file__, *sys.argv[1:]], cwd=ROOT)
    raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the src app into a runnable PyInstaller bundle."
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with a console window instead of a windowed app.",
    )
    parser.add_argument(
        "--name",
        default=APP_NAME,
        help=f"Executable/app bundle name (default: {APP_NAME}).",
    )
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        args.name,
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(WORK_DIR),
        "--specpath",
        str(SPEC_DIR),
        "--paths",
        str(SRC_DIR),
        "--add-data",
        add_data_arg(SRC_DIR / "assets", "assets"),
        "--add-data",
        add_data_arg(SRC_DIR / "data.mat", "."),
    ]

    if not args.console:
        command.append("--windowed")

    if sys.platform == "darwin":
        command.extend(["--osx-bundle-identifier", "edu.ucdavis.neurotech.outreach"])

    command.append(str(ENTRYPOINT))
    return command


def main() -> int:
    ensure_expected_python()
    args = parse_args()

    if not ENTRYPOINT.exists():
        print(f"Entrypoint not found: {ENTRYPOINT}", file=sys.stderr)
        return 1

    command = build_command(args)
    env = os.environ.copy()
    env.setdefault("PYINSTALLER_CONFIG_DIR", str(PYINSTALLER_CONFIG_DIR))
    env.setdefault("MPLCONFIGDIR", str(MPLCONFIG_DIR))
    env.setdefault("XDG_CACHE_HOME", str(XDG_CACHE_DIR))
    PYINSTALLER_CONFIG_DIR.mkdir(exist_ok=True)
    MPLCONFIG_DIR.mkdir(exist_ok=True)
    XDG_CACHE_DIR.mkdir(exist_ok=True)
    print("Running build command:", flush=True)
    print(" ".join(command), flush=True)

    try:
        completed = subprocess.run(command, cwd=ROOT, check=False, env=env)
    except FileNotFoundError as exc:
        print(f"Failed to start build: {exc}", file=sys.stderr, flush=True)
        return 1

    if completed.returncode != 0:
        return completed.returncode

    artifact_dir = DIST_DIR / args.name
    artifact_app = DIST_DIR / f"{args.name}.app"
    if artifact_app.exists():
        print(f"Build complete: {artifact_app}", flush=True)
    else:
        print(f"Build complete: {artifact_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
