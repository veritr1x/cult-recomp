#!/usr/bin/env python3
"""Run the kit suites for a Cult profile; default portable tests need no game files."""
import argparse
import subprocess
import sys

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="cult")
    args, extra = parser.parse_known_args()
    tool = ROOT / "kit/tools/test.py"
    if not tool.is_file():
        raise SystemExit("Run git submodule update --init, then tools/apply_kit_patches.py")
    for game_id in GAMES if args.game == "all" else [args.game]:
        subprocess.run([sys.executable, str(tool), "--game-dir",
                        str(ROOT / "games" / game_id), *extra], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
