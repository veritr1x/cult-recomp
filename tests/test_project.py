"""Portable contracts for public profiles and local input preparation."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "kit/tools"))

from test_inputs import (BundledDependencyTests, CompressionTests, InputProbeTests,
                         InterfaceThunkTests, NativeExportTests)  # noqa: F401,E402
import game_config  # noqa: E402
from gen_game_config import render_header  # noqa: E402


def test_static_profiles_and_auxiliary_modules():
    expected = {
        "cult": ("Cult.exe", "20d5795b17047cc18c6eca7daa668f1a7694bee363819cc1070c2a882b0aacca"),
        "cult2": ("Cult2FC.exe", "d574e3a84823829f58ef858d4fdf95a855551a96bd8f36a1314571124fdec316"),
    }
    for game_id, (executable, digest) in expected.items():
        cfg = game_config.load(ROOT / "games" / game_id)
        assert cfg["game"]["id"] == game_id
        assert cfg["game"]["executable"] == executable
        assert cfg["game"]["sha256"] == digest
        assert cfg["translate"]["resumable_stacks"]
        assert len(cfg["aux_modules"]) == 4
        assert len({module["key"] for module in cfg["aux_modules"]}) == 4
        header = render_header(cfg)
        assert "#define RECOMP_ALLOW_RUNTIME_INTERPRETER 0" in header
        assert "#define RECOMP_MODS_BUILTIN_POPULOUS 0" in header
        assert all(value == 0 or value == [] for value in cfg["hooks"].values())
