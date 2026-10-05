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


class ProfileTests(unittest.TestCase):
    def test_exact_images_and_disabled_builtin(self):
        sys.path.insert(0, str(ROOT / "kit/tools"))
        import game_config
        from gen_game_config import render_header
        for game_id in GAMES:
            with self.subTest(game=game_id):
                game = ROOT / "games" / game_id
                cfg = game_config.load(game)
                self.assertEqual(hashlib.sha256(cfg["developer_exe_path"].read_bytes()).hexdigest(),
                                 cfg["game"]["sha256"])
                self.assertIn("#define RECOMP_MODS_BUILTIN_POPULOUS 0", render_header(cfg))
                self.assertTrue(all(value == 0 or value == [] for value in cfg["hooks"].values()))

    def test_translation_reports(self):
        for game_id in GAMES:
            with self.subTest(game=game_id):
                report = json.loads((ROOT / "games" / game_id / "analysis/translation-report.json").read_text())
                self.assertGreater(report["functions_ok"], 400)
                for key in ("failures", "unmodelled", "table_gaps", "table_sites_undecoded"):
                    self.assertEqual(report[key], [])


if __name__ == "__main__":
    unittest.main()
