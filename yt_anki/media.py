from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .transcript import CaptionCue, parse_json3, parse_vtt


@dataclass(frozen=True)
class VideoAssets:
    video_title: str
    video_id: str
    audio_path: Path
    captions: list[CaptionCue]


def yt_dlp_command() -> list[str]:
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]
    return [sys.executable, "-m", "yt_dlp"]


def ffmpeg_command() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        import imageio_ffmpeg
    except ImportError as exc:
        raise RuntimeError(
            "ffmpeg is required. Install project dependencies or put ffmpeg on PATH."
        ) from exc
    return imageio_ffmpeg.get_ffmpeg_exe()


def node_command() -> str | None:
    return shutil.which("node")


def yt_dlp_environment_args(ffmpeg: str) -> list[str]:
    args = ["--ffmpeg-location", ffmpeg]
    node = node_command()
    if node:
        args.extend(["--js-runtimes", f"node:{node}"])
    return args


def _run(args: list[str], cwd: Path) -> None:
    completed = subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )


def fetch_video_assets(video_url: str, language: str, output_dir: Path) -> VideoAssets:
    yt_dlp = yt_dlp_command()
    ffmpeg = ffmpeg_command()
    env_args = yt_dlp_environment_args(ffmpeg)
    output_dir.mkdir(parents=True, exist_ok=True)

    info = json.loads(
        subprocess.check_output(
            [*yt_dlp, *env_args, "--skip-download", "--dump-single-json", video_url],
            text=True,
        )
    )
    info_json = output_dir / "info.json"
    info_json.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")

    video_id = info.get("id", "video")
    title = info.get("title", video_id)
    output_template = f"{video_id}.%(ext)s"

    _run(
        [
            *yt_dlp,
            *env_args,
            "--write-sub",
            "--write-auto-sub",
            "--sub-langs",
            language,
            "--sub-format",
            "json3/vtt",
            "--skip-download",
            "-o",
            output_template,
            video_url,
        ],
        output_dir,
    )
    subtitle_files = sorted(output_dir.glob(f"{video_id}.{language}*.json3"))
    subtitle_parser = parse_json3
    if not subtitle_files:
        subtitle_files = sorted(output_dir.glob(f"{video_id}.{language}*.vtt"))
        subtitle_parser = parse_vtt
    if not subtitle_files:
        raise RuntimeError(f"No usable {language} transcript was downloaded for this video.")
    captions = subtitle_parser(subtitle_files[0].read_text(encoding="utf-8"))
    if not captions:
        raise RuntimeError(f"The downloaded {language} transcript did not contain usable cues.")

    _run(
        [
            *yt_dlp,
            *env_args,
            "-f",
            "bestaudio",
            "-x",
            "--audio-format",
            "mp3",
            "-o",
            output_template,
            video_url,
        ],
        output_dir,
    )
    audio_files = sorted(output_dir.glob(f"{video_id}*.mp3"))
    if not audio_files:
        raise RuntimeError("Audio download completed, but no mp3 file was found.")

    return VideoAssets(video_title=title, video_id=video_id, audio_path=audio_files[0], captions=captions)


def clip_audio(source: Path, start: float, end: float, target: Path) -> Path:
    ffmpeg = ffmpeg_command()
    if not source.exists():
        raise RuntimeError(f"Source audio file does not exist: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    duration = max(0.25, end - start)
    _run(
        [
            ffmpeg,
            "-y",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(source),
            "-vn",
            "-acodec",
            "libmp3lame",
            str(target),
        ],
        target.parent,
    )
    if not target.exists() or target.stat().st_size == 0:
        raise RuntimeError(f"ffmpeg did not create a usable audio clip: {target}")
    return target
