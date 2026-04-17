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
        0.14 * np.sin(2 * np.pi * 72 * t)
        + 0.10 * np.sin(2 * np.pi * 108 * t)
        + 0.06 * np.sin(2 * np.pi * 144 * t)
    )
    pulse = 0.72 + 0.14 * np.sin(2 * np.pi * 0.09 * t)
    noise = np.random.default_rng(7).normal(0.0, 0.012, len(t)).astype(np.float32)
    audio = (chords + 0.35 * noise) * pulse
    audio *= envelope(len(audio), 0.05, 0.08)
    return audio * 0.20


def make_music_intro():
    duration = 8.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    pad = (
        0.15 * np.sin(2 * np.pi * 98 * t)
        + 0.11 * np.sin(2 * np.pi * 147 * t)
        + 0.07 * np.sin(2 * np.pi * 196 * t)
    )
    air = np.random.default_rng(31).normal(0.0, 0.018, len(t)).astype(np.float32)
    rise = np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 0.7
    audio = (pad + 0.45 * air) * (0.42 + 0.58 * rise)
    audio *= envelope(len(audio), 0.12, 0.35)
    return audio * 0.19


def make_music_outro():
    duration = 9.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    base = (
        0.20 * np.sin(2 * np.pi * 68 * t)
        + 0.13 * np.sin(2 * np.pi * 102 * t)
        + 0.08 * np.sin(2 * np.pi * 136 * t)
    )
    sub = 0.09 * np.sin(2 * np.pi * 48 * t) * (0.65 + 0.35 * np.sin(2 * np.pi * 0.14 * t))
    tail_noise = np.random.default_rng(37).normal(0.0, 0.014, len(t)).astype(np.float32)
    settle = 1.0 - np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 1.2
    audio = (base + sub + 0.42 * tail_noise) * (0.35 + 0.65 * settle)
    audio *= envelope(len(audio), 0.04, 0.45)
    return audio * 0.18


def make_transition_swoosh():
    duration = 0.42
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    freq = 120 + 880 * (t / duration) ** 1.2
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    tone = np.sin(phase)
    airy = 0.25 * np.sin(phase * 0.45 + 1.0)
    noise = np.random.default_rng(11).normal(0.0, 0.06, len(t)).astype(np.float32)
    audio = (0.58 * tone + 0.22 * airy + 0.20 * noise)
    audio *= envelope(len(audio), 0.08, 0.72)
    return audio * 0.30


def make_impact_hit():
    duration = 0.28
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    thump = np.sin(2 * np.pi * 78 * t) * np.exp(-14 * t)
    click = np.sin(2 * np.pi * 340 * t) * np.exp(-30 * t)
    grit = np.random.default_rng(23).normal(0.0, 0.035, len(t)).astype(np.float32) * np.exp(-24 * t)
    audio = 0.82 * thump + 0.18 * click + grit
    audio *= envelope(len(audio), 0.03, 0.85)
    return audio * 0.42


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
