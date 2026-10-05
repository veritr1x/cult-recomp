"""Create a local Windows LLVM-MinGW preset for diagnostic native builds."""

import argparse
import json
from pathlib import Path

from import_archives import ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", type=Path, required=True, help="Directory containing bin/clang.exe")
    args = parser.parse_args()
    directory = args.toolchain.resolve() / "bin"
    for compiler in ("clang.exe", "clang++.exe", "ld.lld.exe"):
        if not (directory / compiler).is_file():
            parser.error(f"Missing {directory / compiler}")
    preset = {"version": 5, "configurePresets": [{
        "name": "cult-windows-llvm", "inherits": "base",
        "cacheVariables": {"CMAKE_C_COMPILER": (directory / "clang.exe").as_posix(),
                           "CMAKE_CXX_COMPILER": (directory / "clang++.exe").as_posix(),
                           "CMAKE_EXE_LINKER_FLAGS": "-fuse-ld=lld",
                           "CMAKE_SHARED_LINKER_FLAGS": "-fuse-ld=lld",
                           "CMAKE_MODULE_LINKER_FLAGS": "-fuse-ld=lld",
                           "RECOMP_VIDEO": "OFF"},
    }]}
    path = ROOT / "kit/CMakeUserPresets.json"
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8-sig"))
        configs = existing.get("configurePresets", [])
        matching = [item for item in configs if item.get("name") == "cult-windows-llvm"]
        if matching and matching != preset["configurePresets"]:
            parser.error(f"Preserving different local LLVM preset: {path}")
        if not matching:
            configs += preset["configurePresets"]
        existing["configurePresets"] = configs
        preset = existing
    path.write_text(json.dumps(preset, indent=2) + "\n")
    print(f"Wrote ignored diagnostic preset {path}")


if __name__ == "__main__":
    main()
