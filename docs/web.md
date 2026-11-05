# Browser build and optional streaming

Use this repository's pinned `kit/`, your own hash-matched installation, and
the preparation/analysis steps in [CONTRIBUTING.md](../CONTRIBUTING.md).
Install the kit's hashed Python requirements and activate Emscripten 6.0.11.
On Windows, use `.venv/Scripts/python.exe` instead of `.venv/bin/python`.

```sh
.venv/bin/python tools/apply_kit_patches.py
.venv/bin/python tools/build.py --game all --target web --jobs 4
.venv/bin/python kit/tools/web_launcher.py \
    --game-dir "$PWD/games/cult" --game-dir "$PWD/games/cult2" \
    --out build/web-stream-site \
    --web-build cult=games/cult/build/web/recomp \
    --web-build cult2=games/cult2/build/web/recomp \
    --stream cult --stream cult2 --serve 2028
```

After the first translation, omit `--regenerate` when translator inputs have
not changed. Open `http://127.0.0.1:2028/` and choose **Stream game**.
The command stages a private installation and manifest into the site. It
preserves executable/module hash checks, bundle exclusions and prepared
auxiliary modules. Original installation files are unchanged.

If analysis uses a minimal executable copy, select the full installation
explicitly: replace `--stream cult` with
`--stream "cult=/path/to/full installation"`. That directory must contain
the configured executable with its pinned hash and required data folders.
This changes the staging source only, preserving configured analysis inputs.
Keep generated game data and all local evidence private.

The worker mounts game files read-only at `/data`, using 4 MiB HTTP ranges
and a 64 MiB download cache. This is a cache bound, not total browser memory.
The kit supplies a corrected fetch backend without modifying the installed
SDK. Saves and settings use a separate writable OPFS profile.

**Import folder**, ZIP import and **Play** remain available. Play uses an
imported installation; Stream game selects hosting explicitly. Direct player
URLs prefer imported data when available. Both modes share saves on the same
origin. For games with prepared auxiliary modules, import a prepared bundle
with the pinned modules at their configured names; the staged `data/` folder
is such a bundle. A raw install may keep those modules elsewhere.

To prepare an import-only site, use a separate `--out` directory and omit
`--stream`. Previously staged assets are not removed by omitting the flag.
The server supplies HEAD, byte ranges, Wasm MIME and COOP/COEP. Other hosting
must preserve those semantics and same-origin asset URLs; files larger than
64 MiB require ranges. Streaming has no persistent offline asset cache.

Keep the hostname and port consistent to reuse saves. Export saves from
**Manage** before clearing site storage. Browser compatibility results are
recorded below; compilation alone does not establish gameplay.

## Local validation

Shared kit pin: `1cbd81ca8e6e1ef2cf33f1c27a06f69a00e64b82`.

On Windows/Chromium 145 with hardware WebGPU, fresh streamed profiles reached
both Cult and Cult II gameplay with the four supporting modules verified by
the loader. Cult exposed 101 files and Cult II 100. After moving in each game,
loading the earlier slot and saving into a second slot produced byte-identical
54-byte Cult and 124-byte Cult II saves; the intervening moved saves differed.
Neither streaming run copied game assets into OPFS, and neither produced a
JavaScript exception, failed asset request or WebGPU validation error.

Cult also imported its prepared installation through the normal Import folder
control, booted with source `import`, issued zero streamed asset GETs and kept
the existing saves. The final rebuilt Cult player was also reimported: the hub retained Ready
after reload and Play booted source `import` with zero asset GETs. Cult II
folder import was not separately rerun. These are
bounded local checks, not full playthroughs or proof of browser-restart save
persistence. Audible output and other browsers remain unverified.

The real Emscripten 6.0.11 builds pass for both profiles. All 18 portable
project tests and four focused patched-kit native suites pass. An archive of
the final kit base accepts the source patch and its reverse check, and matches
the active patched native/tool sources. Applying the helper again preserves
the already applied patch. Private logs, saves and screenshots stay ignored.
