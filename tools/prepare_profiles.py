"""Create exact-image RecompKit profiles from the locally inspected game binaries."""

import json
from import_archives import GAMES, ROOT

NAMES = {"cult": ("Cult", "CultRecomp", "Cult"),
         "cult2": ("Cult II - Federal Crime", "Cult2Recomp", "Cult2FC")}


def main():
    for game_id, (_, executable) in GAMES.items():
        game = ROOT / "games" / game_id
        report = json.loads((game / "analysis/pe-report.json").read_text())
        name, app, directory = NAMES[game_id]
        entries = ", ".join(f"0x{a:08x}" for a in report["vb"]["structural_entry_points"])
        text = f'''# Exact supplied image. Native code translation remains experimental.
[game]
id = "{game_id}"
name = "{name}"
app_name = "{app}"
bundle_id = "dev.recompkit.{game_id}"
executable = "{executable}"
sha256 = "{report['sha256']}"
image_base = 0x{report['image_base']:08x}
entry_point = 0x{report['entry_point']:08x}
guest_root = 'C:\\{directory}'
developer_exe = "original/install/{executable}"
windows_version = "4.10"

[translate]
allow_runtime_interpreter = false
function_alignment = 4
listings = "analysis/{executable}"
globals = "globals.toml"
animation_counter = 0
volatile_reads = []
entry_points = [{entries}]

[hooks]
# Zero means no audited native timing or pointer adapter for this game.
frame_clock_begin = 0
frame_clock_wait = 0
frame_clock_wait_clamp = 0
frame_clock_clamp_deadline = 0
frame_clock_wait_deadline = 0
cursor_surface_ptrs = []
mouse_vtable = 0
mouse_device_ptr = 0
mouse_device_right = 0
camera = 0

[controls]
default_layout = "keys"
pad = "mapped"

[controls.mapped]
left_stick = "cursor"
dpad = "arrows"
cross = "mouse_left"
circle = "key:Escape"

[mods]
builtin = "none"

[bundle]
exclude = ["*.DEP", "ReadMe.txt", "Cheats.txt", "*.url", "file_id.diz"]
'''
        target = game / "game.toml"
        if target.exists() and "\n[modules.aux." in target.read_text():
            # Preserve hash-pinned DLL configuration from prepare_modules.py.
            current = target.read_text()
            text = text.replace('[game]\n', '[game]\nguest_size = 0x74200000\n')
            text += current[current.index("\n[modules.aux."):]
        if target.exists() and target.read_text() != text:
            raise ValueError(f"Preserving modified profile: {target}")
        target.write_text(text, newline="\n")
        globals_path = game / "globals.toml"
        if not globals_path.exists():
            globals_path.write_text("# No game globals or gameplay hooks have been audited yet.\n[globals]\n", newline="\n")
        print(f"{game_id}: profile pinned to {report['sha256']}")


if __name__ == "__main__":
    main()
