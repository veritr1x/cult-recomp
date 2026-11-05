# Port analysis

## Current shared-kit checkpoint: 2026-11-01

Both profiles pin published recomp-kit `a18ccafa1e8c98002b2d3f7347b64fa655ebb018`
and apply the remaining VB5/OLE/GDI source patch. The upstream tree equals the
reviewed `b1bdfd6` head; its 14 platform CI checks pass. No unpublished commit
is needed by a recursive checkout. Older bring-up observations are retained in
[status.md](status.md) with their original dates and scope.

The rebase retains structured storage, Automation, system Edit/ListBox controls,
VB continuations, MIDI and the GDI/window behavior required by these games.
It incorporates upstream guarded guest memory, thread/message scheduling,
strict target validation, entry-specific variadic-return proofs and bounded
GetDIBits conversion. Both games' main images and all four auxiliary modules
were fully regenerated after translator changes; every generated call target
resolves. Runtime interpretation remains disabled.

Windows x64 LLVM-MinGW/Vulkan builds link the app, smoke and headless hosts for
both profiles. Fresh isolated save probes pass: Cult moves from (267,60) to
(267,90), and Cult II from (407,160) to (437,160). Each writes three fresh saves,
restores byte-identical state after reload and records changed player position.
No called missing imports, unknown transfers, VB runtime errors or guest access
violations occur in these bounded checks. The integrated drawing suite passes
237 native checks; the portable kit suite with these extensions passes 683 tests
with four platform skips.

These checks used video-disabled Windows builds. Historical Linux/browser
results are not fresh validation of this pin. Full campaigns, original-save
compatibility, physical/touch input, audible output and refreshed mobile runtime
checks remain outside the established coverage. No assets or private evidence
are published. The implementation is not a distribution of the original games.

A clean recursive checkout with no original inputs also passes the 18 portable
project tests. The source patch applies once and accepts a second invocation
without changing it. Both profiles link their Windows app, headless and smoke
hosts against stub translations through the kit build API; all 44 game-independent
Windows native suites pass with the patch applied, including the 237 drawing
checks. These verify source reproducibility and compatibility contracts, not
additional real-game or device coverage.

## 2026-11-05 browser streaming and shared kit refresh

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

See [web.md](web.md) for reproducible browser commands on kit `1cbd81c`.
Earlier platform results are historical and were not all rerun.
