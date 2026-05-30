from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .transcript import CaptionCue, parse_vtt


@dataclass(frozen=True)
class VideoAssets:
    video_title: str
    video_id: str
    audio_path: Path
    captions: list[CaptionCue]


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required command is not on PATH: {name}")


def _run(args: list[str], cwd: Path) -> None:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def fetch_video_assets(video_url: str, language: str, output_dir: Path) -> VideoAssets:
    require_command("yt-dlp")
    output_dir.mkdir(parents=True, exist_ok=True)

    info = json.loads(
        subprocess.check_output(
            ["yt-dlp", "--skip-download", "--dump-single-json", video_url],
            text=True,
        )
    )
    info_json = output_dir / "info.json"
    info_json.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    video_id = info.get("id", "video")
    title = info.get("title", video_id)
    base = output_dir / f"{video_id}"

    _run(
        [
            "yt-dlp",
            "--write-sub",
            "--write-auto-sub",
            "--sub-langs",
            language,
            "--sub-format",
            "vtt",
            "--skip-download",
            "-o",
            str(base) + ".%(ext)s",
            video_url,
        ],
        output_dir,
    )
    subtitle_files = sorted(output_dir.glob(f"{video_id}.{language}*.vtt"))
    if not subtitle_files:
        raise RuntimeError(f"No usable {language} transcript was downloaded for this video.")
    captions = parse_vtt(subtitle_files[0].read_text(encoding="utf-8"))
    if not captions:
        raise RuntimeError(f"The downloaded {language} transcript did not contain usable cues.")

    _run(
        [
            "yt-dlp",
            "-f",
            "bestaudio",
            "-x",
            "--audio-format",
            "mp3",
            "-o",
            str(base) + ".%(ext)s",
            video_url,
        ],
        output_dir,
    )
    audio_files = sorted(output_dir.glob(f"{video_id}*.mp3"))
    if not audio_files:
        raise RuntimeError("Audio download completed, but no mp3 file was found.")

    return VideoAssets(video_title=title, video_id=video_id, audio_path=audio_files[0], captions=captions)


def clip_audio(source: Path, start: float, end: float, target: Path) -> Path:
    require_command("ffmpeg")
    target.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.25, end - start)
    _run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source),
            "-acodec",
            "libmp3lame",
            str(target),
        ],
        target.parent,
    )
    return target
