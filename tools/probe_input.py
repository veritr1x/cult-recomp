"""Exercise the native host's normal mouse routing using each game's smoke script."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=30)
    parser.add_argument("--toolchain", type=Path, default=ROOT / "build/toolchains/llvm-mingw-20260922-ucrt-x86_64")
    args = parser.parse_args()
    if args.max_seconds <= 0:
        parser.error("The time bound must be positive")
    failed = False
    for game_id in GAMES if args.game == "all" else [args.game]:
        game = ROOT / "games" / game_id
        directory = game / "build/input-probe"
        directory.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("RECOMP_")}
        env.update(RECOMP_PROFILE_DIR=str(directory / "profile"), RECOMP_PIN_CLOCK="1",
                   RECOMP_NO_MODS="1", RECOMP_SMOKE_DRAWABLE="1024x768",
                   RECOMP_SMOKE_SECONDS=str(args.max_seconds), RECOMP_FRAME_EVERY="30",
                   RECOMP_FRAMES=str(directory / "frames"), RECOMP_LOG="2" if args.verbose else "1")
        env["PATH"] = str(args.toolchain.resolve() / "bin") + os.pathsep + env.get("PATH", "")
        executable = game / "build/recomp/pop_smoke.exe"
        script = game / "smoke/play.script"
        timed_out = False
        try:
            result = subprocess.run([str(executable), "--script", str(script)], cwd=directory,
                                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=args.max_seconds + 25)
            output, returncode = result.stdout, result.returncode
        except subprocess.TimeoutExpired as error:
            output, returncode, timed_out = error.stdout or b"", None, True
        (directory / "startup.log").write_bytes(output)
        log = output.decode("utf-8", errors="replace")
        progress = re.search(r"script:\s+(\d+) of (\d+) steps", log)
        completed = bool(progress and progress.group(1) == progress.group(2))
        missing = re.findall(r"unimplemented import ([^:]+):", log)
        unknown = re.findall(r"(?:call to unknown target|unknown (?:call|jump)(?: target)?|no translated function|no block entry for indirect jump)[^\n]*", log)
        frames = re.search(r"presented frames:\s+(\d+)", log)
        record = {"returncode": returncode, "timed_out": timed_out, "platform": "Windows x64",
                  "script_completed": completed,
                  "presented_frames": int(frames.group(1)) if frames else None,
                  "missing_imports_called": missing, "unknown_transfers": unknown,
                  "playability_verified": False, "executable": str(executable),
                  "script": str(script), "probe": "native mouse input and play-control transition"}
        (directory / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        failed |= returncode != 0 or timed_out or not completed or bool(missing) or bool(unknown)
        print(f"{game_id}: exit={returncode}, timeout={timed_out}, script_completed={completed}, missing={missing}, unknown={len(unknown)}")
        print(f"Evidence: {directory / 'result.json'}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
