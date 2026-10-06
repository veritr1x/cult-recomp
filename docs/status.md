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
for Cult and 2,509 for Cult II. These are bounded tests of particular paths,
not complete gameplay verification or original-save compatibility tests.
Cult's stronger test now verifies movement from (267,60) to (267,90), then
restoration to (267,60), with fresh saves before and after loading matching
byte for byte. Cult II's test likewise verifies movement from (407,160) to
(437,160), then restoration to (407,160), with fresh saves matching byte for
byte. Both repeat this test successfully on Linux x86_64 through the desktop
keyboard gate, with 2,055 frames for Cult and 2,510 for Cult II.
Earlier Cult II builds left the inventory icon blank after loading until the
next movement input. The timer and paint corrections below restore it immediately
in the new Windows, Linux and browser checks; the serialized inventory is preserved.

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
after a recoverable out-of-date swapchain. macOS and iOS binaries
have not been produced. Both browser builds linked with Emscripten
6.0.11 and are packaged under ignored build/player/web/. Debug metadata was
stripped without changing executable WebAssembly sections. Both original data
sets imported into private browser storage; both games render their language
screens through WebGPU and initialize their MIDI banks. GetKeyState now retains
the retrieved mouse message's button state, so an early physical release no longer
erases a windowless control's press. Ordinary Play clicks start both games;
keyboard input reaches their opening scenes and advances the conversations.
Later browser movement/menu input can leave blank or stale frames. The shared
gray initial-menu rectangles are fixed in both Windows diagnostic hosts: child
windows now start below existing siblings, showing a child preserves its
stacking, and WS_CLIPSIBLINGS prevents covered controls from erasing menu pixels.
The GDI suite passes 220 checks, including child creation/show order and sibling
clipping through an ancestor. Both menus are visually checked, and both games
pass fresh movement/save/load round trips with the fix. Both browser builds are
updated; both main menus and Cult II's in-game Escape menu are visually verified.
Its browser save screen accepts keyboard input and reaches GAME SAVED; loading
the selected entry returned to the opening scene with the menu-only fix.
SetWindowTextA now reaches the control procedure to notify and repaint, making
Cult II's save/load name visibly legible in the native host and browser.
The repaint exposed an unsupported GetWindowTextA call; the browser then aborted
on Load. Its implementation now delivers WM_GETTEXT with encoding conversion,
and both native Windows movement/save/load tests pass without missing imports,
unknown transfers or runtime errors. All Windows, Linux, browser and Android
packages are rebuilt with these text changes. Cult II creates a fresh browser
save (P4) and loads it from the in-game menu, returning to its street scene.
The translator now recognizes VB/MSVC prologues that cache FS:[0] in a register
before pushing the registration link. The runtime retires unlinked registrations
while locals are still allocated and lets the resumable driver adopt surviving
checkpoints after generated activations return, resetting profiling ownership.
This passes **352 Windows and Linux SEH checks** and **212 selected translator
checks**. Both games are regenerated. Both refreshed Windows diagnostics pass
fresh movement/save/load round trips with identical restored saves; Cult's
refreshed Linux diagnostic repeats its 2,055-frame round trip successfully.
The exported P4 and R6R6 browser saves also load from the refreshed Windows
diagnostic host's startup menu: each presents 603 frames and renders the street
without missing imports, unknown transfers or runtime errors.

Cult II's earlier refreshed browser aborted when loading P4 from the startup
menu. Its trace exposed a callback ownership error:
the guest restores an older callback's stack and returns at ESP=0efffe94, while
the runtime still expects the handler callback below ESP=0efff864. The resumable
driver mistakes this completed older callback for a handler disposition of zero.
A regression reproduces the erroneous disposition and abort before the source
fix. The correction finds the owning callback and retires abandoned callback
and SEH records, while preserving active SEH landings through their checkpoints.
It passes **365 SEH checks on both Windows and Linux**. Both browser builds now
include this correction. Cult II's browser startup Load opens P4.fcg and reads
its 124 bytes, then reports Visual Basic error 5 (invalid procedure call or
argument) and exits the guest with code zero. A successful browser startup Load
had not yet been established. A concise trace
preserves the error after verbose import traffic had displaced it from the
browser console. Import tracing can now be suppressed independently of other
verbose diagnostics through RECOMP_TRACE_IMPORTS=0. A bounded ReadFile byte
trace confirms that all 124 browser input bytes equal the exported P4 file.
The exception stack reports a failed picture-control method (offset 0x280);
its underlying cause was subsequently traced to timer ordering, described below.
Targeted argument tracing now shows the browser's first sprite call arrives
from a different timer callback with a null animation BSTR; the successful
native path first supplies "Stand". Direction restoration matches the native
writer and the saved bytes are not the divergence.

Window message retrieval now returns pending paint before generated SetTimer
notifications, as documented by Windows, while explicitly posted WM_TIMER
messages keep their queue order. Eight regressions exercise both retrieval APIs,
filters, removal and paint validation. The first GDI pass covered **229 checks on
Windows and Linux**. A Windows startup P4 load with this change presents 604
frames, completes all 11 script steps and renders both the street and inventory
icon without movement. The browser also paints that scene and inventory, but
still raises error 5 and exits on its first sprite timer call. That painted
frame is not evidence of playable browser Load.

A Windows probe with real time reproduces that error: after slow input loading,
the 1,000 ms sprite update timer is retrieved before the overdue 10 ms setup
timer because the runtime iterates timers by window handle. A message-only
fixture using Windows' own USER32 API retrieves the earlier deadline first,
with three separate windows and with three timers on one window. The runtime
now queues expired timers in deadline order, with regressions for DWORD clock
wrap. **233 GDI checks pass on Windows and Linux**. The corrected real-time Windows
startup P4 probe completes all 11 steps and 2,197 frames, restores the street
and inventory, and exits cleanly. The equivalent real-time Linux probe completes
all 11 steps and 2,195 frames, renders the street and inventory, and exits cleanly.
The corrected browser now loads P4 from its
startup menu, renders the street, character and inventory, and keeps executing
its timers with valid "Stand" BSTR arguments. The captured console trace has
neither a run-time error nor ExitProcess. Broader browser gameplay remains to
be verified. Escape opens its in-game menu, keyboard navigation reaches Save,
and a fresh A.fcg reaches GAME SAVED. Exporting through the local player's save
manager yields a 124-byte A.fcg identical to the loaded P4.fcg. A single Right
tap did not change its coordinates; browser movement is not established.
Both Windows diagnostics now repeat movement/save/load with the timer corrections:
2,055 frames for Cult and 2,509 for Cult II. The fresh Linux runs also pass:
2,055 and 2,510 frames respectively, restoring identical saves. Cult moves
from (267,60) to (267,90); Cult II's Windows run reaches (437,160) and its
Linux run reaches (417,160), both restoring (407,160).
The corrected Cult II diagnostics repeat the 2,510-frame movement/save/load
round trip on Windows and Linux, restoring identical save bytes.
Cult likewise repeats its 2,055-frame round trip on both systems after the
callback correction. A fresh Windows startup Load of P4 presents 603 frames
and restores the street. Linux also restores P4 from the startup menu with
real time and concise logging: all eleven input steps complete, 1,592 frames
are presented and the guest exits cleanly. The preserved pinned-clock run
stalled; a verbose real-time run had not finished its intro when input arrived.
Those earlier probes do not establish a Linux startup-Load failure.
The browser's newly exported save byte comparison covers the P4 startup Load and
resave path. Sustained browser gameplay and physical/touch device compatibility
remain unverified.
The four mouse-state regressions pass; the keyboard gate and queued-input checks
have 78 checks with zero
failures. The latest broader runtime run has 1,617 checks, 24 failures and two
skips, including file overlay, version/image resources, timing fixtures and
translation metadata contracts; it is not a full pass. Its window-model checks
pass.
All Windows, Linux, browser and Android packages include the control text changes,
checkpoint lifetime fix, callback ownership correction and timer ordering fixes. The latest
five-second Windows launcher probes explicitly select legacy Vulkan, render and exit cleanly
with running audio devices: Cult captures 225,280 PCM frames and Cult II captures
231,424, both with peak 17,341 PCM16. Audible
output is still unverified.
The latest Linux launchers also explicitly select legacy Vulkan and pass
twenty-second startup with 118 presented frames for Cult and five for Cult II.
Cult captures 935,831 PCM frames, peak 32,767, and Cult II captures 945,904,
peak 17,341. Both report zero late or starved audio pulls and exit cleanly.
These checks establish menu startup, renderer selection and captured output;
they do not establish audible sound quality. Earlier Cult II runs during
concurrent work reported late pulls; their logs are retained as historical evidence.
The initial five-second menu-only Cult II run has buffered PCM with a zero peak
and is preserved separately.
Windows-hosted Android
NDK r30, API 36 revision 2 and Build Tools 37.0.0 are staged under ignored
build/toolchains/android-sdk/. Their archives matched pinned upstream checksums;
the repository's associated agreement matches the already accepted installed
SDK agreement after whitespace normalization. No new agreement was accepted.
Android configuration and APK assembly succeeded for both games. Private debug
APKs are under build/player/android/. Both install and load their ARM64 libraries
on an isolated emulator using libndk_translation. Its original software Vulkan
driver lacks dynamic rendering. Switching to the host GPU creates a device but
exposed an omitted VK_KHR_android_surface extension, now enabled when available.
The original emulator then failed in WHPX MMIO emulation. Checksum-pinned stable
emulator 37.2.12 boots in the same isolated AVD, but its device connection becomes
unavailable after launch. Neither test verifies Android gameplay.
The stable emulator 37.2.12 with software graphics boots and keeps the guest
responsive, but its Vulkan device lacks dynamic rendering. The installed Cult
II build falls back to the launcher and reports no GPU device; it does not reach
gameplay. This owned test emulator was stopped after logs were captured.
Both Android ARM64 APKs have now been rebuilt and packaged with the child-window
and control-text fixes. The package checks verify the native ELF ABI and named runtime resources;
they do not verify device gameplay.
Cult II's newest APK also contains the checkpoint lifetime and callback ownership
corrections, confirmed in its ARM64 library. Its SHA-256 is
e539f6242a0d6485e197cefb082917dafc497f299b796101f6ccda92c5880db8.
Cult's corresponding rebuild is also packaged; its SHA-256 is
218d6878458cbfd6c13ca2222103b25b05abe910e43e139d291eee60e17e8f80.
Both APKs now include a legacy Vulkan render-pass fallback and buffer diagnostics.
The fallback selects supported features, retains framebuffers through submission
and retires them before their image views. Its focused attachment clear/load,
depth and lifetime suite passes 53 checks on Windows and Linux; presenter pixel
checks pass 131 on each. Validation layers are absent on both tested hosts.
The broad Windows renderer suite records 3,738,266 checks and 229 failures in both
dynamic and legacy modes, with identical failure records; it is not a full pass.
The swapchain suite now renders before resizing to cover framebuffer retirement;
both modes record 36 checks and one failure because the hidden Windows surface
remains 32 pixels wide when the fixture requests a 64-pixel swapchain.
The emulator now creates a legacy Vulkan device and a 1080x2400 swapchain, clearing
the missing-dynamic-rendering blocker. Its native-bridge libc then faults during
the 10,368,000-byte staging upload of launcher pixels. Buffer diagnostics preserve
the returned maps and faulting write; no game frame has been established.
After correcting copied game-directory permissions, the Android app recognizes
Cult2FC.exe. The adb push path now applies that scoped directory permission fix,
and 40 build and packaging tests pass.
Disabling GLDirectMem, including a second attempt also disabling GLDMA and GLDMA2,
causes the emulator's own SurfaceFlinger to abort; those test emulators were
stopped after logs were captured. Disabling VirtioGpuNext preserves a healthy
emulator boot but the same app upload still faults. An explicit mapping size
also faults and was reverted. Android gameplay remains unverified.
Gradle now receives CMake's NDK path and Pkg.Revision, avoiding a silent failure
to strip symbols with AGP's different default NDK. This reduces Cult II's APK
from about 1.28 GB to 658 MB; Cult's package is about 654 MB. The Gradle/build
contracts pass 16 tests. Physical ARM64
hardware, touch input and audible output remain unverified.

Browser and Android packaging previously omitted the host's General MIDI bank.
The browser builds include it and its license, and Cult initializes TinySoundFont
from the packaged bank. Both Android APKs also stage
display modes and the optional symbol index, with Java copying only those named
runtime files into the app's data root. APK contents are verified; full platform
execution still needs checking.
Windows packages now include LLVM-MinGW's shared C++ runtimes and their notices.
Both packaged executables reach command-line argument handling with a PATH
containing only Windows system directories. This checks loading dependencies;
it does not verify SDL display or audio devices.

## Runtime verification

The latest selected native contracts pass:

- Graphics: **233 checks, zero failures**, including paint/timer priority,
  deadline ordering across clock wrap, control text delivery and
  retrieval, child/sibling stacking and clipping, requested-depth bitmap
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
After the mouse-state fix, updated Windows launchers pass 20-second checks with
nonzero captured device PCM; updated Linux launchers pass five-second checks
with nonzero PCM. These checks verify startup and clean exits, not gameplay.

Remaining work: exercise further interactions/transitions, verify original-save
compatibility, test physical and touch input plus audible music/effects, and
build/test each requested platform with its required toolchain and SDK. Full
playable ports and an all-platform release remain outstanding.
