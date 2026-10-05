"""Run bounded native startup probes in isolated profiles and retain honest results."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--toolchain", type=Path, default=ROOT / "build/toolchains/llvm-mingw-20260922-ucrt-x86_64")
    args = parser.parse_args()
    failed = False
    for game_id in GAMES if args.game == "all" else [args.game]:
        game = ROOT / "games" / game_id
        directory = game / "build/probe"
        directory.mkdir(parents=True, exist_ok=True)
        env = {key: value for key, value in os.environ.items() if not key.startswith("RECOMP_")}
        env.update(RECOMP_PROFILE_DIR=str(directory / "profile"), RECOMP_IMPORT_STATS="1",
                   RECOMP_MAX_SECONDS="5", RECOMP_MAX_FRAMES="10", RECOMP_FRAME_EVERY="0",
                   RECOMP_NO_MODS="1", RECOMP_FRAMES=str(directory / "frames"))
        env["PATH"] = str(args.toolchain.resolve() / "bin") + os.pathsep + env.get("PATH", "")
        executable = game / "build/recomp/pop_headless.exe"
        result = subprocess.run([str(executable)], cwd=game, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=15)
        (directory / "startup.log").write_bytes(result.stdout)
        log = result.stdout.decode("utf-8", errors="replace")
        frames = re.search(r"presented frames:\s+(\d+)", log)
        missing = re.findall(r"unimplemented import ([^:]+):", log)
        record = {"returncode": result.returncode, "platform": "Windows x64",
                  "presented_frames": int(frames.group(1)) if frames else None,
                  "missing_imports_called": missing, "playability_verified": False,
                  "executable": str(executable), "probe": "bounded native headless entry"}
        (directory / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        failed |= result.returncode != 0 or not record["presented_frames"] or bool(missing)
        print(f"{game_id}: exit={result.returncode}, frames={record['presented_frames']}, missing={missing}")
        print(f"Log: {directory / 'startup.log'}")
    # A no-frame or unresolved-import run must never look like a successful test.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
