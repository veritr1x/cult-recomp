"""Run the experimental Cult profiles through the pinned RecompKit toolchain.

Translation emits native C, including the mapped VB5/ActiveX libraries.
Completed builds still require platform and gameplay verification.
"""

import argparse
import os
import subprocess
import sys
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
            # Publish the main image and every auxiliary module together, so a
            # rejected translation cannot replace the last working output.
            sys.path.insert(0, str(kit / "tools"))
            import build as kit_build
            config = kit_build.game_config.load(game)
            build_root = game / "build"
            with kit_build.buildlock.BuildLock(game, "Cult translation"):
                kit_build.publish_generated(
                    build_root, lambda stage: kit_build.run_translator(
                        stage, game, build_root,
                        aux_modules=[module["key"] for module in config["aux_modules"]]))
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
