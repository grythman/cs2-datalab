#!/usr/bin/env python3
import os
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 44100
OUTPUT_DIR = Path(__file__).resolve().parent / "audio"


def envelope(length, attack, release):
    env = np.ones(length, dtype=np.float32)
    attack_len = max(1, int(length * attack))
    release_len = max(1, int(length * release))
    env[:attack_len] = np.linspace(0.0, 1.0, attack_len, dtype=np.float32)
    env[-release_len:] = np.linspace(1.0, 0.0, release_len, dtype=np.float32)
    return env


def write_wav(path, samples):
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm])
    with wave.open(path, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(stereo.tobytes())


def make_music_bed():
    duration = 24.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    chords = (
        0.18 * np.sin(2 * np.pi * 92 * t)
        + 0.14 * np.sin(2 * np.pi * 138 * t)
        + 0.10 * np.sin(2 * np.pi * 184 * t)
    )
    shimmer = 0.04 * np.sin(2 * np.pi * 368 * t + 0.4 * np.sin(2 * np.pi * 0.2 * t))
    pulse = 0.72 + 0.18 * np.sin(2 * np.pi * 0.11 * t)
    noise = np.random.default_rng(7).normal(0.0, 0.015, len(t)).astype(np.float32)
    audio = (chords + shimmer + noise) * pulse
    audio *= envelope(len(audio), 0.05, 0.08)
    return audio * 0.22


def make_music_intro():
    duration = 8.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    shimmer = (
        0.18 * np.sin(2 * np.pi * 220 * t)
        + 0.14 * np.sin(2 * np.pi * 330 * t + 0.3 * np.sin(2 * np.pi * 0.5 * t))
        + 0.08 * np.sin(2 * np.pi * 440 * t)
    )
    air = np.random.default_rng(31).normal(0.0, 0.02, len(t)).astype(np.float32)
    rise = np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 0.7
    audio = (shimmer + 0.55 * air) * (0.45 + 0.55 * rise)
    audio *= envelope(len(audio), 0.12, 0.35)
    return audio * 0.24


def make_music_outro():
    duration = 9.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    base = (
        0.24 * np.sin(2 * np.pi * 82 * t)
        + 0.16 * np.sin(2 * np.pi * 123 * t)
        + 0.10 * np.sin(2 * np.pi * 164 * t)
    )
    sub = 0.12 * np.sin(2 * np.pi * 56 * t) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.15 * t))
    tail_noise = np.random.default_rng(37).normal(0.0, 0.018, len(t)).astype(np.float32)
    settle = 1.0 - np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 1.2
    audio = (base + sub + 0.45 * tail_noise) * (0.35 + 0.65 * settle)
    audio *= envelope(len(audio), 0.04, 0.45)
    return audio * 0.26


def make_transition_swoosh():
    duration = 0.42
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    freq = 180 + 2400 * (t / duration) ** 1.4
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase)
    airy = 0.4 * np.sin(phase * 0.5 + 1.2)
    noise = np.random.default_rng(11).normal(0.0, 0.10, len(t)).astype(np.float32)
    audio = (0.72 * tone + 0.28 * airy + 0.22 * noise)
    audio *= envelope(len(audio), 0.08, 0.72)
    return audio * 0.5


def make_impact_hit():
    duration = 0.28
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    thump = np.sin(2 * np.pi * 95 * t) * np.exp(-14 * t)
    click = np.sin(2 * np.pi * 900 * t) * np.exp(-34 * t)
    grit = np.random.default_rng(23).normal(0.0, 0.05, len(t)).astype(np.float32) * np.exp(-26 * t)
    audio = 0.9 * thump + 0.35 * click + grit
    audio *= envelope(len(audio), 0.03, 0.85)
    return audio * 0.72


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    write_wav(str(OUTPUT_DIR / "music_bed.wav"), make_music_bed())
    write_wav(str(OUTPUT_DIR / "music_intro.wav"), make_music_intro())
    write_wav(str(OUTPUT_DIR / "music_outro.wav"), make_music_outro())
    write_wav(str(OUTPUT_DIR / "transition_swoosh.wav"), make_transition_swoosh())
    write_wav(str(OUTPUT_DIR / "impact_hit.wav"), make_impact_hit())
    print("Generated audio assets in", OUTPUT_DIR)


if __name__ == "__main__":
    main()
