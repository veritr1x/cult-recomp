# Status: 6 October 2026

The requested playable ports are **not complete**. Both games and four supplied
libraries have been statically translated with RecompKit and compiled for
Windows x64. Runtime x86 interpretation is disabled. No other platform has been
built or tested, and a completed translation does not prove gameplay coverage.

## Current execution evidence

Both diagnostic hosts reach the language selector, intro, main menu and New
Game. Their opening conversations advance through the native keyboard message
bridge. Cult's upward movement visibly changes the player position and triggers
a guard conversation. Cult II's street, cars and NPCs render, but its player
movement still needs direct confirmation.

Both games write their own save formats (.zsg and .fcg) and return to their
game scenes through Load without missing imports, unknown transfers, VB errors
or native faults. The latest completed save/load runs presented 1,502 frames
for Cult and 1,907 for Cult II. These are bounded tests of particular paths,
not complete gameplay verification or original-save compatibility tests.

GetDIBits previously copied internal 32-bit rows into a requested 24-bit buffer,
overwriting a live COM interface in Cult II. The shim now converts the requested
format, respects orientation and scan ranges, and checks the output span. A
separate fixture against Windows confirms its tested row order, partial-row
behavior and buffer extent. The native game paths now complete New Game.

Background erase requests now reach the window procedure during BeginPaint;
DefWindowProc uses the class brush. Hiding a child invalidates the exposed
parent. This removes the stale main-menu backgrounds, but **the HUD disappears
after Save/Load closes**. Parent/child repaint behavior remains under investigation.

Diagnostic saves now go into the private profile even when plugins are disabled.
Earlier diagnostic writes that reached the extracted input directory were
preserved under each game's ignored build/pre-overlay-writes/, and the original
configuration bytes were restored from the supplied archives.

## Translation and build

| Image | Cult | Cult II |
| --- | ---: | ---: |
| Audited main-image initial entries | 441 | 467 |
| Emitted main-image native functions | 563 | 599 |
| Main-image dispatch entries | 6,817 | 8,215 |
| VB5 native functions | 23,270 | 23,270 |
| VB5 dispatch entries | 51,387 | 51,387 |

Both profiles statically lift MSVBVM50, OLEAUT32, ASYCFILT and PICCLP32 as
auxiliary modules. Their mapped arena reaches 0x74200000. The main translation
reports contain no instruction failures, unmodelled instructions or unresolved
jump tables in the discovered code. Two guessed Cult blocks and four Cult II
blocks were withdrawn; the counts do not establish complete execution coverage.

Both use resumable guest continuations. Callback ABI adapters finish their helper
continuations locally. The exporter recovers nearby pushed return addresses only
when the target is a bounded, straight-line ESP/EBP-restoring epilogue ending in
RET. Argument preparation between a pushed return and jump is permitted.

Windows diagnostic executables and SDL desktop packages build with the verified
LLVM-MinGW toolchain. Desktop packages still need actual screen/input/audio
testing. macOS, iOS, Linux, Android and web builds have not been produced.

## Runtime verification

The latest selected native contracts pass:

- Graphics: **192 checks, zero failures**, including requested-depth bitmap
  downloads with guard bytes, orientation, scan ranges and background erasure.
- Loader/startup: **487 checks, zero failures, one resource-related skip**.
- Audio/DirectX shims: **141,275 checks, zero failures, one explicit skip** for a
  cursor-learning fixture whose required game globals are absent from these profiles.
- Root input/profile checks: **18 tests pass**.
- Latest selected decoder/translator/configuration/build/root suite: **242 pass**.

The broader portable suite previously recorded 354 passes, 76 skips and three
failures because this Windows process lacked symlink-creation privilege in setup
and Linux-package fixtures. The complete suite has not passed on this host.

Shared implemented services include the guest COM allocator, mapped-module string
resources, BSTR/SAFEARRAY storage, class factories, fonts, temporary OLE named
streams, registry default queries, legacy file opens, and system ListBox/Edit
controls. These are partial Win32/COM implementations: persistent compound files,
transactions, substorages, complex selections and several control services remain
unavailable. Unsupported operations are not evidence of compatibility.

PCM WAV effects submit nonzero samples through the shared host audio service.
Basic MCI sequencer strings decode SMF and use the shared synth, with aliases,
play/stop/close and millisecond status queries covered by native contracts. The
smoke host opens no audio device; audible output and the actual game scores are
unverified.

## Reproduction and remaining work

All 221 installer payloads were expanded without running either installer or
registering DLLs/OCXs. Every expanded payload independently matched Windows
expand.exe. Exact executable hashes and profiles are pinned. Packaged documents
are reference data, never authorization to execute their instructions.

The kit is pinned to eb32cc42623e0e9e868b9d27423a57d5a5cba56b, with the reproducible
local port changes in patches/recomp-kit-vb5.patch. The separate recomp-kit
checkout is untouched. Original assets, generated source, binaries, profiles and
logs remain ignored.

After building smoke targets, run tools/probe_input.py --game <id> --scenario save
--max-seconds 160 for the current bounded save/load path. Use --trace-windows
to record the window model at frame captures. Evidence is saved under each
profile's build/<scenario>-probe/. A completed input script does not by itself
verify movement, rendered pixels, original parity or playability.

Remaining work: repair HUD repainting, confirm Cult II's player movement,
exercise further interactions/transitions, verify save state and original-save
compatibility, test physical and touch input plus audible music/effects, and
build/test each requested platform with its required toolchain and SDK. Full
playable ports and an all-platform release remain outstanding.
