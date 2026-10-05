# Status: 5 October 2026

The requested playable ports are **not complete**. The game binaries were
statically translated with RecompKit, and both Windows x64 diagnostic
executables have compiled and been probed. No other platform has been tested.

## Verified work

- Expanded all 221 installer payloads without running either installer or
  registering system libraries. Every file matches Windows `expand.exe`.
- Confirmed native x86 VB5 compilation from the startup header and its nonzero
  project native-code pointer.
- Pin exact executable hashes, entry points and profiles; original game inputs,
  generated source, binaries and logs remain ignored.
- Export native listings using actual VB event/method pointers and direct x86
  control-flow edges: 420 initial entries for Cult, 444 for Cult II.
- RecompKit emits 549 native C functions / 606 dispatch entries for Cult and
  587 functions / 655 dispatch entries for Cult II. It reports no instruction
  failures, unmodelled instructions or unresolved jump tables in this pass.
- Fifteen focused input/profile/report checks pass. Complete gameplay coverage
  and numerical parity with the original games are unverified.
- Both LLVM-MinGW headless native builds link with four statically translated
  supplied libraries on the locally patched kit. Probes enter the actual
  VB startup routine. Both complete 150-frame offscreen captures with no called
  missing imports or unknown transfers; this is not a gameplay test.

## Runtime blockers

The ongoing second pass adds four supplied dependencies as statically translated
auxiliary modules in each profile. The arena reaches `0x74200000`, and runtime
x86 interpretation is explicitly disabled. The local kit maps all DLLs before
binding imports and initializes static dependencies before the executable.
The real Cult image passes 433 loader/startup contract checks (zero failures,
one resource-related skip). Decoder, switch, return-path and profile checks pass:
256 focused translator/profile/build/private-input checks in the latest run.
The latest Cult VB5 pass emits 23,150 discovered routines and 25,172 dispatch
entries; Cult II regeneration is ongoing. PictureClip emits 580 routines.
Branch-pruning fixes include regressions for split epilogues and listing gaps.
The translator also preserves shared VB interface adjustors whose method body
has a separate vtable entry, plus all 1,024 indexed interface CALL thunks whose
dispatcher consumes the return address. Unknown indirect jumps now honor the
interpreter-disable setting. Fixed generated heap callback templates dispatch
the native interface resolver and reference-owning object getter through ABI
adapters. The native GDI suite passes 173 checks, including region subtraction,
clipping that retains holes, anisotropic picture mapping, plain ANSI text and
matching ANSI/UTF-16 measurements from the selected font.
The broader portable suite records 354 passes, 76 skips and three failures:
this Windows process lacks the privilege to create the symlinks in the setup
and Linux package fixtures. That complete suite has not passed on this host.
Neither game has reached verified gameplay.

Both probes now complete the statically translated VB5 DLL's process attach,
then execute `ThunRTMain`. Implemented startup services include a guest COM task
allocator, mapped-module string resources, wide string comparison, and OLE
Automation's named/ordinal bindings, binary BSTRs, and caller-created SAFEARRAY
storage. Probes create VB's main, component-manager and focus windows and reach
native object dispatch. Both execute the supplied OLE Automation library's
font construction. Cult creates its language-selection form, radio buttons and
frame after fixing ANSI icon loading and adding the system Button procedure.
Its picture construction uses ASYCFILT, now translated as a fourth module.
Automation's seven image-filter vtable methods have been audited and seeded.
Both language forms are created, and Cult reaches translated game initialization.
Both latest native probes carry the complete interface table and finish 150
presented frames with no called missing imports or unknown transfers. Captures
show language-selection forms, titles, flags, character artwork and the Play
label. Anisotropic GDI mapping now renders the supplied OLE pictures.
Dynamic sound exports now bind and report unavailable playback rather than
throwing a missing-entry-point exception.
MIDI and WAV assets use `.dat` filenames; actual media playback remains unfinished.
Offscreen frames have been inspected. Scripted desktop coordinates now route
through the same native input bridge as host mouse events. English-selection
and Play clicks advance both games into intro processing. Legacy file/path
APIs and two additional audited callbacks are translated or implemented.
The temporary OLE storage service is now implemented with named streams,
read/write/seek, cloning, copying and ownership. Native Windows conformance
probes confirm stream invalidation after element deletion and parent release.
Persistent compound files, transactions and substorages remain unsupported.
Both last completed input probes successfully use that service. Audited VB
window/shutdown callbacks and Cult II exception cleanup are now translated.
System ListBox and Edit controls initialize with owned text/items, selection,
typing limits, read-only state, undo and parent notifications. They are partial
Win32 implementations: clipboard, scrolling and complex selection remain open.
The last probes fail with VB error 321 (Invalid file format) after an uncovered
form-loader property callback (`0x74056080`) and unsupported Edit margin message.
The margin message is implemented and tested; the property callback is audited
and translated. Updated executable checks are ongoing. The last script does
not complete; gameplay remains unverified. Input evidence is recorded
under each profile's private `build/input-probe/` directory.
The remaining work includes callback coverage, physical input, audio,
save/load and gameplay verification.

Both games have the same object structure: `GameForm`, `Module1`, `LanSet`,
and `Intro`. Cult's forms describe 62 controls; Cult II's describe 63.
Both depend on `PICCLP32.OCX` as well as COM/OLE services. Those controls and
VB's strings, variants, arrays, file I/O, exceptions, runtime calls and event
dispatch need compatible behavior before gameplay can run.

The selected route lifts the supplied VB runtime and control as auxiliary
modules, then closes their Windows/COM dependency gaps. This requires guest
arena sizing and module mapping explicitly:
`MSVBVM50.dll` has preferred base `0x74010000`, image size `0x14d000`, and 671
PE imports; PictureClip has base `0x211a0000`, size `0x15000`, and 147 imports.
Both are now configured for static translation. Copying these x86 DLLs into
a package would not make them execute natively on ARM or non-Windows targets.

## Verification records

Each profile has private `analysis/archive-manifest.json`, `pe-report.json`,
`import-verification.json`, `translation-report.json`, and `llvm-build.log`.
Native startup evidence goes into `build/probe/startup.log` and `result.json`.
These files are deliberately untracked because they contain private binary
metadata, generated outputs or run logs.

Re-run a startup diagnostic after building:

```powershell
.venv\Scripts\python.exe tools\probe_startup.py --game all
```

The probe returns a failure when it encounters unresolved imports, a failed
process or zero frames. Even a later successful probe is not a gameplay test.
The portable LLVM-MinGW diagnostic builds use compiler runtime DLLs from the
toolchain's `bin` directory; the probe adds that directory to its own PATH.
The diagnostic executables are not standalone player packages.

The local GCC experiment compiled Cult's generated C archive but failed to
link the kit's complete host. Its temporary runtime edits were reverted;
the original kit checkout is unchanged. The game's local kit submodule now has
the loader and translator changes described above.

## Release requirements still outstanding

Close the shared VB5/PictureClip startup and rendering gaps, then compare
menus, movement, interactions, dialogue, save/load, transitions and endings
against the original games. Verify audio and physical/touch input. Build and
test separately on Windows, Linux, macOS, Android, iOS and web, subject to the
kit's supported architectures and SDK requirements. Prepare distributable
packages only after those results establish playable behavior.
