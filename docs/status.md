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
- RecompKit emits 548 native C functions / 605 dispatch entries for Cult and
  586 functions / 654 dispatch entries for Cult II. It reports no instruction
  failures, unmodelled instructions or unresolved jump tables in this pass.
- Twelve focused input/profile/report checks pass. Complete gameplay coverage
  and numerical parity with the original games are unverified.
- Both LLVM-MinGW headless native builds finish successfully on the unchanged
  pinned kit. Both startup probes fail at the same VB5 runtime import,
  return exit code 1 and present zero frames.

## Runtime blockers

Cult imports 121 functions from `MSVBVM50.dll`; Cult II imports 122. Every one
is currently a logging-only fallback in the pinned kit. The first executed
import is ordinal 100, which resolves to `ThunRTMain` in the supplied runtime
export table. A fallback returning zero cannot construct the VB project or
start its form/event loop. Cult's native startup probe returns exit code 1,
sets no display mode and presents zero frames. The subsequent unknown target
in startup padding is a consequence of returning from this nonreturning
runtime startup call, not evidence that inventing a padding function would fix it.
Cult II reproduces the same failure at its own native entry point.

Both games have the same object structure: `GameForm`, `Module1`, `LanSet`,
and `Intro`. Cult's forms describe 62 controls; Cult II's describe 63.
Both depend on `PICCLP32.OCX` as well as COM/OLE services. Those controls and
VB's strings, variants, arrays, file I/O, exceptions, runtime calls and event
dispatch need compatible behavior before gameplay can run.

There are two substantial implementation routes to investigate:

1. Implement the required VB5 services, form/event engine and PictureClip
   control against the kit's guest-memory and host/GDI interfaces.
2. Statically lift the supplied VB runtime and control as auxiliary modules,
   then close their own Windows/COM dependency gaps and validate DLL startup.

The second route must address guest arena sizing and module mapping explicitly:
`MSVBVM50.dll` has preferred base `0x74010000`, image size `0x14d000`, and 671
PE imports; PictureClip has base `0x211a0000`, size `0x15000`, and 147 imports.
Neither is included in the current translation. Copying these x86 DLLs into
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
both the pinned kit submodule and the original kit checkout are unchanged.

## Release requirements still outstanding

Close the shared VB5/PictureClip startup and rendering gaps, then compare
menus, movement, interactions, dialogue, save/load, transitions and endings
against the original games. Verify audio and physical/touch input. Build and
test separately on Windows, Linux, macOS, Android, iOS and web, subject to the
kit's supported architectures and SDK requirements. Prepare distributable
packages only after those results establish playable behavior.
