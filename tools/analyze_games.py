"""Record PE imports and VB5 compilation metadata without executing game code."""

import hashlib
import json
import struct
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

from import_archives import GAMES, ROOT


def inspect_pe(path):
    """Return image layout/import facts and startup instructions for one PE32."""
    data = path.read_bytes()
    pe = pefile.PE(data=data)
    base = pe.OPTIONAL_HEADER.ImageBase
    entry = base + pe.OPTIONAL_HEADER.AddressOfEntryPoint
    result = {
        "file": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "machine": pe.FILE_HEADER.Machine,
        "image_base": base,
        "image_size": pe.OPTIONAL_HEADER.SizeOfImage,
        "entry_point": entry,
        "sections": [{
            "name": section.Name.rstrip(b"\0").decode("ascii"),
            "address": base + section.VirtualAddress,
            "virtual_size": section.Misc_VirtualSize,
            "raw_size": section.SizeOfRawData,
            "executable": bool(section.Characteristics & 0x20000000),
        } for section in pe.sections],
        "imports": [{
            "dll": descriptor.dll.decode("ascii"),
            "symbols": [{"name": symbol.name.decode("ascii") if symbol.name else None,
                         "ordinal": symbol.ordinal, "iat": symbol.address}
                        for symbol in descriptor.imports],
        } for descriptor in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])],
        "startup": [{"address": instruction.address, "bytes": instruction.bytes.hex(),
                     "instruction": instruction.mnemonic + " " + instruction.op_str}
                    for instruction in Cs(CS_ARCH_X86, CS_MODE_32).disasm(
                        pe.get_data(entry - base, 24), entry)],
    }
    # Follow the startup PUSH pointer rather than searching arbitrary string data.
    startup = pe.get_data(entry - base, 5)
    if len(startup) == 5 and startup[0] == 0x68:
        header = struct.unpack_from("<I", startup, 1)[0]
        if pe.get_data(header - base, 4) == b"VB5!":
            def u32(address):
                return struct.unpack("<I", pe.get_data(address - base, 4))[0]

            project = u32(header + 0x30)
            native = u32(project + 0x20)
            table = u32(project + 4)
            array = u32(table + 0x30)
            count = struct.unpack("<H", pe.get_data(table - base + 0x2a, 2))[0]
            objects, seeds = [], {entry}
            for index in range(count):
                descriptor = array + index * 0x30
                info = u32(descriptor)
                name = pe.get_data(u32(descriptor + 0x18) - base, 128).split(b"\0")[0]
                item = {"name": name.decode("cp1252"), "descriptor": descriptor,
                        "object_info": info, "declared_method_count": u32(descriptor + 0x1c),
                        "controls": [], "method_links": []}
                # These images' form descriptors have both HasOptInfo and Form bits.
                if u32(descriptor + 0x28) & 0x80:
                    optional = info + 0x38
                    link_count = struct.unpack("<H", pe.get_data(optional - base + 0x28, 2))[0]
                    links = u32(optional + 0x30)
                    item["method_links"] = [u32(links + n * 4) for n in range(link_count)]
                    seeds.update(item["method_links"])
                    controls = u32(optional + 0x24)
                    for n in range(u32(optional + 0x20)):
                        control = controls + n * 0x28
                        control_name = pe.get_data(u32(control + 0x20) - base, 128).split(b"\0")[0]
                        events = struct.unpack("<H", pe.get_data(control - base + 2, 2))[0]
                        event_table = u32(control + 0x18)
                        pointers = [u32(event_table + 0x18 + k * 4) for k in range(events)]
                        seeds.update(p for p in pointers if p)
                        item["controls"].append({"name": control_name.decode("cp1252"),
                                                "events": pointers})
                objects.append(item)
            result["vb"] = {
                "header": header, "project_info": project,
                "project_version": u32(project),
                "object_table": table,
                "native_code_pointer": native,
                "project_compilation_flag": "pcode" if native == 0 else "native",
                "external_table": u32(project + 0x234),
                "external_count": u32(project + 0x238),
                "objects": objects,
                "structural_entry_points": sorted(seeds),
            }
    pe.close()
    return result


def main():
    for game_id, (_, executable) in GAMES.items():
        game = ROOT / "games" / game_id
        result = inspect_pe(game / "original/install" / executable)
        result["dependencies"] = [inspect_pe(game / "original/dependencies" / name)
                                  for name in ("MSVBVM50.dll", "PICCLP32.OCX")]
        runtime = pefile.PE(str(game / "original/dependencies/MSVBVM50.dll"))
        ordinal_names = {symbol.ordinal: symbol.name.decode("ascii") if symbol.name else None
                         for symbol in runtime.DIRECTORY_ENTRY_EXPORT.symbols}
        for dll in result["imports"]:
            if dll["dll"].casefold() == "msvbvm50.dll":
                for symbol in dll["symbols"]:
                    symbol["resolved_name"] = symbol["name"] or ordinal_names.get(symbol["ordinal"])
        runtime.close()
        destination = game / "analysis/pe-report.json"
        destination.write_text(json.dumps(result, indent=2) + "\n")
        print(f"{game_id}: entry=0x{result['entry_point']:08x}, "
              f"VB={result.get('vb', {}).get('project_compilation_flag')}, "
              f"imports={sum(len(d['symbols']) for d in result['imports'])}")
        if "vb" in result:
            print("Objects:", [(o["name"], len(o["controls"]), len(o["method_links"]))
                               for o in result["vb"]["objects"]])


if __name__ == "__main__":
    main()
