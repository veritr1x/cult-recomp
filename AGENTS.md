# Working on Cult Recomp

Read README.md, CONTRIBUTING.md and docs/analysis.md before a broad change.
This repository holds the Cult and Cult II profiles, curated metadata,
import/export helpers, smoke scripts and docs. The runtime and translator
belong to the pinned recomp-kit submodule. The remaining shared VB5/OLE/GDI
extensions are a reproducible source patch in patches/, applied locally.

- Preserve original game inputs and player profiles. Never bypass image hashes.
- Edit translator rules, never generated C. Regenerate with tools/build.py
  --translate-only after translator changes; native builds use the kit build API.
- Guest addresses remain 32-bit addresses, never host pointers.
- Keep runtime interpretation disabled for these static recompilations.
- Run relevant checks from docs/testing.md and report bounded coverage accurately.
- Do not publish executables, DLLs/OCXs, assets, generated code, builds, saves,
  credentials or run logs. Run tools/check_repo.py before committing.
- Update CHANGELOG.md for user-visible changes and keep documentation current.
