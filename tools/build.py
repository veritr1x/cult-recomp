"""Run the experimental Cult profiles through the pinned RecompKit toolchain.

Translation emits native C, including the mapped VB5/ActiveX libraries.
Completed builds still require platform and gameplay verification.
"""

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--kit", type=Path, default=ROOT / "kit")
    parser.add_argument("--translate-only", action="store_true")
    parser.add_argument("--target", choices=["app", "gen", "headless", "smoke", "ios", "android", "web"], default="app")
    parser.add_argument("--preset")
    parser.add_argument("--jobs", type=int, default=6)
    args, extra = parser.parse_known_args()
    if args.translate_only and extra:
        parser.error("Unknown translation arguments: " + " ".join(extra))
    kit = args.kit.resolve()
    env = os.environ.copy()
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    for game_id in GAMES if args.game == "all" else [args.game]:
        game = ROOT / "games" / game_id
        if args.translate_only:
            output = game / "build/recomp/gen"
            command = [sys.executable, str(kit / "tools/recomp/translate.py"),
                       "--game", str(game), "--out", str(output),
                       "--report", str(game / "analysis/translation-report.json")]
            subprocess.run(command, cwd=ROOT, env=env, check=True)
            config = tomllib.loads((game / "game.toml").read_text())
            for module in config.get("modules", {}).get("aux", {}):
                subprocess.run([sys.executable, str(kit / "tools/recomp/translate.py"),
                                "--game", str(game), "--module", module,
                                "--out", str(output / ("aux-" + module)),
                                "--report", str(game / "analysis" / (module + "-translation-report.json"))],
                               cwd=ROOT, env=env, check=True)
            continue
        else:
            print(f"{game_id}: experimental build; gameplay and other platforms are unverified.", flush=True)
            command = [sys.executable, str(kit / "tools/build.py"), "--game-dir", str(game),
                       "--target", args.target, "--jobs", str(args.jobs)]
            if args.preset:
                command += ["--preset", args.preset]
            command += extra
        subprocess.run(command, cwd=ROOT, env=env, check=True)


if __name__ == "__main__":
    main()
