#!/usr/bin/env python3
"""Verify a local narration MP4 before delivery; no networking or downloads."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path


def executable(name: str) -> str:
    result = shutil.which(name)
    if not result:
        raise ValueError("missing_media_tool")
    return result


def signature(file: Path) -> tuple[int, int, int, int]:
    stat = file.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino


def verify(file: Path, ffprobe: str = "ffprobe", ffmpeg: str = "ffmpeg",
           promote_to: Path | None = None, timeout: float = 900) -> dict:
    if file.is_symlink() or not file.is_file():
        raise ValueError("media_missing_or_symlink")
    if promote_to is None and file.suffix.lower() != ".mp4":
        raise ValueError("unfinished_or_non_mp4_file")
    if promote_to is not None:
        if file.suffix.lower() != ".part" or promote_to.suffix.lower() != ".mp4":
            raise ValueError("promotion_requires_part_to_mp4")
        if file.resolve().parent != promote_to.resolve().parent:
            raise ValueError("promotion_requires_same_directory")
        if promote_to.exists() or promote_to.is_symlink():
            raise ValueError("destination_already_exists")
    probe_tool, decode_tool = executable(ffprobe), executable(ffmpeg)
    initial = signature(file)
    if initial[0] <= 1024:
        raise ValueError("file_too_small")
    with file.open("rb") as handle:
        header = handle.read(12)
    if header[4:8] != b"ftyp":
        raise ValueError("not_mp4_header")
    process = subprocess.run(
        [probe_tool, "-v", "error", "-show_entries",
         "format=format_name,duration:stream=codec_type,codec_name,width,height,r_frame_rate",
         "-of", "json", str(file)], capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, check=False)
    if process.returncode != 0:
        raise ValueError("ffprobe_failed")
    media = json.loads(process.stdout)
    duration = float(media["format"]["duration"])
    if "mp4" not in media["format"]["format_name"].split(",") or not math.isfinite(duration) or duration <= 0:
        raise ValueError("invalid_container_or_duration")
    streams = media.get("streams", [])
    video = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if not video or not audio:
        raise ValueError("narration_requires_video_and_audio")
    for stream in video:
        if not stream.get("codec_name") or int(stream.get("width", 0)) <= 0 or int(stream.get("height", 0)) <= 0:
            raise ValueError("invalid_video_stream")
        if Fraction(stream.get("r_frame_rate", "0/1")) <= 0:
            raise ValueError("invalid_frame_rate")
    if any(not stream.get("codec_name") for stream in audio):
        raise ValueError("invalid_audio_stream")
    decoded = subprocess.run(
        [decode_tool, "-nostdin", "-v", "error", "-xerror", "-i", str(file),
         "-map", "0:v", "-map", "0:a", "-f", "null", "-"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=timeout, check=False)
    if decoded.returncode != 0 or decoded.stderr.strip():
        raise ValueError("full_decode_failed")
    digest = hashlib.sha256()
    with file.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    if signature(file) != initial:
        raise ValueError("file_changed_during_validation")
    final = file
    if promote_to is not None:
        # A hard link creates the new name atomically and fails if it already exists.
        # Unsupported filesystems fail here and keep the incomplete source name.
        os.link(file, promote_to)
        final = promote_to
        if signature(final) != initial:
            raise ValueError("file_changed_during_promotion")
        file.unlink()
    return {"status": "passed", "file": str(final.resolve()), "bytes": initial[0],
            "sha256": digest.hexdigest(), "duration_seconds": duration,
            "probe_exit": process.returncode, "decode_exit": decoded.returncode,
            "media": media, "content_identity_checked": False, "background_music_listened": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--promote-to", type=Path)
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    try:
        result = verify(args.file, args.ffprobe, args.ffmpeg, args.promote_to, args.timeout)
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError,
            subprocess.TimeoutExpired):
        # Do not echo subprocess stderr, which can contain sensitive paths or input.
        print(json.dumps({"status": "failed", "reason": "media_check_or_safe_promotion_failed"}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
