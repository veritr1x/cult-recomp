"""Copy the privately built Android players and their notices without publishing."""

import hashlib
import json
import shutil
import zipfile

from import_archives import GAMES, ROOT


def main():
    out = ROOT / "build/player/android"
    out.mkdir(parents=True, exist_ok=True)
    records = []
    for game in GAMES:
        name = "CultRecomp" if game == "cult" else "Cult2Recomp"
        source = ROOT / "games" / game / "build/android/app/build/outputs/apk/debug/app-debug.apk"
        with zipfile.ZipFile(source) as archive:
            for asset in ("general-midi.sf2", "general-midi-LICENSE.txt", "classic-modes.json"):
                archive.getinfo("assets/runtime/" + asset)
            library = archive.getinfo("lib/arm64-v8a/libmain.so")
            with archive.open(library) as stream:
                header = stream.read(20)
            if header[:5] != b"\x7fELF\x02" or int.from_bytes(header[18:20], "little") != 183:
                raise ValueError(f"{game}: expected an ARM64 ELF library")
        target = out / (name + ".apk")
        shutil.copy2(source, target)
        with target.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        records.append({"game": game, "apk": target.name, "bytes": target.stat().st_size,
                        "sha256": digest, "abi": "arm64-v8a", "signing": "local debug",
                        "device_gameplay_verified": False})
    for name in ("LICENSE", "NOTICE"):
        shutil.copy2(ROOT / "kit" / name, out / name)
    (out / "build-info.json").write_text(json.dumps(records, indent=2) + "\n")
    (out / "README.txt").write_text(
        "Experimental private Android ARM64 players, signed with a local debug key.\n"
        "Device gameplay remains unverified. The APKs include translated code and runtime resources.\n"
        "Use your supplied original game files when importing game data. Keep these packages private.\n",
        newline="\n")
    print(out)


if __name__ == "__main__":
    main()
