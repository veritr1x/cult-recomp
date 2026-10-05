"""Exercise the native host's normal mouse routing using each game's smoke script."""

import argparse
import json
import os
import re
import subprocess
import time
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
        "guest_access_violations": re.findall(r"[^\n]*raising an access violation[^\n]*", log),
        "unsupported_control_messages": re.findall(r"(?:ListBox|Edit) message [0-9a-f]+ is unsupported", log),
    }


def save_roundtrip(profile, extension, started):
    """Only fresh saves from this run can establish a serialized-state round trip."""
    paths = [profile / (name + extension) for name in ("P1", "P2", "P3")]
    if not all(p.is_file() and 0 < p.stat().st_size < 65536 for p in paths):
        return {"verified": False, "reason": "The three nonempty save files were not written"}
    fresh = all(p.stat().st_mtime >= started for p in paths)
    equal = paths[0].read_bytes() == paths[1].read_bytes()
    try:
        # Both supplied save formats store the audited X/Y integers in lines 3/4.
        positions = [[int(v) for v in p.read_text().splitlines()[2:4]] for p in paths]
        moved = all(len(pos) == 2 for pos in positions) and positions[0] != positions[2]
    except ValueError:
        positions, moved = [], False
    verified = fresh and equal and moved
    return {"verified": verified, "fresh_writes": fresh,
            "same_serialized_state": equal,
            "player_position_changed": moved, "positions_before_restored_changed": positions,
            "reason": "Fresh saves match after movement and reload" if verified else
                      "Stale saves, different restored state or unverified movement"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--scenario", choices=["play", "intro", "newgame", "gameplay", "help", "save"], default="play")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--trace-abi", "--trace-import-abi", dest="trace_abi", action="store_true")
    parser.add_argument("--watch-guest", help="guest watchpoint in hex address[:length] form")
    parser.add_argument("--trace-windows", action="store_true")
    parser.add_argument("--trace-gdi", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=30)
    parser.add_argument("--toolchain", type=Path, default=ROOT / "build/toolchains/llvm-mingw-20260922-ucrt-x86_64")
    args = parser.parse_args()
    if args.max_seconds <= 0:
        parser.error("The time bound must be positive")
    failed = False
    for game_id in GAMES if args.game == "all" else [args.game]:
        game = ROOT / "games" / game_id
        directory = game / "build" / ("input-probe" if args.scenario == "play" else f"{args.scenario}-probe")
        directory.mkdir(parents=True, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("RECOMP_")}
        env.update(RECOMP_PROFILE_DIR=str(directory / "profile"), RECOMP_PIN_CLOCK="1",
                   RECOMP_NO_MODS="1", RECOMP_SMOKE_DRAWABLE="1024x768",
                   RECOMP_SMOKE_SECONDS=str(args.max_seconds), RECOMP_FRAME_EVERY="30",
                   RECOMP_FRAMES=str(directory / "frames"), RECOMP_LOG="2" if args.verbose else "1")
        env["PATH"] = str(args.toolchain.resolve() / "bin") + os.pathsep + env.get("PATH", "")
        if args.trace_abi:
            env["RECOMP_IMPORT_ABI_TRACE"] = "1"
            env["RECOMP_MODULE_ABI_TRACE"] = "1"
        if args.watch_guest:
            env["RECOMP_WATCH"] = args.watch_guest
        if args.trace_windows:
            env["RECOMP_TRACE_WINDOWS"] = "1"
        if args.trace_gdi:
            env["RECOMP_TRACE_GDI"] = "1"
        executable = game / "build/recomp/pop_smoke.exe"
        script = game / "smoke" / f"{args.scenario}.script"
        timed_out = False
        started = time.time()
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
                  "script": str(script), "scenario": args.scenario,
                  "probe": "native mouse input and " +
                           {"play": "play-control transition", "intro": "intro transition",
                            "newgame": "new-game and keyboard movement",
                            "gameplay": "opening dialogue and keyboard movement",
                            "help": "keyboard navigation to the help screen",
                            "save": "save, movement, load and serialized-state round trip"}[args.scenario]}
        if args.scenario == "save":
            record["save_roundtrip"] = save_roundtrip(directory / "profile",
                                                    ".zsg" if game_id == "cult" else ".fcg", started)
            failed |= not record["save_roundtrip"]["verified"]
        (directory / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        failed |= returncode != 0 or timed_out or not completed or any(
            evidence[key] for key in ("missing_imports_called", "unknown_transfers", "runtime_errors", "guest_access_violations", "unsupported_control_messages"))
        print(f"{game_id}: exit={returncode}, timeout={timed_out}, script_completed={completed}, missing={missing}, unknown={len(unknown)}, runtime_errors={evidence['runtime_errors']}")
        print(f"Evidence: {directory / 'result.json'}")
        if "save_roundtrip" in record:
            print(f"Save round trip: {record['save_roundtrip']}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
