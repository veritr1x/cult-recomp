"""Download a checksum-pinned portable LLVM-MinGW compiler into ignored build/."""

import hashlib
import json
import urllib.request
import zipfile

from import_archives import ROOT

NAME = "llvm-mingw-20260922-ucrt-x86_64"
SHA256 = "e3ad77d117a4bea19a7a3b333341824d79a5a371004a10e25b8504e7b3047666"
URL = f"https://github.com/mstorsjo/llvm-mingw/releases/download/20260922/{NAME}.zip"


def main():
    directory = ROOT / "build/toolchains"
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / (NAME + ".zip")
    if not archive.exists():
        temporary = archive.with_suffix(".download")
        urllib.request.urlretrieve(URL, temporary)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != SHA256:
            raise ValueError("Compiler download checksum differs from the pinned GitHub asset")
        temporary.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise ValueError("Preserving invalid existing compiler archive; checksum differs")
    with zipfile.ZipFile(archive) as zipped:
        for item in zipped.infolist():
            if not (directory / item.filename).resolve().is_relative_to(directory.resolve()):
                raise ValueError("Compiler archive entry escapes build/toolchains")
        zipped.extractall(directory)
    (directory / "llvm-provenance.json").write_text(json.dumps({
        "url": URL, "sha256": SHA256, "version": "LLVM 23.1.2 / LLVM-MinGW 20260922",
    }, indent=2) + "\n")
    print(directory / NAME)


if __name__ == "__main__":
    main()
