"""Assemble private browser players and local test inputs without publishing them."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from import_archives import GAMES, ROOT


def wasm_sections(path):
    data = path.read_bytes()
    if data[:8] != b"\0asm\1\0\0\0":
        raise ValueError(f"Not a WebAssembly module: {path}")
    at = 8
    records = []
    while at < len(data):
        section_id = data[at]
        at += 1
        size, shift = 0, 0
        while True:
            value = data[at]
            at += 1
            size |= (value & 127) << shift
            if not value & 128:
                break
            shift += 7
            if shift > 28:
                raise ValueError("Invalid WebAssembly section size")
        end = at + size
        if end > len(data):
            raise ValueError("Truncated WebAssembly section")
        if section_id:
            records.append((section_id, size, hashlib.sha256(memoryview(data)[at:end]).hexdigest()))
        at = end
    return records


def main():
    out = ROOT / "build/player/web"
    command = [sys.executable, str(ROOT / "kit/tools/web_launcher.py"), "--out", str(out)]
    for game in GAMES:
        command += ["--game-dir", str(ROOT / "games" / game), "--web-build",
                    f"{game}={ROOT / 'games' / game / 'build/web/recomp'}"]
    subprocess.run(command, check=True)
    objcopy = (ROOT / "build/toolchains/llvm-mingw-20260922-ucrt-x86_64/bin/llvm-objcopy.exe"
               if os.name == "nt" else ROOT / "build/toolchains/emsdk/upstream/bin/llvm-objcopy")
    diagnostics = out / "_diagnostic"
    diagnostics.mkdir(exist_ok=True)
    records = []
    for game in GAMES:
        name = "CultRecomp" if game == "cult" else "Cult2Recomp"
        source = ROOT / "games" / game / "build/web/recomp" / (name + ".wasm")
        target = out / game / source.name
        subprocess.run([str(objcopy), "--strip-debug", str(source), str(target)], check=True)
        if wasm_sections(source) != wasm_sections(target):
            raise ValueError(f"{game}: stripping debug metadata changed executable sections")
        records.append({"game": game, "source_bytes": source.stat().st_size,
                        "player_bytes": target.stat().st_size, "executable_sections_unchanged": True,
                        "browser_gameplay_verified": False})
        with zipfile.ZipFile(diagnostics / (game + ".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
            install = ROOT / "games" / game / "original/install"
            for path in sorted(install.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(install).as_posix())
    (diagnostics / "build-info.json").write_text(json.dumps(records, indent=2) + "\n")
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(ROOT / "kit" / name, out / name)
    (out / "README.txt").write_text(
        "Experimental private browser players. No external publication.\n"
        "The _diagnostic ZIPs contain copies of your supplied game data.\n"
        "Keep this folder private. Browser gameplay remains unverified.\n"
        "Serve with kit/tools/web_launcher.py --game-dir <absolute cult dir> "
        "--game-dir <absolute cult2 dir> --out <this folder> --serve 8086.\n",
        newline="\n")
    print(out)


if __name__ == "__main__":
    main()
