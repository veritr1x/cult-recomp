"""Render the supplied games' SMF scores through RecompKit's offline MCI mixer."""

import argparse
import os
import subprocess
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--host-binary", type=Path,
                        default=ROOT / "games/cult2/build/recomp" /
                        ("host_tests.exe" if os.name == "nt" else "host_tests"))
    parser.add_argument("--toolchain", type=Path, default=ROOT /
                        "build/toolchains/llvm-mingw-20260922-ucrt-x86_64" if os.name == "nt" else None)
    args = parser.parse_args()
    scores = []
    for game in GAMES if args.game == "all" else [args.game]:
        for path in sorted((ROOT / "games" / game / "original/install").iterdir()):
            if path.is_file():
                with path.open("rb") as source:
                    if source.read(4) == b"MThd":
                        scores.append(path)
    if not scores:
        parser.error("No supplied SMF scores found; import the archives first")
    env = {key: value for key, value in os.environ.items() if not key.startswith("RECOMP_")}
    if args.toolchain:
        env["PATH"] = str(args.toolchain.resolve() / "bin") + os.pathsep + env.get("PATH", "")
    evidence = ROOT / "build/audio-probe"
    evidence.mkdir(parents=True, exist_ok=True)
    env["RECOMP_PROFILE_DIR"] = str(evidence / "profile")
    with (evidence / "scores.log").open("wb") as output:
        result = subprocess.run([str(args.host_binary.resolve()), "--mci-scores", *map(str, scores)],
                                cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT,
                                timeout=180)
    print(f"{len(scores)} original scores: exit={result.returncode}")
    print(f"Evidence: {evidence / 'scores.log'}")
    print("This offline render does not verify audible device output or guest music triggers.")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
