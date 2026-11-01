# Cult Recomp

[Build & contribute](CONTRIBUTING.md) · [Port analysis](docs/analysis.md) ·
[Testing](docs/testing.md) · [Changelog](CHANGELOG.md)

Static recompilations of **Cult** and **Cult II: Federal Crime**, built with
[recomp-kit](https://github.com/veritr1x/recomp-kit). Each game's x86 executable
and four supporting libraries are translated to native C ahead of time.
Runtime x86 interpretation is disabled. Windows and Linux desktop and WebGPU
browser builds have bounded local verification; full playthroughs remain
unverified. See the analysis notes for platform-specific evidence.

**You need your own copies of the games.** Original executables, DLLs/OCXs,
artwork, music, generated translations, binaries and saves are not included.
The original games are by Lee Blum; see the [official Cult II site](https://www.studio-blum.com/Cult2/)
and [NOTICE](NOTICE). This is an independent compatibility project.

## Repository layout

| Path | Contents |
| --- | --- |
| `kit/` | Published recomp-kit, pinned as a git submodule |
| `games/cult/`, `games/cult2/` | Exact-image `game.toml`, curated globals and smoke scripts |
| `patches/recomp-kit-vb5.patch` | Remaining shared VB5/OLE/GDI source extensions |
| `tools/` | Game input preparation and thin kit build/test entry points |
| `tests/` | Asset-free configuration, importer and probe contracts |
| `docs/` | Analysis, validation and historical bring-up notes |

Game inputs, listings and outputs stay in each profile's ignored `original/`,
`analysis/` and `build/`. The two related games share a repo and kit pin; their
identity, inputs, output directories and profiles remain separate.

## Prepare the checkout

Use Python 3.12 and Git. On Windows, replace `.venv/bin/python` with
`.venv/Scripts/python.exe`.

```sh
git clone --recurse-submodules https://github.com/veritr1x/cult-recomp.git
cd cult-recomp
python3 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r kit/requirements.lock
.venv/bin/python tools/apply_kit_patches.py
```

The kit pin is `a18ccafa1e8c98002b2d3f7347b64fa655ebb018`, the merged,
reviewed runtime/renderer/translator update. The patch is published here so no
unpublished submodule commit is needed. Its helper validates the exact base,
accepts an already applied patch and preserves conflicting local edits.

## Prepare your game copies

Place your own `Cult_Win_EN.zip` and `Cult-II-Federal-Crime_Win_EN.zip` in a
local directory, then run:

```sh
.venv/bin/python tools/import_archives.py --downloads /path/to/your/archives
.venv/bin/python tools/export_native.py --kit ./kit
.venv/bin/python tools/prepare_modules.py
.venv/bin/python tools/build.py --game all --translate-only
.venv/bin/python tools/test_inputs.py
```

The importer expands installer payloads without executing an installer or
registering DLLs/OCXs. Preparation validates exact executable/module hashes.
Native export uses the kit decoder and verified VB metadata; it is this port's
alternative to Ghidra listings. Do not regenerate the reviewed `game.toml`
profiles with `prepare_profiles.py` for an ordinary build.

## Build and check

Install the native prerequisites listed in [CONTRIBUTING.md](CONTRIBUTING.md).
Build one profile, or select `--game all`:

```sh
.venv/bin/python tools/build.py --game cult --target app
.venv/bin/python tools/build.py --game cult2 --target app
.venv/bin/python tools/test.py
.venv/bin/python -m pytest -q tests
.venv/bin/python tools/check_repo.py
```

All remaining kit build options pass through, including `--stub`, `--preset`,
`--regenerate` and `--jobs`. A stub build needs no original inputs:
`tools/build.py --game all --stub`. The patch must be applied first.

For bounded save/load checks, build each smoke host and run
`tools/probe_input.py --game all --scenario save --max-seconds 120`.
The probe records fresh writes, equal restored serialized state and changed
player positions. It uses isolated diagnostic profiles. See
[testing](docs/testing.md) before repeating existing local probes.

Private desktop folders assembled by `tools/package_player.py` include their
own launchers and writable profiles. They are local outputs, never repository
or release payloads. Historical browser/mobile packaging helpers and their
verification limits are described in [docs/status.md](docs/status.md).
