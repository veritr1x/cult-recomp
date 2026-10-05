"""Run a bounded SDL desktop startup using the actual presenter and audio device."""

import argparse
import array
import json
import os
import platform
import re
import subprocess
import sys
import wave
from pathlib import Path

from import_archives import GAMES, ROOT
from probe_input import read_evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=[*GAMES, "all"], default="all")
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--audio-ahead", type=int)
    parser.add_argument("--player", action="store_true", help="Test the assembled private launcher")
    args = parser.parse_args()
    if not 0 < args.seconds <= 120:
        parser.error("--seconds must be between 0 and 120")
    if args.audio_ahead is not None and args.audio_ahead <= 0:
        parser.error("--audio-ahead must be positive")
    failed = False
    for game in GAMES if args.game == "all" else [args.game]:
        name = "CultRecomp" if game == "cult" else "Cult2Recomp"
        folder = ROOT / "games" / game / "build/package" / name
        if args.player:
            folder = ROOT / "build/player" / platform.system().lower() / name
        binary = folder / (name + ".exe" if os.name == "nt" else name)
        evidence_dir = ROOT / "games" / game / "build/desktop-probe" / platform.system().lower()
        if args.player:
            evidence_dir /= "player"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        audio_file = evidence_dir / "audio.wav"
        audio_file.unlink(missing_ok=True)
        env = {key: value for key, value in os.environ.items() if not key.startswith("RECOMP_")}
        if os.name == "nt":
            env["PATH"] = os.environ["SystemRoot"] + "/System32;" + os.environ["SystemRoot"]
        env.update(RECOMP_HOST_SECONDS=str(args.seconds), RECOMP_NO_MODS="1",
                   RECOMP_PROFILE_DIR=str(evidence_dir / "profile"), RECOMP_LOG="1",
                   RECOMP_HOST_AUDIO_CAPTURE=str(audio_file))
        if args.audio_ahead is not None:
            env["RECOMP_AUDIO_AHEAD"] = str(args.audio_ahead)
        executable = "Cult.exe" if game == "cult" else "Cult2FC.exe"
        env["RECOMP_EXE"] = str(ROOT / "games" / game / "original/install" / executable)
        timed_out = False
        launcher = folder / ("Play.cmd" if os.name == "nt" else "Play.sh")
        command = ([str(Path(os.environ["SystemRoot"]) / "System32/cmd.exe"), "/d", "/c", str(launcher)]
                   if os.name == "nt" else [str(launcher)]) if args.player else [str(binary)]
        try:
            result = subprocess.run(command, cwd=folder, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=args.seconds + 50)
            output, code = result.stdout, result.returncode
        except subprocess.TimeoutExpired as error:
            output, code, timed_out = error.stdout or b"", None, True
        (evidence_dir / "startup.log").write_bytes(output)
        log = output.decode("utf-8", errors="replace")
        evidence = read_evidence(log)
        record = {"platform": f"{platform.system()} {platform.machine()}",
                  "returncode": code, "timed_out": timed_out, "executable": str(binary),
                  "launcher": str(launcher) if args.player else None,
                  "seconds_requested": args.seconds, **evidence,
                  "physical_input_verified": False, "audible_output_verified": False,
                  "audio_device_running": "[host] audio device running:" in log,
                  "audio_device_errors": re.findall(r"\[host\] audio: no playback device:[^\n]*", log),
                  "sdl_video_driver_requested": env.get("SDL_VIDEODRIVER"),
                  "sdl_audio_driver_requested": env.get("SDL_AUDIODRIVER"),
                  "pulse_latency_ms_requested": env.get("PULSE_LATENCY_MSEC"),
                  "audio_ahead_frames_requested": env.get("RECOMP_AUDIO_AHEAD"),
                  "presenter_faults": re.findall(r"presenter: FAULT:[^\n]*", log),
                  "playability_verified": False}
        # A startup run has no input script. Success requires actual presents
        # and a clean guest shutdown; silent mixer output is valid at a menu.
        record.pop("script_completed")
        if audio_file.is_file():
            try:
                with wave.open(str(audio_file), "rb") as capture:
                    if capture.getsampwidth() != 2:
                        raise ValueError("Expected PCM16 capture")
                    samples = array.array("h", capture.readframes(capture.getnframes()))
                    if sys.byteorder != "little":
                        samples.byteswap()
                    record["captured_audio"] = {
                        "sample_rate": capture.getframerate(), "channels": capture.getnchannels(),
                        "frames": capture.getnframes(),
                        "peak_pcm16": max(map(abs, samples), default=0)}
            except (wave.Error, ValueError, EOFError) as error:
                record["audio_capture_error"] = str(error)
        record["verified"] = (code == 0 and not timed_out and
                              (record["presented_frames"] or 0) > 0 and not any(
                                  record[key] for key in ("missing_imports_called", "unknown_transfers",
                                                         "runtime_errors", "guest_access_violations",
                                                         "unsupported_control_messages", "presenter_faults")))
        record["audio_device_verified"] = (record["audio_device_running"] and
                                           record.get("captured_audio", {}).get("frames", 0) > 0)
        (evidence_dir / "result.json").write_text(json.dumps(record, indent=2) + "\n")
        failed |= not record["verified"]
        print(f"{game}: exit={code}, timeout={timed_out}, frames={record['presented_frames']}, "
              f"verified={record['verified']}")
        print(f"Evidence: {evidence_dir / 'result.json'}")
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
