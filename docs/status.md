# Status: 6 October 2026

The requested playable ports are **not complete**. Both games and four supplied
libraries have been statically translated with RecompKit and compiled for
Windows x64. Both Linux x86_64 diagnostic executables also build and pass
the bounded movement/save/load path under Ubuntu in WSL. Runtime x86
interpretation is disabled; a completed translation does not prove gameplay coverage.

## Current execution evidence

Both diagnostic hosts reach the language selector, intro, main menu and New
Game. Their opening conversations advance through the native keyboard message
bridge. Cult's upward movement visibly changes the player position and triggers
a guard conversation. Cult II's street, cars, NPCs and player now render. The
player visibly moves and appears again after loading a saved game.

Both games write their own save formats (.zsg and .fcg) and return to their
game scenes through Load without missing imports, unknown transfers, VB errors
or native faults. The latest completed save/load runs presented 2,055 frames
for Cult and 2,510 for Cult II. These are bounded tests of particular paths,
not complete gameplay verification or original-save compatibility tests.
Cult's stronger test now verifies movement from (267,60) to (267,90), then
restoration to (267,60), with fresh saves before and after loading matching
byte for byte. Cult II's test likewise verifies movement from (407,160) to
(437,160), then restoration to (407,160), with fresh saves matching byte for
byte. Both repeat this test successfully on Linux x86_64 through the desktop
keyboard gate, with 2,055 frames for Cult and 2,510 for Cult II.
Cult II's inventory icon is blank immediately after loading and returns
on the next movement input; the serialized inventory is preserved throughout.

StretchDIBits now converts positive-height source crops from a bottom-up DIB's
lower-left origin to the bitmap DC's top-left coordinates. Previously Cult II
selected an empty part of its correctly decoded sprite sheet. Three owned
bitmap fixtures against Windows confirm the tested crop coordinates. Negative
source-height crops have not received equivalent conformance verification.

GetDIBits previously copied internal 32-bit rows into a requested 24-bit buffer,
overwriting a live COM interface in Cult II. The shim now converts the requested
format, respects orientation and scan ranges, and checks the output span. A
separate fixture against Windows confirms its tested row order, partial-row
behavior and buffer extent. The native game paths now complete New Game.

Background erase requests now reach the window procedure during BeginPaint;
DefWindowProc uses the class brush. Hiding a child invalidates the exposed
parent. Paint DCs now clip to accumulated update rectangles and exposed child
bounds. This removes stale main-menu backgrounds and preserves the HUD after
dialogs close. Hidden child DCs have an empty clip and cannot read or draw in
their visible parent surface, removing leaked helper sprite previews. A native
Windows fixture confirms the empty-clip behavior of a hidden window DC.

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
LLVM-MinGW toolchain. Both Linux SDL packages also build. Both games complete
20-second desktop runs on each system with clean exits, Vulkan presentation,
nonzero 48 kHz stereo device PCM and no presenter faults. Cult presents 21 frames
and Cult II presents five while waiting at their startup screens. Windows Cult
II uses DirectSound because the default audio backend found no playback device.
The tested WSL configuration uses X11, PULSE_LATENCY_MSEC=100 and
RECOMP_AUDIO_AHEAD=8192. Cult captures 945,429 PCM frames and Cult II 929,104;
both report zero late or starved audio pulls. These bounded runs do not establish
audibility, physical input or full desktop gameplay.

Default WSL backends previously hung during startup or audio cleanup. A debugger
found one cleanup waiting in SDL's PulseAudio thread. A fetched-source patch now
holds the PulseAudio mainloop lock while updating write accounting; it fixes a
data race, but its relationship to the hangs is unproven. The launcher therefore
uses the tested WSL settings. Vulkan acquisition also rebuilds and retries once
after a recoverable out-of-date swapchain. macOS, iOS, Android and web binaries
have not been produced. Both browser builds are compiling with Emscripten
6.0.11 after successful WebGPU/pthreads configuration. Windows-hosted Android
NDK r30, API 36 revision 2 and Build Tools 37.0.0 are staged under ignored
build/toolchains/android-sdk/. Their archives matched pinned upstream checksums;
the repository's associated agreement matches the already accepted installed
SDK agreement after whitespace normalization. No new agreement was accepted.
Android compilation remains pending.

Browser and Android packaging previously omitted the host's General MIDI bank.
The pending platform builds now stage it and its license. Android also stages
display modes and the optional symbol index, with Java copying only those named
runtime files into the app's data root. Platform execution still needs checking.
Windows packages now include LLVM-MinGW's shared C++ runtimes and their notices.
Both packaged executables reach command-line argument handling with a PATH
containing only Windows system directories. This checks loading dependencies;
it does not verify SDL display or audio devices.

## Runtime verification

The latest selected native contracts pass:

- Graphics: **202 checks, zero failures**, including requested-depth bitmap
  downloads with guard bytes, orientation, scan ranges, background erasure,
  partial update clipping, hidden child DCs and cropped DIB orientation.
- Loader/startup: **487 checks, zero failures, one resource-related skip**.
- Audio/DirectX shims: **141,275 checks, zero failures, one explicit skip** for a
  cursor-learning fixture whose required game globals are absent from these profiles.
- Root input/profile checks: **19 tests pass**, including stale-file rejection
  and serialized-state round-trip verification.
- Latest selected decoder/translator/configuration/build/root suite: **242 pass**.
- Desktop keyboard gate: **66 checks, zero failures**, including suppression of
  duplicate character messages when the guest calls TranslateMessage.
- Actual MIDI score rendering: **6,272 checks, zero failures** across all 49 SMF
  assets from both archives, with 12 seconds per score and nonzero mixer output.
- Selected Windows packaging tests: **7 pass**, including bundled compiler
  runtimes and exclusion of unrelated files.
- All desktop packaging tests on Linux: **21 pass**.
- Windows developer/saved game-path contracts: **11 checks, zero failures**,
  including recognition of the actual drive-rooted developer executable.
- Build argument/runtime-resource staging suite: **15 tests pass**, including
  MIDI bank/license packaging, exclusion of unrelated files and stale-index removal.

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
smoke host opens no audio device. All 49 original SMF scores now produce notes
and nonzero PCM through the production MCI scheduler, TinySoundFont synth and
offline mixer. This verifies the tested first 12 seconds of each asset;
audible device output and the guest's music triggers remain unverified.

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
--max-seconds 210 --host-keyboard for the current bounded save/load path through
the desktop keyboard gate. Use --trace-windows
to record the window model at frame captures. Evidence is saved under each
profile's build/<scenario>-probe/. A completed input script does not by itself
verify movement, rendered pixels, original parity or playability.

Build host_tests with kit/tools/test.py --native-target host_tests --compile-only
and the appropriate --game-dir and --preset, then run tools/probe_audio.py to
repeat the actual-score offline render. Logs go under build/audio-probe/.

After building the SDL app, tools/probe_desktop.py --game <id> --seconds 20
exercises the real desktop presenter and audio initialization with a bounded
guest close. It records presenter faults and PCM captures separately from
physical input or audible-output verification. tools/package_player.py assembles
private local player folders, including the supplied inputs and a launcher,
under ignored build/player/<platform>/. Windows and Linux folders now exist for
both games. Windows launchers default to DirectSound and WSL launchers use the
tested display/audio settings, preserving explicit overrides. Desktop evidence
is kept under games/<id>/build/desktop-probe/<platform>/. For the WSL probe, set
SDL_VIDEODRIVER=x11 and PULSE_LATENCY_MSEC=100 and add --audio-ahead 8192.
These are experimental builds.
The assembled Play.cmd and Play.sh launchers also pass five-second startup
checks for both games, with device PCM, rendered frames and clean exits. Repeat
with tools/probe_desktop.py --game all --seconds 5 --player. Launcher evidence
is kept in the platform's desktop-probe/player/ subdirectory.

Remaining work: investigate Cult II's inventory redraw immediately after loading,
exercise further interactions/transitions, verify original-save
compatibility, test physical and touch input plus audible music/effects, and
build/test each requested platform with its required toolchain and SDK. Full
playable ports and an all-platform release remain outstanding.
