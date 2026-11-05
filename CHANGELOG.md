# Changelog

## Unreleased

- Update recomp-kit to `1cbd81c` and rebase the remaining VB5/OLE/GDI source
  patch. Enable optional hosted streaming alongside folder import for both
  profiles; validate gameplay and exact save restoration in Chromium.

- Publish the Cult and Cult II static recompilation profiles with the same
  submodule, contributor documentation, source checks and CI conventions as
  the other recomp-kit game projects. Original game inputs remain private.
- Pin recomp-kit `a18ccaf` and rebase the remaining VB5/OLE/GDI extensions on
  its reviewed translator, scheduler, renderer and bounded bitmap fixes.
- Publish translations transactionally through the kit build API.

Historical local verification is retained in [docs/status.md](docs/status.md).
