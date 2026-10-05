"""Focused SZDD safety/overlap checks and exact-image profile validation."""

import hashlib
import json
import struct
import sys
import unittest

from import_archives import GAMES, ROOT, SZDD_MAGIC, expand_szdd, filename


def szdd(length, payload, mode=b"A"):
    return SZDD_MAGIC + mode + b"_" + struct.pack("<I", length) + payload


class CompressionTests(unittest.TestCase):
    def test_literals(self):
        self.assertEqual(expand_szdd(szdd(3, b"\x07ABC")), b"ABC")

    def test_overlapping_reference(self):
        self.assertEqual(expand_szdd(szdd(6, b"\x01A\xf0\xf2")), b"AAAAAA")

    def test_initial_ring_spaces(self):
        self.assertEqual(expand_szdd(szdd(3, b"\0\0\0")), b"   ")

    def test_empty_output(self):
        self.assertEqual(expand_szdd(szdd(0, b"")), b"")

    def test_truncated(self):
        for data in (SZDD_MAGIC, szdd(1, b""), szdd(1, b"\x01"), szdd(3, b"\0\0")):
            with self.subTest(data=data), self.assertRaises(ValueError):
                expand_szdd(data)

    def test_oversized_backreference(self):
        with self.assertRaises(ValueError):
            expand_szdd(szdd(1, b"\0\0\0"))

    def test_output_limit(self):
        with self.assertRaises(ValueError):
            expand_szdd(szdd(0xffffffff, b""))

    def test_unknown_mode(self):
        with self.assertRaises(ValueError):
            expand_szdd(szdd(1, b"\x01A", b"B"))

    def test_plain_data(self):
        self.assertEqual(expand_szdd(b"MZordinary"), b"MZordinary")

    def test_unsafe_names(self):
        for name in ("../game.exe", "C:game", "NUL.dll", "COM1", "game.", "game ", "x\0y"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                filename(name)



class NativeExportTests(unittest.TestCase):
    def test_cleanup_return_discovery_excludes_push_data_and_non_epilogues(self):
        from types import SimpleNamespace as NS
        from export_native import cleanup_continuations
        translator = NS(parse_operand=lambda text: NS(kind="imm", imm=int(text, 0)))
        body = [NS(mnem="MOV"), NS(mnem="POP"), NS(mnem="RET")]
        image = NS(is_exec=lambda at: 0x400000 <= at < 0x401000,
                   recover=lambda at, boundaries: body)
        push = NS(addr=0x400010, mnem="PUSH", ops=["0x400080"])
        jump = NS(addr=0x400015, mnem="JMP", ops=["0x400040"])
        self.assertEqual(list(cleanup_continuations(translator, image, [push, jump])),
                         [(0x400080, 0x400010)])
        for target in ("0x20", "0x400030", "0x401500"):
            push.ops = [target]
            self.assertEqual(list(cleanup_continuations(translator, image, [push, jump])), [])
        push.ops = ["0x400080"]
        body.insert(0, NS(mnem="CALL"))
        self.assertEqual(list(cleanup_continuations(translator, image, [push, jump])), [])
        body[:] = [NS(mnem="MOV")]
        self.assertEqual(list(cleanup_continuations(translator, image, [push, jump])), [])


class ProfileTests(unittest.TestCase):
    def test_exact_images_and_disabled_builtin(self):
        sys.path.insert(0, str(ROOT / "kit/tools"))
        import game_config
        from gen_game_config import render_header
        for game_id in GAMES:
            with self.subTest(game=game_id):
                game = ROOT / "games" / game_id
                cfg = game_config.load(game)
                self.assertTrue(cfg["translate"]["resumable_stacks"])
                self.assertEqual(hashlib.sha256(cfg["developer_exe_path"].read_bytes()).hexdigest(),
                                 cfg["game"]["sha256"])
                self.assertIn("#define RECOMP_MODS_BUILTIN_POPULOUS 0", render_header(cfg))
                self.assertIn("#define RECOMP_ALLOW_RUNTIME_INTERPRETER 0", render_header(cfg))
                self.assertTrue(all(value == 0 or value == [] for value in cfg["hooks"].values()))

    def test_translation_reports(self):
        for game_id in GAMES:
            with self.subTest(game=game_id):
                report = json.loads((ROOT / "games" / game_id / "analysis/translation-report.json").read_text())
                self.assertGreater(report["functions_ok"], 400)
                for key in ("failures", "unmodelled", "table_gaps", "table_sites_undecoded"):
                    self.assertEqual(report[key], [])


class InputProbeTests(unittest.TestCase):
    def test_completed_script_retains_guest_errors(self):
        from probe_input import read_evidence
        result = read_evidence("script: 5 of 5 steps\npresented frames: 180\n"
                               "MessageBoxIndirectA: Run-time error '7':\nOut of memory\n")
        self.assertTrue(result["script_completed"])
        self.assertEqual(result["runtime_errors"], ["7"])
        self.assertEqual(result["presented_frames"], 180)

    def test_unsupported_code_and_controls(self):
        from probe_input import read_evidence
        result = read_evidence("unimplemented import ole32.dll!Test: returning 0\n"
                               "call to unknown target 74000001: returning 0\n"
                               "ListBox message 0192 is unsupported\n")
        self.assertFalse(result["script_completed"])
        self.assertEqual(result["missing_imports_called"], ["ole32.dll!Test"])
        self.assertEqual(len(result["unknown_transfers"]), 1)
        self.assertEqual(len(result["unsupported_control_messages"]), 1)


    def test_completed_script_reports_guest_access_violation(self):
        from probe_input import read_evidence
        result = read_evidence("script: 5 of 5 steps\n"
                               "[recomp] call to 00000000 (return=7405612a): raising an access violation, as Windows would\n")
        self.assertTrue(result["script_completed"])
        self.assertEqual(len(result["guest_access_violations"]), 1)


class BundledDependencyTests(unittest.TestCase):
    def test_guest_data_is_copied_and_different_existing_input_preserved(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from prepare_modules import bundle_dependency
        with TemporaryDirectory() as directory:
            game = Path(directory)
            dependencies = game / "original/dependencies"
            install = game / "original/install"
            dependencies.mkdir(parents=True)
            install.mkdir()
            (dependencies / "StdOle2.tlb").write_bytes(b"own type-library fixture")
            target = bundle_dependency(game, "stdole2.tlb")
            self.assertEqual(target.read_bytes(), b"own type-library fixture")
            self.assertEqual(bundle_dependency(game, "STDOLE2.TLB"), target)
            target.write_bytes(b"different local input")
            with self.assertRaises(ValueError):
                bundle_dependency(game, "stdole2.tlb")
            self.assertEqual(target.read_bytes(), b"different local input")


class InterfaceThunkTests(unittest.TestCase):
    def test_complete_table_and_corrupt_call(self):
        from prepare_modules import interface_thunks
        from types import SimpleNamespace
        first, count = 0x1000, 3
        handler = first + count * 8 - 3
        data = bytearray()
        for i in range(count):
            addr = first + i * 8
            data.extend(b"\xe8" + struct.pack("<i", handler - addr - 5))
            if i != count - 1:
                data.extend(b"\x2e\x8b\xc0")
        data.extend(b"\x58\x2d" + struct.pack("<I", first + 5) + bytes.fromhex(
            "d1e88b5424048b5210895424048b12ff2410"))
        image = SimpleNamespace(base=first, data=bytes(data),
                                exec_ranges=[(first, first + len(data), ".text")])
        self.assertEqual(interface_thunks(image),
                         ({first + i * 8: handler for i in range(count)}, {handler}))
        data[9] ^= 1
        image.data = bytes(data)
        self.assertEqual(interface_thunks(image), ({}, set()))


if __name__ == "__main__":
    unittest.main()
