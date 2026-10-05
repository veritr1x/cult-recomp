"""Exercise the native host's normal mouse routing using each game's smoke script."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

from import_archives import GAMES, ROOT


def read_evidence(log):
    """A completed input script cannot hide a VB error dialog or failed call."""
    progress = re.search(r"script:\s+(\d+) of (\d+) steps", log)
    frames = re.search(r"presented frames:\s+(\d+)", log)
    return {
        "script_completed": bool(progress and progress.group(1) == progress.group(2)),
        "presented_frames": int(frames.group(1)) if frames else None,
        "missing_imports_called": re.findall(r"unimplemented import ([^:]+):", log),
        "unknown_transfers": re.findall(r"(?:call to unknown target|unknown (?:call|jump)(?: target)?|no translated function|no block entry for indirect jump)[^\n]*", log),
        "runtime_errors": re.findall(r"Run-time error '(\d+)'", log),
        "unsupported_control_messages": re.findall(r"(?:ListBox|Edit) message [0-9a-f]+ is unsupported", log),
    }


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
        evidence = read_evidence(log)
        completed = evidence["script_completed"]
        missing, unknown = evidence["missing_imports_called"], evidence["unknown_transfers"]
        record = {"returncode": returncode, "timed_out": timed_out, "platform": "Windows x64",
                  **evidence,
                  "playability_verified": False, "executable": str(executable),
                  "script": str(script), "probe": "native mouse input and play-control transition"}
        (directory / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        failed |= returncode != 0 or timed_out or not completed or any(
            evidence[key] for key in ("missing_imports_called", "unknown_transfers", "runtime_errors", "unsupported_control_messages"))
        print(f"{game_id}: exit={returncode}, timeout={timed_out}, script_completed={completed}, missing={missing}, unknown={len(unknown)}, runtime_errors={evidence['runtime_errors']}")
        print(f"Evidence: {directory / 'result.json'}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
