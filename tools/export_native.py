"""Export native listings with RecompKit's decoder and VB event-table seeds.

This bootstrap uses explicit VB metadata and direct control-flow edges. It does
not produce Ghidra pseudocode and does not prove complete callback coverage.
"""

import argparse
import importlib.util
import json
import sys
import tomllib
from pathlib import Path

from import_archives import GAMES, ROOT



def cleanup_continuations(translator, image, instructions):
    """Recover VB's PUSH-return/JMP-cleanup calls with a returning epilogue.

    Ordinary PUSH data is excluded: both destinations must be executable and
    ordered in the nearby forward cleanup region, and the return target must
    decode as a straight-line register/frame epilogue ending in RET.
    """
    for push, jump in zip(instructions, instructions[1:]):
        if push.mnem != "PUSH" or jump.mnem != "JMP" or not push.ops or not jump.ops:
            continue
        ret, cleanup = translator.parse_operand(push.ops[0]), translator.parse_operand(jump.ops[0])
        if ret.kind != "imm" or cleanup.kind != "imm":
            continue
        if jump.addr != push.addr + 5 or not (jump.addr + 5 <= cleanup.imm < ret.imm < push.addr + 4096):
            continue
        if not image.is_exec(ret.imm) or not image.is_exec(cleanup.imm):
            continue
        epilogue = image.recover(ret.imm, set())
        if (epilogue and epilogue[-1].mnem == "RET" and len(epilogue) <= 16
                and all(i.mnem in {"MOV", "POP", "XOR", "ADD", "RET"} for i in epilogue)):
            yield ret.imm, push.addr


def export_game(kit, game_id):
    """Decode native entries and callees; preserve provenance for every seed."""
    spec = importlib.util.spec_from_file_location("kit_translate", kit / "tools/recomp/translate.py")
    translator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(translator)
    game = ROOT / "games" / game_id
    report = json.loads((game / "analysis/pe-report.json").read_text())
    executable = GAMES[game_id][1]
    image = translator.Image(str(game / "original/install" / executable))
    seeds = set(report["vb"]["structural_entry_points"])
    provenance = {a: "vb_event_table" for a in seeds}
    provenance[report["entry_point"]] = "pe_entry_point"
    configured = tomllib.loads((game / "game.toml").read_text())
    if configured["game"]["sha256"] != report["sha256"]:
        raise ValueError("Preserving audited entries for a different game image")
    for entry in configured["translate"].get("entry_points", []):
        if not image.is_exec(entry):
            raise ValueError(f"Audited entry outside executable section: {entry:08x}")
        if entry not in seeds:
            provenance[entry] = "audited_config_seed"
            seeds.add(entry)
    # ThunRTMain never returns: stop the tiny process entry after its CALL.
    first = image.instruction_at(report["entry_point"] + 5)
    if first and first.mnem == "CALL":
        target = translator.parse_operand(first.ops[0]).imm
        image.noreturn_callees.add(target)
    pending, decoded = sorted(seeds, reverse=True), {}
    while pending:
        entry = pending.pop()
        if entry in decoded:
            continue
        if not image.is_exec(entry):
            raise ValueError(f"Structural seed outside executable section: {entry:08x}")
        instructions = image.recover(entry, set(), boundaries=seeds)
        if not instructions:
            raise ValueError(f"No native instructions at {entry:08x}")
        decoded[entry] = instructions
        for continuation, source in cleanup_continuations(translator, image, instructions):
            if continuation not in seeds:
                seeds.add(continuation)
                provenance[continuation] = f"vb_cleanup_return:{source:08x}"
                pending.append(continuation)
        for instruction in instructions:
            if instruction.mnem not in ("CALL", "JMP") or not instruction.ops:
                continue
            operand = translator.parse_operand(instruction.ops[0])
            if operand.kind == "imm" and image.is_exec(operand.imm) and operand.imm not in seeds:
                seeds.add(operand.imm)
                provenance[operand.imm] = f"direct_edge:{instruction.addr:08x}"
                pending.append(operand.imm)
    # Re-decode with final boundaries so functions do not absorb neighbouring entries.
    destination = game / "analysis" / executable
    functions = destination / "functions"
    functions.mkdir(parents=True, exist_ok=True)
    rows = ["address\tname\tbytes\tstatus\tmessage"]
    for entry in sorted(decoded):
        instructions = image.recover(entry, set(), boundaries=seeds)
        size = sum(image.insn_end(i.addr, i.mnem) - i.addr for i in instructions)
        (functions / f"{entry:08x}.asm").write_text("\n".join(i.raw for i in instructions) + "\n")
        rows.append(f"{entry:08x}\tVB_NATIVE_{entry:08x}\t{size}\tnative-bootstrap\t{provenance[entry]}")
    (destination / "functions.tsv").write_text("\n".join(rows) + "\n")
    (destination / "inputs.json").write_text(json.dumps({
        "executable_sha256": report["sha256"],
        "exporter": "RecompKit Image.recover + VB5 event metadata",
        "function_count": len(decoded),
        "recovery_errors": image.recover_errors,
        "coverage_verified": False,
    }, indent=2) + "\n")
    print(f"{game_id}: exported {len(decoded)} native entries to {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit", type=Path, required=True)
    args = parser.parse_args()
    kit = args.kit.resolve()
    sys.path.insert(0, str(kit / "tools"))
    for game_id in GAMES:
        export_game(kit, game_id)


if __name__ == "__main__":
    main()
