"""Expand the supplied VB5 setup media locally, without running an installer.

SETUP.LST is read only as a filename/length table. Registration directives,
shortcuts, embedded documents and executable contents are never executed.
"""

import argparse
import csv
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SZDD_MAGIC = b"SZDD\x88\xf0\x27\x33"
MAX_FILE_SIZE = 64 * 1024 * 1024
GAMES = {
    "cult": ("Cult_Win_EN.zip", "Cult.exe"),
    "cult2": ("Cult-II-Federal-Crime_Win_EN.zip", "Cult2FC.exe"),
}


def expand_szdd(data):
    """Decode SZDD mode A's 4 KiB LZSS ring and enforce the declared length."""
    if not data.startswith(SZDD_MAGIC):
        return data
    if len(data) < 14 or data[8] != ord("A"):
        raise ValueError("Unsupported or truncated SZDD header")
    length = struct.unpack_from("<I", data, 10)[0]
    if length > MAX_FILE_SIZE:
        raise ValueError("SZDD output exceeds the private-input size limit")
    ring = bytearray(b" " * 4096)
    cursor, position = 4096 - 16, 14
    output = bytearray()
    while len(output) < length:
        if position >= len(data):
            raise ValueError("Truncated SZDD flag byte")
        flags = data[position]
        position += 1
        for bit in range(8):
            if len(output) == length:
                break
            if flags & (1 << bit):
                if position >= len(data):
                    raise ValueError("Truncated SZDD literal")
                values = [data[position]]
                position += 1
                for value in values:
                    output.append(value)
                    ring[cursor] = value
                    cursor = (cursor + 1) & 4095
            else:
                if position + 2 > len(data):
                    raise ValueError("Truncated SZDD backreference")
                low, high = data[position:position + 2]
                position += 2
                source = low | ((high & 0xf0) << 4)
                count = (high & 15) + 3
                if len(output) + count > length:
                    raise ValueError("SZDD backreference exceeds declared size")
                # Read each byte after the previous write: references may overlap.
                for index in range(count):
                    value = ring[(source + index) & 4095]
                    output.append(value)
                    ring[cursor] = value
                    cursor = (cursor + 1) & 4095
    return bytes(output)


def filename(value):
    """Accept only a plain setup-media filename, never a path or directive."""
    if not value or value in (".", "..") or any(c in value for c in '/\\:'):
        raise ValueError(f"Unsafe setup filename: {value!r}")
    if any(ord(c) < 32 for c in value) or value.endswith((".", " ")):
        raise ValueError(f"Invalid setup filename: {value!r}")
    if re.fullmatch(r"(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", value, re.I):
        raise ValueError(f"Reserved setup filename: {value!r}")
    return value


def import_archive(archive_path, game_id):
    """Validate all payloads first, then write private game and dependency copies."""
    game_dir = ROOT / "games" / game_id
    install = game_dir / "original" / "install"
    dependencies = game_dir / "original" / "dependencies"
    payloads, destinations, size_mismatches = [], set(), []
    with zipfile.ZipFile(archive_path) as archive:
        members = {}
        for member in archive.infolist():
            key = member.filename.casefold()
            if key in members:
                raise ValueError(f"Duplicate ZIP member: {member.filename}")
            members[key] = member
        setup = archive.read(members["setup.lst"]).decode("cp1252")
        for line in setup.splitlines():
            if not re.match(r"^File\d+=", line):
                continue
            row = next(csv.reader([line.split("=", 1)[1]]))
            source, target = filename(row[2]), filename(row[3])
            member = members[source.casefold()]
            if member.file_size > MAX_FILE_SIZE:
                raise ValueError(f"Input exceeds size limit: {source}")
            content = expand_szdd(archive.read(member))
            if len(content) != int(row[8]):
                # The supplied media has stale SETUP.LST lengths for some data.
                # SZDD's own declared length was checked by the decoder.
                size_mismatches.append({"source": source, "setup_size": int(row[8]),
                                        "actual_size": len(content)})
            directory = install if row[4] == "$(AppPath)" else dependencies
            path = directory / target
            if str(path).casefold() in destinations:
                raise ValueError(f"Duplicate destination: {path}")
            destinations.add(str(path).casefold())
            if path.exists() and path.read_bytes() != content:
                raise ValueError(f"Preserving different existing file: {path}")
            payloads.append((path, content, source))
    manifest = {
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "game_id": game_id,
        "setup_size_mismatches": size_mismatches,
        "files": [],
    }
    for path, content, source in payloads:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(content)
        manifest["files"].append({
            "source": source, "path": path.relative_to(game_dir).as_posix(),
            "size": len(content), "sha256": hashlib.sha256(content).hexdigest(),
        })
    analysis = game_dir / "analysis"
    analysis.mkdir(exist_ok=True)
    (analysis / "archive-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"{game_id}: validated and expanded {len(payloads)} files into {game_dir / 'original'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--downloads", type=Path, required=True)
    args = parser.parse_args()
    for game_id, (archive_name, _) in GAMES.items():
        import_archive(args.downloads / archive_name, game_id)


if __name__ == "__main__":
    main()
