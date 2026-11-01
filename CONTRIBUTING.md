# Contributing

This repo holds the two Cult game profiles and their preparation/validation
tools. Shared runtime and translator changes belong in recomp-kit. Remaining
VB5/OLE/GDI changes are carried as a source patch against the published kit pin.
Keep that patch reproducible and describe its validation when changing it.

## Prerequisites

- Python 3.12, Git and the hashed `kit/requirements.lock` tooling environment.
- Windows: LLVM plus the Windows SDK/Visual Studio developer environment, or
  the optional hash-verified LLVM-MinGW toolchain described below.
- Linux: clang, lld, pkg-config and SDL development headers listed in
  `kit/.github/workflows/checks.yml`.
- macOS/iOS: Xcode and its SDKs; stub compilation is separate from game runtime
  verification. No new Apple-device runtime claim is made for these profiles.
- Real builds: your own exact game archives and auxiliary libraries, prepared
  as described in [README.md](README.md). CI uses no game files.

## Build

After applying the kit patch and preparing inputs, use `tools/build.py --game
cult --target app` or `--game cult2`. `--game all` builds both. Every native
compile goes through the kit build API. `--translate-only` publishes the main
image and all auxiliary modules transactionally; never edit generated C.

The optional Windows diagnostic toolchain remains local:

```powershell
.venv/Scripts/python.exe tools/bootstrap_llvm.py
.venv/Scripts/python.exe tools/configure_mingw.py --toolchain ./build/toolchains/llvm-mingw-20260922-ucrt-x86_64
.venv/Scripts/python.exe tools/build.py --game all --preset cult-windows-llvm --target smoke
```

That preset disables video. Set PATH to the virtual environment's Scripts
folder and the selected compiler's bin folder for its runtime DLLs.

## Validate and submit

Run `tools/test.py`, `python -m pytest -q tests`, and `tools/check_repo.py`.
See [docs/testing.md](docs/testing.md) for native and real-game checks.
Describe the concrete behavior, tests and limits in each PR; update
[CHANGELOG.md](CHANGELOG.md). Follow [AGENTS.md](AGENTS.md) for source boundaries.

Do not publish game media, dependencies, generated translations, builds,
personal profiles or logs. The source license does not relicense the games.
