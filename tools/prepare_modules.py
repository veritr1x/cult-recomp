"""Pin and export the supplied DLLs without executing or registering them."""

import hashlib
import importlib.util
import json
import sys
import re
import shutil
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pefile

from import_archives import GAMES, ROOT


def main():
    kit = ROOT / "kit"
    sys.path.insert(0, str(kit / "tools"))
    spec = importlib.util.spec_from_file_location("kit_translate", kit / "tools/recomp/translate.py")
    translator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(translator)
    for game_id in GAMES:
        game = ROOT / "games" / game_id
        profile = game / "game.toml"
        text = profile.read_text()
        config = tomllib.loads(text)
        if "guest_size =" not in text:
            text = text.replace('[game]\n', '[game]\nguest_size = 0x74200000\n')
        for key, filename in (("vb5", "MSVBVM50.DLL"), ("pictureclip", "PICCLP32.OCX")):
            path = game / "original/dependencies" / filename
            # Archives preserve their original filename capitalization.
            path = next(p for p in path.parent.iterdir() if p.name.lower() == filename.lower())
            pe = pefile.PE(str(path))
            base, size = pe.OPTIONAL_HEADER.ImageBase, pe.OPTIONAL_HEADER.SizeOfImage
            image = translator.Image(str(path))
            data_exports = {base + e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols
                            if e.name and e.name.startswith((b"IID_", b"CLSID_", b"LIBID_", b"DIID_"))}
            seeds = {base + pe.OPTIONAL_HEADER.AddressOfEntryPoint}
            seeds.update(base + e.address for e in pe.DIRECTORY_ENTRY_EXPORT.symbols
                         if not e.forwarder and image.is_exec(base + e.address)
                         and base + e.address not in data_exports)
            exported_seeds = set(seeds)
            configured = config.get("modules", {}).get("aux", {}).get(key, {})
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if configured and configured["sha256"] != digest:
                raise ValueError(f"Preserving a profile for a different {filename} image")
            # Portable bundles stage the installation directory. These pinned
            # image bytes are mapped as guest data; no host DLL is installed.
            bundled = game / "original/install" / filename
            if bundled.exists() and hashlib.sha256(bundled.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Preserving a different existing module: {bundled}")
            if not bundled.exists():
                shutil.copy2(path, bundled)
            seeds.update(a for a in configured.get("entry_points", []) if a not in data_exports)
            provenance = {a: "pe_export_or_entry" if a in exported_seeds else "audited_config_seed" for a in seeds}
            initial_seeds = set(seeds)
            pending, decoded, rejected = sorted(seeds, reverse=True), {}, {}
            decoder = translator.Translator(image, seeds, SimpleNamespace(eager_flags=False))
            while pending:
                entry = pending.pop()
                if entry in decoded or entry in rejected:
                    continue
                instructions = image.recover(entry, set(), boundaries=seeds)
                if not instructions:
                    if entry in initial_seeds:
                        raise ValueError(f"No instructions at {entry:08x} in {filename}: {image.recover_errors[-3:]}")
                    rejected[entry] = "Decoder found no user-mode instructions"
                    continue
                forbidden = [i for i in instructions if i.mnem in
                             {"IN", "OUT", "INSB", "INSW", "INSD", "OUTSB", "OUTSW", "OUTSD", "LJMP"}]
                if forbidden and entry not in initial_seeds:
                    rejected[entry] = f"User-mode DLL cannot execute {forbidden[0].mnem} at {forbidden[0].addr:08x}"
                    continue
                decoded[entry] = instructions
                instruction_addresses = {i.addr for i in instructions}
                fn = translator.Function(entry, "native", 0, instructions)
                fn.measure(image)
                decoder.prepare(fn, strict=False)
                targets = {(a, "jump_table") for a in decoder.unlisted_targets if image.is_exec(a)}
                decoder.unlisted_targets.clear()
                for instruction in instructions:
                    if (instruction.mnem not in ("CALL", "JMP") and not instruction.mnem.startswith("J")) or not instruction.ops:
                        continue
                    operand = translator.parse_operand(instruction.ops[0])
                    if operand.kind == "imm" and image.is_exec(operand.imm):
                        if instruction.mnem not in ("CALL", "JMP") and operand.imm in instruction_addresses:
                            continue
                        targets.add((operand.imm, f"direct_edge:{instruction.addr:08x}"))
                for target, reason in targets:
                    if target not in seeds:
                        seeds.add(target)
                        provenance[target] = reason
                        pending.append(target)
            destination = game / "analysis" / filename
            functions = destination / "functions"
            functions.mkdir(parents=True, exist_ok=True)
            rows = ["address\tname\tbytes\tstatus\tmessage"]
            for entry in sorted(decoded):
                instructions = image.recover(entry, set(), boundaries=seeds)
                length = sum(image.insn_end(i.addr, i.mnem) - i.addr for i in instructions)
                (functions / f"{entry:08x}.asm").write_text("\n".join(i.raw for i in instructions) + "\n")
                rows.append(f"{entry:08x}\tDLL_NATIVE_{entry:08x}\t{length}\tnative-bootstrap\t{provenance[entry]}")
            (destination / "functions.tsv").write_text("\n".join(rows) + "\n")
            (destination / "inputs.json").write_text(json.dumps({
                "sha256": digest, "seed_count": len(decoded), "coverage_verified": False,
                "recovery_errors": image.recover_errors, "rejected_candidates": rejected,
            }, indent=2) + "\n")
            entries = ", ".join(f"0x{a:08x}" for a in sorted(initial_seeds))
            if f"[modules.aux.{key}]" not in text:
                text += f'''\n[modules.aux.{key}]
name = "{filename}"
path = "original/dependencies/{path.name}"
sha256 = "{digest}"
base = 0x{base:08x}
size = 0x{size:08x}
listings = "analysis/{filename}"
function_alignment = 1
entry_points = [{entries}]
'''
            else:
                pattern = rf"(\[modules\.aux\.{key}\][\s\S]*?entry_points = )\[[^\n]*\]"
                text = re.sub(pattern, lambda m: m.group(1) + f"[{entries}]", text, count=1)
            print(f"{game_id}/{filename}: {len(decoded)} export/entry/direct-edge routines", flush=True)
        profile.write_text(text, newline="\n")


if __name__ == "__main__":
    main()
