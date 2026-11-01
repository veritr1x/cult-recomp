# Testing

Prepare the recursive submodule, hashed Python environment and source patch
first, following [README.md](../README.md). No game input is needed for CI.

| Command | Coverage | Needs game files? |
| --- | --- | --- |
| `python tools/test.py` | Shared kit portable suites, once for the default profile | No |
| `python -m pytest -q tests` | Importer, exporter, probe and exact-image profile contracts | No |
| `python tools/check_repo.py` | Tracked publication inputs and documentation links | No |
| `python tools/build.py --game all --stub` | Both profiles linked against stub translations | No |
| `python tools/test.py --game cult --compile-only` | Native test binaries through the kit build API | No |
| `ctest --test-dir <build dir> -L nogame --output-on-failure` | Native game-independent suites | No |
| `python tools/test_inputs.py` | Exact local input hashes and translation reports, plus tool contracts | Yes |
| `python tools/probe_input.py --game all --scenario save --max-seconds 120` | Fresh movement/save/load round trips through smoke hosts | Yes |

Native compilation always goes through tools/build.py or tools/test.py. Use
`--preset` and `--jobs` as needed. The kit's portable suites need Node 22 for
browser launcher checks; native compilation also needs the platform toolchain.
CI checks both profile stub builds on Windows, Linux and macOS, including
unsigned iOS stub compilation on macOS. This does not establish mobile gameplay.

Build smoke hosts before game probes. Probe evidence lives under each profile's
ignored build directory. The save probe owns `build/save-probe/profile`; archive
its old diagnostic folder before a fresh run. Never point a probe at a player's
profile. A passed script must also have fresh saves, equal restored state,
changed player coordinates and no reported guest errors. Captures and counters
alone do not prove full playability or performance. See [analysis.md](analysis.md)
for current results and [status.md](status.md) for historical device settings.
