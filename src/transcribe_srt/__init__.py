# src/transcribe_srt/cli.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
from typing import Tuple

import openai


def split_audio(wav_path: str, chunk_dir: str, chunk_secs: int = 300):
    import math

    os.makedirs(chunk_dir, exist_ok=True)

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            wav_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    total_sec = float(result.stdout.strip())
    num_chunks = math.ceil(total_sec / chunk_secs)

    for i in range(num_chunks):
        start = i * chunk_secs
        out_path = os.path.join(chunk_dir, f"chunk_{i:03d}.wav")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-t",
                str(chunk_secs),
                "-i",
                wav_path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                out_path,
            ],
            check=True,
        )


def transcribe_chunk(wav_chunk: str) -> str:
    with open(wav_chunk, "rb") as f:
        return str(
            openai.Audio.transcribe(file=f, model="whisper-1", response_format="srt")
        )


def extract_audio(ts_path: str, wav_path: str):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            ts_path,
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            wav_path,
        ],
        check=True,
    )


def adjust_srt(srt_text: str, offset_secs: int, start_index: int) -> Tuple[str, int]:
    lines = srt_text.splitlines()
    out_lines = []
    idx = start_index

    for line in lines:
        if line.isdigit():
            out_lines.append(str(idx))
            idx += 1
        elif "-->" in line:
            start, _, end = line.partition(" --> ")

            def shift(ts):
                h, m, rest = ts.split(":")
                s, ms = rest.split(",")
                total = int(h) * 3600 + int(m) * 60 + int(s) + offset_secs
                hh = total // 3600
                mm = (total % 3600) // 60
                ss = total % 60
                return f"{hh:02}:{mm:02}:{ss:02},{ms}"

            out_lines.append(f"{shift(start)} --> {shift(end)}")
        else:
            out_lines.append(line)

    return "\n".join(out_lines) + "\n\n", idx


def transcribe_to_srt(wav_path: str, srt_path: str, chunk_secs: int):
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        sys.exit(1)

    openai.api_key = api_key
    chunk_dir = "chunks"
    split_audio(wav_path, chunk_dir, chunk_secs=chunk_secs)

    offset = 0
    next_idx = 1
    merged = ""

    for i, fname in enumerate(sorted(os.listdir(chunk_dir))):
        if not fname.endswith(".wav"):
            continue
        chunk_path = os.path.join(chunk_dir, fname)

        print(f"[INFO] Transcribing chunk {i:03d}: {fname}")

        srt_piece = transcribe_chunk(chunk_path)
        adj_piece, next_idx = adjust_srt(srt_piece, offset, next_idx)
        merged += adj_piece
        offset += chunk_secs

    with open(srt_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(merged)

        for f in os.listdir(chunk_dir):
            os.remove(os.path.join(chunk_dir, f))
        os.rmdir(chunk_dir)


def main():
    if len(sys.argv) not in (3, 4):
        print("Usage: gen-sub INPUT_VIDEO OUTPUT.srt [chunk_secs]")
        sys.exit(1)

    inp, out = sys.argv[1], sys.argv[2]
    chunk_secs = int(sys.argv[3]) if len(sys.argv) == 4 else 300

    if os.path.isdir(inp):
        for fname in sorted(os.listdir(inp)):
            base, ext = os.path.splitext(fname)

            if ext.lower() not in (".mp4"):
                continue

            video_path = os.path.join(inp, fname)
            srt_path = os.path.join(out, f"{base}.srt")

            if os.path.exists(srt_path):
                print(f"[SKIP] {srt_path} already exists.")
                continue

            print(f"[INFO] Processing {video_path} -> {srt_path}")
            wav_path = os.path.join(inp, f"{base}.wav")
            extract_audio(video_path, wav_path)
            transcribe_to_srt(wav_path, srt_path, chunk_secs)
            os.remove(wav_path)
    else:
        video_path = inp
        srt_path = out

        if os.path.exists(srt_path):
            print(f"[SKIP] {srt_path} already exists.")
            return

        print(f"[INFO] Processing {video_path} -> {srt_path}")
        wav_path = os.path.splitext(video_path)[0] + ".wav"
        extract_audio(video_path, wav_path)
        transcribe_to_srt(wav_path, srt_path, chunk_secs)
        os.remove(wav_path)
