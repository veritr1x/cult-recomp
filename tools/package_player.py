"""Assemble a private local player folder from native builds and the supplied inputs."""

import argparse
import json
import platform
import shutil
import tomllib
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--platform", choices=["Windows", "Linux"], default=platform.system())
    args = parser.parse_args()
    for game in GAMES if args.game == "all" else [args.game]:
        game_dir = ROOT / "games" / game
        config = tomllib.loads((game_dir / "game.toml").read_text())["game"]
        app = config["app_name"]
        binary = app + (".exe" if args.platform == "Windows" else "")
        source = game_dir / "build/package" / app
        inputs = game_dir / "original/install"
        if not (source / binary).is_file() or not (inputs / config["executable"]).is_file():
            parser.error(f"{game}: build the requested desktop target and import its inputs first")
        out = ROOT / "build/player" / args.platform.lower() / app
        out.mkdir(parents=True, exist_ok=True)
        names = [binary, "LICENSE", "NOTICE"]
        if args.platform == "Windows":
            names += ["libc++.dll", "libunwind.dll"]
            names += [p.name for p in source.glob("av*-*.dll")]
        else:
            names += [p.name for p in source.glob("libav*.so.*")]
        for name in names:
            path = source / name
            if path.is_file():
                shutil.copy2(path, out / name)
        shutil.copytree(source / "resources", out / "resources", dirs_exist_ok=True)
        shutil.copytree(inputs, out / "game", dirs_exist_ok=True)
        if args.platform == "Windows":
            launch = ("@echo off\r\nsetlocal\r\n"
                      f'set "RECOMP_EXE=%~dp0game\\{config["executable"]}"\r\n'
                      'set "RECOMP_PROFILE_DIR=%~dp0profile"\r\n'
                      'set "RECOMP_NO_MODS=1"\r\n'
                      'if not defined SDL_AUDIODRIVER set "SDL_AUDIODRIVER=directsound"\r\n'
                      f'"%~dp0{binary}"\r\n')
            (out / "Play.cmd").write_bytes(launch.encode("utf-8"))
        else:
            launch = ('#!/bin/sh\nset -eu\n'
                      'player_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
                      f'export RECOMP_EXE="$player_dir/game/{config["executable"]}"\n'
                      'export RECOMP_PROFILE_DIR="$player_dir/profile"\n'
                      'export RECOMP_NO_MODS=1\n'
                      'if [ -n "${WSL_DISTRO_NAME:-}" ]; then\n'
                      '  export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-x11}"\n'
                      '  export PULSE_LATENCY_MSEC="${PULSE_LATENCY_MSEC:-100}"\n'
                      '  export RECOMP_AUDIO_AHEAD="${RECOMP_AUDIO_AHEAD:-8192}"\n'
                      'fi\n'
                      f'exec "$player_dir/{binary}"\n')
            script = out / "Play.sh"
            script.write_text(launch, newline="\n")
            script.chmod(script.stat().st_mode | 0o111)
        (out / "README.txt").write_text(
            f"{config['name']} - experimental native {args.platform} build\n\n"
            "Private local folder assembled from your supplied archive.\n"
            "Launch Play.cmd on Windows or ./Play.sh on Linux.\n"
            "Select a language and Play; use arrows and Enter in the menu.\n"
            "In the game, arrows move and Space advances conversations.\n"
            "Keep the entire folder together; saves and settings go under profile/.\n"
            "Original code and artwork retain their original ownership.\n\n"
            "Bounded opening-scene movement and save/load paths are tested.\n"
            "Full game completion, physical input and audible output remain unverified.\n",
            newline="\n")
        (out / "build-info.json").write_text(json.dumps(
            {"game": game, "platform": args.platform, "binary": binary,
             "original_executable": config["executable"], "full_gameplay_verified": False},
            indent=2) + "\n")
        print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
