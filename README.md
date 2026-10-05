# Cult / Cult II RecompKit bring-up

**Incomplete: these are experimental static recompilation projects, not playable ports.**
Both supplied games contain native x86 code compiled with Visual Basic 5.
Their game code has been translated to C with RecompKit. Native gameplay,
save compatibility, audio, input and other platforms are not yet verified.
Both Windows x64 headless executables compile, but startup probes fail at
unimplemented VB5 `ThunRTMain`, with zero frames presented.
The deadline requested was 6 October 2026; an all-platform playable release
by that date cannot be promised from the current state.

RecompKit is pinned as the `kit/` submodule to
`eb32cc42623e0e9e868b9d27423a57d5a5cba56b`.
The existing `C:/GitRepos/recomp-kit` checkout was not modified.

| Profile | Original executable | Emitted native functions | Dispatch entries |
| --- | --- | ---: | ---: |
| `games/cult` | `Cult.exe` | 548 | 605 |
| `games/cult2` | `Cult2FC.exe` | 586 | 654 |

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
.venv\Scripts\python.exe tools\import_archives.py --downloads C:\Users\satta\Downloads
.venv\Scripts\python.exe tools\analyze_games.py
.venv\Scripts\python.exe tools\prepare_profiles.py
.venv\Scripts\python.exe tools\export_native.py --kit .\kit
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

## Other targets

After the shared runtime gaps are resolved, `tools/build.py --game <id>`
forwards `--target app`, `android`, `ios` or `web` to RecompKit.
macOS and iOS require Apple tooling on a Mac; Android requires its SDK/NDK;
web requires Emscripten and the kit's WebGPU/browser requirements.
Linux and other CPU architectures need their own native builds and gameplay
verification. No binaries for these targets have been produced here.

## Metadata references

The VB project/object/event layout was checked against the primary
[python-vb parser source](https://github.com/williballenthin/python-vb/blob/master/vb/__init__.py)
and the [Semi VB Decompiler structure definitions](https://github.com/VBGAMER45/Semi-VB-Decompiler/blob/master/Semi%20VB%20Decompiler/modGlobals.bas).
The zero/nonzero native-code flag is described by the
[VB Decompiler author](https://www.vb-decompiler.org/pcode_decompiling.htm).
The scripts use those format facts; upstream code is not vendored.
