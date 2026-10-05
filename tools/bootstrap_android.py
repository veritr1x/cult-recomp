"""Stage pinned Windows Android packages using the already accepted SDK agreement."""

import hashlib
import json
import os
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from import_archives import ROOT

REPOSITORY = "https://dl.google.com/android/repository/"
PACKAGES = {
    "ndk;30.0.16248370": ("android-ndk-r30-windows.zip", "9bf167a1985fa7d4a036186b78f702eab9179408", "ndk/30.0.16248370"),
    "platforms;android-36": ("platform-36_r02.zip", "2c1a80dd4d9f7d0e6dd336ec603d9b5c55a6f576", "platforms/android-36"),
    "build-tools;37.0.0": ("build-tools_r37_windows.zip", "e9c97e26b5b5678002e9d3fed632c841ae62d99f", "build-tools/37.0.0"),
}


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha1").hexdigest()


def normalized(text):
    return re.sub(r"\s+", " ", text).strip()


def main():
    if os.name != "nt":
        raise SystemExit("This bootstrap stages the Windows-hosted Android toolchain")
    installed = Path(os.environ["LOCALAPPDATA"]) / "Android/Sdk"
    accepted = set((installed / "licenses/android-sdk-license").read_text().split())
    local = ET.parse(installed / "platforms/android-35/package.xml").getroot()
    local_license = next(item.text for item in local if item.tag.split("}")[-1] == "license")
    if hashlib.sha1(local_license.encode()).hexdigest() not in accepted:
        raise ValueError("The installed SDK package's agreement has no accepted license record")
    data = urllib.request.urlopen(REPOSITORY + "repository2-3.xml", timeout=60).read()
    document = ET.fromstring(data)
    remote_license = next(item.text for item in document if item.attrib.get("id") == "android-sdk-license")
    if normalized(remote_license) != normalized(local_license):
        raise ValueError("SDK agreement terms changed; explicit user acceptance is required before downloading")
    sdk = ROOT / "build/toolchains/android-sdk"
    downloads = ROOT / "build/toolchains/android-downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    (downloads / "repository.xml").write_bytes(data)
    records = []
    for package_id, (filename, checksum, relative) in PACKAGES.items():
        package = next(item for item in document if item.attrib.get("path") == package_id)
        license_ref = next(item.attrib["ref"] for item in package.iter() if item.tag.split("}")[-1] == "uses-license")
        if license_ref != "android-sdk-license":
            raise ValueError(f"{package_id} requires a different agreement")
        archives = [item for item in package.iter() if item.tag.split("}")[-1] == "archive"]
        selected = None
        for archive_info in archives:
            fields = {item.tag.split("}")[-1]: item.text for item in archive_info.iter()}
            if fields.get("host-os", "windows") == "windows" and fields.get("url") == filename:
                selected = fields
                break
        if not selected or selected.get("checksum") != checksum:
            raise ValueError(f"{package_id} no longer matches the pinned upstream archive")
        archive = downloads / filename
        if not archive.is_file():
            temporary = archive.with_suffix(".download")
            print(f"Downloading {package_id}", flush=True)
            urllib.request.urlretrieve(REPOSITORY + filename, temporary)
            if digest(temporary) != checksum:
                raise ValueError(f"{filename} download checksum mismatch; preserving it for inspection")
            temporary.replace(archive)
        if digest(archive) != checksum:
            raise ValueError(f"Existing {filename} checksum mismatch; preserving it")
        destination = sdk / relative
        marker = destination / ".recomp-bootstrap.json"
        record = {"package": package_id, "url": REPOSITORY + filename, "sha1": checksum}
        if destination.exists() and any(destination.iterdir()):
            if not marker.is_file() or json.loads(marker.read_text()) != record:
                raise ValueError(f"Preserving unmanaged contents at {destination}")
        destination.mkdir(parents=True, exist_ok=True)
        marker.write_text(json.dumps(record, indent=2) + "\n")
        with zipfile.ZipFile(archive) as source:
            entries = source.infolist()
            roots = {item.filename.split("/")[0] for item in entries}
            if len(roots) != 1:
                raise ValueError(f"Unexpected archive roots in {filename}")
            for item in entries:
                parts = item.filename.replace("\\", "/").split("/")[1:]
                if not parts or not any(parts):
                    continue
                target = destination.joinpath(*parts)
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise ValueError(f"Archive entry escapes destination: {item.filename}")
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with source.open(item) as read, target.open("wb") as write:
                        shutil.copyfileobj(read, write)
        records.append(record)
        print(f"Staged {package_id}: {destination}", flush=True)
    (sdk / "licenses").mkdir(exist_ok=True)
    shutil.copy2(installed / "licenses/android-sdk-license", sdk / "licenses/android-sdk-license")
    (sdk / "bootstrap-info.json").write_text(json.dumps({
        "packages": records, "accepted_installed_license": hashlib.sha1(local_license.encode()).hexdigest(),
        "repository_license_diff": "whitespace only; canonical text matches installed accepted agreement",
    }, indent=2) + "\n")
    print(sdk)


if __name__ == "__main__":
    main()
