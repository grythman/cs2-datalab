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

# LOW-MID AMBIENCE instead of tonal chords
def make_music_bed():
    duration = 24.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    # Low rumble and texture
    rumble = 0.1 * np.sin(2 * np.pi * 50 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t))
    noise = np.random.default_rng(7).normal(0.0, 0.015, len(t)).astype(np.float32)
    filtered_noise = np.convolve(noise, np.ones(50)/50, mode='same')
    audio = rumble + 0.5 * filtered_noise
    audio *= envelope(len(audio), 0.05, 0.08)
    return audio * 0.15

def make_music_intro():
    duration = 8.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    air = np.random.default_rng(31).normal(0.0, 0.02, len(t)).astype(np.float32)
    filtered_air = np.convolve(air, np.ones(20)/20, mode='same')
    rise = np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 0.5
    audio = filtered_air * (0.2 + 0.8 * rise)
    audio *= envelope(len(audio), 0.12, 0.35)
    return audio * 0.2

def make_music_outro():
    duration = 9.0
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    rumble = 0.1 * np.sin(2 * np.pi * 40 * t) 
    tail_noise = np.random.default_rng(37).normal(0.0, 0.01, len(t)).astype(np.float32)
    filtered_noise = np.convolve(tail_noise, np.ones(30)/30, mode='same')
    settle = 1.0 - np.clip(t / max(duration, 1e-6), 0.0, 1.0) ** 1.5
    audio = (rumble + 0.8 * filtered_noise) * settle
    audio *= envelope(len(audio), 0.04, 0.45)
    return audio * 0.15

# TEXTURE/PERCUSSION instead of tonal transition
def make_transition_swoosh():
    duration = 0.42
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    noise = np.random.default_rng(11).normal(0.0, 0.1, len(t)).astype(np.float32)
    # create a fast whoosh filter effect conceptually with envelope
    intensity = 1.0 - np.abs((t - duration/2) / (duration/2))
    audio = noise * intensity
    audio *= envelope(len(audio), 0.2, 0.2)
    return audio * 0.3

def make_impact_hit():
    duration = 0.28
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False, dtype=np.float32)
    noise = np.random.default_rng(23).normal(0.0, 0.1, len(t)).astype(np.float32) * np.exp(-30 * t)
    sub_thump = np.sin(2 * np.pi * 50 * t) * np.exp(-10 * t)
    audio = 0.4 * noise + 0.6 * sub_thump
    audio *= envelope(len(audio), 0.01, 0.9)
    return audio * 0.4

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    write_wav(str(OUTPUT_DIR / "music_bed.wav"), make_music_bed())
    write_wav(str(OUTPUT_DIR / "music_intro.wav"), make_music_intro())
    write_wav(str(OUTPUT_DIR / "music_outro.wav"), make_music_outro())
    write_wav(str(OUTPUT_DIR / "transition_swoosh.wav"), make_transition_swoosh())
    write_wav(str(OUTPUT_DIR / "impact_hit.wav"), make_impact_hit())
    print("Generated cinematic ambience audio assets in", OUTPUT_DIR)

if __name__ == "__main__":
    main()
