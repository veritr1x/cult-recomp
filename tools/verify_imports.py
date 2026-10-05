"""Compare expanded media against Windows' independent SZDD decoder."""

import argparse
import hashlib
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from import_archives import GAMES, ROOT


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    parser.add_argument("--expand", type=Path, default=Path("C:/Windows/System32/expand.exe"))
    args = parser.parse_args()
    if not args.expand.is_file():
        parser.error("This independent check needs Windows expand.exe")
    for game_id, (archive_name, _) in GAMES.items():
        game = ROOT / "games" / game_id
        manifest = json.loads((game / "analysis/archive-manifest.json").read_text())
        checked = 0
        with tempfile.TemporaryDirectory() as temporary, zipfile.ZipFile(args.downloads / archive_name) as archive:
            directory = Path(temporary)
            members = {name.casefold(): name for name in archive.namelist()}
            for index, item in enumerate(manifest["files"]):
                source, output = directory / "compressed.bin", directory / "expanded.bin"
                source.write_bytes(archive.read(members[item["source"].casefold()]))
                if output.exists():
                    output.unlink()
                subprocess.run([str(args.expand), str(source), str(output)], check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                expected = output.read_bytes()
                actual = (game / item["path"]).read_bytes()
                if actual != expected or hashlib.sha256(actual).hexdigest() != item["sha256"]:
                    raise ValueError(f"Independent decoder mismatch: {game_id}/{item['source']}")
                checked += 1
        report = {"independent_decoder": "Windows expand.exe", "checked_files": checked,
                  "all_equal": True, "archive_sha256": manifest["archive_sha256"]}
        (game / "analysis/import-verification.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{game_id}: all {checked} payloads match Windows expand.exe byte for byte")


if __name__ == "__main__":
    main()
