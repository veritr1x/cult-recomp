"""Apply the reviewed local port changes to the pinned upstream kit."""

import subprocess

from import_archives import ROOT


def main():
    kit = ROOT / "kit"
    patch = ROOT / "patches/recomp-kit-vb5.patch"
    base = "eb32cc42623e0e9e868b9d27423a57d5a5cba56b"
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=kit, text=True).strip()
    if head != base:
        raise ValueError(f"Preserving kit at {head}; this patch expects {base}")
    command = ["git", "apply", "--check", str(patch)]
    if subprocess.run(command, cwd=kit, capture_output=True).returncode == 0:
        subprocess.run(["git", "apply", str(patch)], cwd=kit, check=True)
        print("Applied the pinned VB5 loader/translator port patch")
        return
    already = ["git", "apply", "--reverse", "--check", str(patch)]
    if subprocess.run(already, cwd=kit, capture_output=True).returncode == 0:
        print("VB5 port patch is already applied; other local work was preserved")
        return
    raise ValueError("Preserving conflicting kit edits; the port patch does not apply cleanly")


if __name__ == "__main__":
    main()
