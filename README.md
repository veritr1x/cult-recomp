# Cult / Cult II RecompKit bring-up

**Experimental ports: full gameplay and an all-platform release remain incomplete.**
Both games contain native x86 code compiled with Visual Basic 5. Their code and
four supporting libraries are statically translated to C with RecompKit;
runtime x86 interpretation is disabled.

Windows x64 and Linux x86_64 diagnostic builds reach the language selector,
intro, main menu and opening scenes. Both games pass fresh movement/save/load
checks on both systems, including byte-for-byte restoration of serialized state.
Cult II's player now renders; its inventory icon is temporarily blank after
loading and returns on the next movement input.

SDL desktop packages build for Windows and Linux. Both games completed bounded
20-second startups with Vulkan presentation, nonzero device PCM and clean exits.
Windows Cult II required DirectSound for its audio device. WSL runs use X11,
100 ms PulseAudio latency and an 8,192-frame audio backlog; both reported zero
late or starved audio pulls. Default WSL backends previously exposed intermittent
startup/cleanup hangs, so these results apply to the tested settings. All 49 original
MIDI scores produce nonzero audio through the offline MCI mixer. Physical input,
audible output and later desktop gameplay remain unverified.

Private local player folders include the supplied data and Play.cmd or Play.sh.
Windows launchers select DirectSound unless overridden; Linux launchers apply
the tested settings under WSL while preserving explicit overrides.
The deadline requested was 6 October 2026; an all-platform playable release by
that date cannot be promised from the current state.

RecompKit is pinned as the `kit/` submodule to
`eb32cc42623e0e9e868b9d27423a57d5a5cba56b`.
The local submodule carries the port patch in `patches/recomp-kit-vb5.patch`
on top of that revision. The separate `C:/GitRepos/recomp-kit` checkout was not
modified. The patch is included here so a clean checkout can reproduce the kit
changes without fetching an unpublished submodule commit.

| Profile | Original executable | Emitted native functions | Dispatch entries |
| --- | --- | ---: | ---: |
| `games/cult` | `Cult.exe` | 563 | 6,817 |
| `games/cult2` | `Cult2FC.exe` | 599 | 8,215 |

Both profiles enable RecompKit's resumable guest continuations. Native calls
propagate a changed guest return address to the dispatch driver, and the
exporter recovers verified VB frame epilogues named by nearby pushed returns.

Both translation reports contain zero reported instruction failures,
zero unmodelled instructions and zero unresolved jump-table sites. These
counts describe the discovered code, not a proof of complete execution coverage.
Two guessed blocks in Cult and four in Cult II were withdrawn by the translator.

## Reproduce the private inputs and translation

Requires Python 3.12+, Git and the user's two supplied ZIP archives.
No installer is launched and no DLL/OCX is registered on the machine.
Instructions in packaged documents and installer registration directives are
never treated as authorization or executed.

```powershell
git submodule update --init
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe tools\apply_kit_patches.py
.venv\Scripts\python.exe tools\import_archives.py --downloads C:\Users\satta\Downloads
.venv\Scripts\python.exe tools\analyze_games.py
.venv\Scripts\python.exe tools\prepare_profiles.py
.venv\Scripts\python.exe tools\export_native.py --kit .\kit
.venv\Scripts\python.exe tools\prepare_modules.py
.venv\Scripts\python.exe tools\build.py --translate-only
.venv\Scripts\python.exe tools\test_inputs.py
```

The importer decompresses the SZDD payloads and uses `SETUP.LST` only to
map filenames. Game files go under each profile's ignored `original/install/`;
system dependencies go under `original/dependencies/`. They are not installed
into Windows system directories. Some installer data lengths are stale;
the actual SZDD header lengths are checked and discrepancies are recorded.
All 111 Cult payloads and 110 Cult II payloads have independently matched
Windows `expand.exe` byte for byte:

```powershell
.venv\Scripts\python.exe tools\verify_imports.py --downloads C:\Users\satta\Downloads
```

The native exporter uses the kit's recursive x86 decoder, seeded from the PE
entry and VB method/event tables. It is a bootstrap alternative to Ghidra
listings, with provenance in `functions.tsv`; it does not export decompiler
pseudocode. Additional dynamically discovered callbacks still need auditing.
`prepare_modules.py` exports DLL entries, direct edges and switch arms and pins
their hashes in each profile. It copies the four mapped module images and the
supplied standard OLE type library beside each executable so portable bundles
can find their guest data. These remain
private inputs and are never registered with Windows.

## Diagnostic Windows builds

Use the kit's standard `windows` preset with LLVM and the Windows SDK, or
the verified portable LLVM-MinGW compiler used in this workspace:

```powershell
.venv\Scripts\python.exe tools\bootstrap_llvm.py
.venv\Scripts\python.exe tools\configure_mingw.py --toolchain .\build\toolchains\llvm-mingw-20260922-ucrt-x86_64
$env:Path = "$PWD\.venv\Scripts;$PWD\build\toolchains\llvm-mingw-20260922-ucrt-x86_64\bin;$env:Path"
.venv\Scripts\python.exe tools\build.py --game all --preset cult-windows-llvm --target headless
```

The portable toolchain is downloaded from its
[upstream release](https://github.com/mstorsjo/llvm-mingw/releases/tag/20260922)
and verified against a pinned SHA-256 before extraction. It remains under ignored
`build/toolchains/`; it does not change global tool installations. This diagnostic
preset disables FFmpeg. Native builds use `kit/tools/build.py` exclusively.

Generated C and binaries remain private under `games/<id>/build/`.
An emitted library or headless executable does not establish playability.
See [status and remaining work](docs/status.md) for verification and blockers.

The smoke host also checks input through the native window-message path:

```powershell
.venv\Scripts\python.exe tools\build.py --game all --preset cult-windows-llvm --target smoke
.venv\Scripts\python.exe tools\probe_input.py --game all --verbose
```

Both games render their language screens, including artwork and the Play label,
and the scripted clicks advance into the intro. Temporary OLE storage is now
implemented. System ListBox and Edit controls now initialize. The last completed
input probes now activate PictureClip's native class factory and load pictures
through OLE memory streams. The uncovered VB, Automation and cleanup callbacks
now execute. DLL-name comparison and legacy file opens are implemented, and the
standard OLE type library is included as guest-readable data. Both short probes
finish with no called missing imports, unknown transfers, VB errors or access
violations. Longer probes exercise New Game, dialogue, movement and Save/Load.
GetDIBits now honors the caller's pixel depth and row count, fixing a buffer
overrun that corrupted Cult II's interface objects. Background erasure removes
retained menu pixels. Paints clip to accumulated update rectangles, preserving
the HUD when dialogs close. Hidden helper controls no longer draw into visible
parent surfaces. Save/load probes use a writable private profile even with
plugins disabled, and reject stale files or an unchanged test position.
Both probes submit three WAV effects with nonzero audio samples. Bounded
movement and save/load paths pass; full gameplay and audible device output
remain unverified.

## Linux builds

Both Linux x86_64 movement/save/load probes pass under Ubuntu in WSL.
Both SDL packages also build; desktop startup and cleanup remain under validation.
Use a separate Linux virtual environment; a Windows virtual environment cannot
run the Linux build tools. Install clang, lld, Python venv, pkg-config and SDL's
development dependencies as listed in `kit/.github/workflows/checks.yml`.
After importing and translating the inputs above:

```sh
python3 -m venv build/linux-venv
build/linux-venv/bin/python -m pip install -r kit/requirements-dev.txt
export PATH="$PWD/build/linux-venv/bin:$PATH"
for game in cult cult2; do
  build/linux-venv/bin/cmake --preset linux -S kit -B "games/$game/build/cmake/linux" \
    -DRECOMP_GAME_DIR="$PWD/games/$game" -DPOP_BUILD_ROOT="$PWD/games/$game/build" \
    -DRECOMP_VIDEO=OFF
  build/linux-venv/bin/python tools/build.py --game "$game" --preset linux --target smoke
  build/linux-venv/bin/python tools/probe_input.py --game "$game" --scenario save \
    --max-seconds 210 --host-keyboard
  build/linux-venv/bin/python tools/build.py --game "$game" --preset linux --target app
done
```

Video is disabled in these builds. Diagnostic output goes under each game's
ignored `build/`; Linux save probes replace the same evidence paths used by
Windows probes. A successful scripted test does not establish complete gameplay.

Private local player folders can be assembled from the builds and supplied
inputs with tools/package_player.py --game <id> --platform Windows (or Linux).
They go under ignored build/player/ and include Play.cmd or Play.sh plus a
separate writable profile directory. Keep the complete player folder together.

## Other targets

After the shared runtime gaps are resolved, `tools/build.py --game <id>`
forwards `--target app`, `android`, `ios` or `web` to RecompKit.
macOS and iOS require Apple tooling on a Mac; Android requires its SDK/NDK;
web requires Emscripten and the kit's WebGPU/browser requirements.
Other CPU architectures need their own native builds and gameplay verification.
No macOS or iOS binaries have been produced here yet. Both Android ARM64 debug
APKs build and are packaged privately under `build/player/android/`.

Both browser builds linked with Emscripten 6.0.11 on Linux x86_64.
The local emsdk checkout is pinned to
`96c657fc60920d2a6a82318aa50e0abf82749604`, whose SDK release revision is
`f6264d4a4dd9ba24a9f0a5702835a44d1463de13`. It stays under ignored
`build/toolchains/emsdk/`. To repeat a browser build after installing and
activating that SDK version, use Bash:

```sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
source build/toolchains/emsdk/emsdk_env.sh
export PATH="$PWD/build/linux-venv/bin:$PATH"
build/linux-venv/bin/python kit/tools/build.py --game-dir "$PWD/games/cult" --target web --jobs 3
build/linux-venv/bin/python kit/tools/build.py --game-dir "$PWD/games/cult2" --target web --jobs 3
```

`tools/package_browser.py` assembles both private players under
`build/player/web/`, including local ZIP copies for importing the supplied data.
It strips only WebAssembly debug metadata and checks that every executable
section remains unchanged. Both games import their supplied data, reach their
language screens through WebGPU and initialize the packaged MIDI bank. A runtime
mouse-state fix lets ordinary Play clicks start both games. Keyboard input reaches
the opening scenes and advances their conversations. Later movement/menu input
can leave blank or stale frames; browser save/load and full gameplay remain
unverified. The guest arena extends
to 0x74200000, so its browser memory
requirements need actual device testing. The kit's player requires a secure,
cross-origin isolated page and a WebGPU-capable browser.

tools/bootstrap_android.py stages checksum-pinned Windows-hosted NDK r30,
Android API 36 revision 2 and Build Tools 37.0.0 under ignored build/toolchains/.
It requires the existing installed Android API 35 package and verifies that the
repository's associated license text matches its accepted agreement apart from
whitespace. It refuses changed terms or unexpected package checksums. Android
configuration and APK assembly succeeded for both games. `tools/package_android.py`
checks the ARM64 library and required runtime assets, then copies the APKs and
notices into `build/player/android/`. Both install and load their libraries on an
isolated emulator using ARM64 translation. Its Vulkan driver lacks dynamic
rendering, so startup stops at the launcher before gameplay. Physical ARM64
device execution, touch input and audible output remain unverified.

## Metadata references

The VB project/object/event layout was checked against the primary
[python-vb parser source](https://github.com/williballenthin/python-vb/blob/master/vb/__init__.py)
and the [Semi VB Decompiler structure definitions](https://github.com/VBGAMER45/Semi-VB-Decompiler/blob/master/Semi%20VB%20Decompiler/modGlobals.bas).
The zero/nonzero native-code flag is described by the
[VB Decompiler author](https://www.vb-decompiler.org/pcode_decompiling.htm).
The scripts use those format facts; upstream code is not vendored.
