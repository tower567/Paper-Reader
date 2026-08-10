#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import os
import shlex
from pathlib import Path

from paperlib import atomic_write_text


CONFIG_RELATIVE_PATH = Path(".config") / "paper-reader" / "mineru.env"
START_MARKER = "# >>> Paper Reader MinerU >>>"
END_MARKER = "# <<< Paper Reader MinerU <<<"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Securely configure a user-level MinerU token for WSL and Paper-Reader."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report whether a token file exists without printing the token.",
    )
    parser.add_argument(
        "--home",
        type=Path,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def validate_token(token: str) -> str:
    token = token.strip()
    if not token:
        raise ValueError("Token cannot be empty")
    if any(character in token for character in ("\n", "\r", "\0")):
        raise ValueError("Token contains unsupported control characters")
    return token


def shell_block() -> str:
    return (
        f"{START_MARKER}\n"
        'if [ -r "$HOME/.config/paper-reader/mineru.env" ]; then\n'
        '    . "$HOME/.config/paper-reader/mineru.env"\n'
        "fi\n"
        f"{END_MARKER}"
    )


def install_token(token: str, home: Path) -> tuple[Path, Path]:
    token = validate_token(token)
    home = home.expanduser().resolve()
    config_path = home / CONFIG_RELATIVE_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(config_path.parent, 0o700)
    content = (
        "# Created by Paper-Reader. Do not commit or share this file.\n"
        f"export MINERU_API_TOKEN={shlex.quote(token)}\n"
    )
    atomic_write_text(config_path, content)
    os.chmod(config_path, 0o600)

    bashrc_path = home / ".bashrc"
    bashrc = bashrc_path.read_text(encoding="utf-8") if bashrc_path.is_file() else ""
    if START_MARKER not in bashrc:
        updated = bashrc.rstrip() + "\n\n" + shell_block() + "\n"
        atomic_write_text(bashrc_path, updated.lstrip("\n"))
    return config_path, bashrc_path


def main() -> int:
    args = parse_args()
    home = (args.home or Path.home()).expanduser().resolve()
    config_path = home / CONFIG_RELATIVE_PATH
    if args.check:
        if config_path.is_file() and config_path.stat().st_size > 0:
            print(f"CONFIGURED: {config_path}")
            print(f"MODE: {oct(config_path.stat().st_mode & 0o777)}")
            return 0
        print(f"NOT CONFIGURED: {config_path}")
        return 1

    token = getpass.getpass("MinerU API Token（输入不会显示）: ")
    try:
        config_path, bashrc_path = install_token(token, home)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Saved securely: {config_path}")
    print(f"Updated shell startup: {bashrc_path}")
    print("Restart Codex, or run: source ~/.bashrc")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
