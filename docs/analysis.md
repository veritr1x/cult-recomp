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
