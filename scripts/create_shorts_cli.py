#!/usr/bin/env python3
import asyncio
import json
import math
import os
import re
import sys
from dataclasses import dataclass

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from moviepy.audio.AudioClip import AudioArrayClip, CompositeAudioClip
from moviepy.editor import AudioFileClip, CompositeVideoClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

W, H = 720, 1280
FPS = 20
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
VOICE_PATH = "/data/videos/temp_voice.mp3"
MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
MOUZ = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}
PLAYER_COLORS = {name: (255, 205, 0) for name in MONGOLZ} | {name: (255, 92, 92) for name in MOUZ}
ACCENTS = {
    "hook": (255, 190, 0),
    "heatmap": (255, 190, 0),
    "firstkill": (255, 220, 110),
    "deathmap": (255, 90, 190),
    "economy": (80, 220, 130),
    "utility": (80, 210, 255),
    "awp": (120, 220, 255),
    "round": (255, 140, 80),
    "clutch": (255, 90, 90),
}


async def generate_voiceover(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, "mn-MN-YesuiNeural")
    await communicate.save(output_path)


@dataclass
class SceneSpec:
    key: str
    title: str
    subtitle: str
    image: str
    layout: str
    focus: tuple[float, float]
    blur: int
    motion: tuple[float, float]


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def clip_script(text: str, limit: int = 1500) -> str:
    cleaned = normalize_text(text)
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit]
    last_stop = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    return cut[: last_stop + 1] if last_stop > 160 else cut + "..."


def split_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalize_text(text)) if part.strip()]
    return parts or ["CS2 тоглолтын гол мөчүүдийг харцгаая."]


def get_kills(data: dict) -> list:
    raw = data.get("kills", [])
    return raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw


def extract_rounds(kills: list[dict]) -> list[list[dict]]:
    ordered = sorted([kill for kill in kills if isinstance(kill, dict)], key=lambda item: item.get("tick", 0))
    if not ordered:
        return []
    rounds = []
    current = [ordered[0]]
    for kill in ordered[1:]:
        if kill.get("tick", 0) - current[-1].get("tick", 0) > 1000:
            rounds.append(current)
            current = [kill]
        else:
            current.append(kill)
    rounds.append(current)
    return rounds


def analyze_match(data: dict) -> dict:
    kills = get_kills(data)
    rounds = extract_rounds(kills)
    score: dict[str, int] = {}
    mongolz_kills = 0
    mouz_kills = 0
    for kill in kills:
        if not isinstance(kill, dict):
            continue
        attacker = kill.get("attacker_name", "")
        if attacker:
            score[attacker] = score.get(attacker, 0) + 1
        if attacker in MONGOLZ:
            mongolz_kills += 1
        elif attacker in MOUZ:
            mouz_kills += 1
    top_fragger = max(score, key=score.get) if score else "Unknown"
    return {
        "mongolz_kills": mongolz_kills,
        "mouz_kills": mouz_kills,
        "rounds": len(rounds),
        "first_kill": rounds[0][0].get("attacker_name", "Unknown") if rounds else "Unknown",
        "top_fragger": top_fragger,
        "top_kills": score.get(top_fragger, 0),
    }


def find_assets(match_id: str, map_name: str, heatmap_img: str, awp_img: str) -> dict[str, str]:
    visual_dir = os.path.dirname(heatmap_img) or "/data/visuals"
    assets = {
        "hook": heatmap_img,
        "heatmap": heatmap_img,
        "firstkill": f"{visual_dir}/{match_id}_{map_name}_firstkill.png",
        "deathmap": f"{visual_dir}/{match_id}_{map_name}_deathmap.png",
        "tactics": f"{visual_dir}/{match_id}_{map_name}_tactics.png",
        "economy": f"{visual_dir}/{match_id}_{map_name}_economy.png",
        "utility": f"{visual_dir}/{match_id}_{map_name}_utility.png",
        "awp": awp_img,
        "round": f"{visual_dir}/{match_id}_{map_name}_round_26.png",
        "clutch": f"{visual_dir}/{match_id}_{map_name}_clutch_round_45.png",
    }
    return {key: path for key, path in assets.items() if path and os.path.exists(path)}


def build_scenes(assets: dict[str, str], stats: dict) -> list[SceneSpec]:
    base = [
        ("hook", "MOUZ VS MONGOLZ", "Mirage дээр momentum хаана эргэсэн бэ?", "hook", (0.18, 0.18), 14, (0.03, 0.02)),
        ("heatmap", "HEATMAP", "Mid дээр тулааны нягтрал хамгийн өндөр.", "focus", (0.50, 0.50), 22, (0.00, 0.00)),
        ("firstkill", "FIRST KILL", f"{stats['first_kill']} эхний цохилтыг нээсэн.", "split", (0.50, 0.50), 20, (0.00, 0.00)),
        ("deathmap", "DEATH MAP", "Trade pattern ба уналтын бүсүүд.", "focus", (0.50, 0.50), 26, (0.00, 0.00)),
        ("economy", "ECONOMY", "Мөнгөний давуу тал tempo-г шийдсэн.", "split", (0.50, 0.50), 18, (0.00, 0.00)),
        ("utility", "UTILITY", "Flash, smoke pressure map control-ийг нээсэн.", "split", (0.50, 0.50), 20, (0.00, 0.00)),
        ("awp", "AWP LINES", "Снайперын хяналт choke point-уудыг түгжсэн.", "focus", (0.50, 0.50), 22, (0.00, 0.00)),
        ("round", "KEY ROUND", "Momentum shift-ийг round map дээр харуулъя.", "focus", (0.50, 0.50), 24, (0.00, 0.00)),
        ("clutch", "CLUTCH", f"{stats['top_fragger']} даралттай мөчийг хаасан.", "focus", (0.50, 0.50), 28, (0.00, 0.00)),
    ]
    scenes = [
        SceneSpec(key, title, subtitle, assets[key], layout, focus, blur, motion)
        for key, title, subtitle, layout, focus, blur, motion in base
        if key in assets
    ]
    return scenes[:8] if len(scenes) > 8 else scenes


def safe_json_load(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        raise RuntimeError(f"JSON уншихад алдаа гарлаа: {path} :: {exc}") from exc


def safe_generate_voiceover(text: str, output_path: str) -> bool:
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
        asyncio.run(generate_voiceover(text, output_path))
        if not os.path.exists(output_path):
            print("Warning: edge_tts output file was not created.")
            return False
        size = os.path.getsize(output_path)
        if size <= 1024:
            print(f"Warning: edge_tts output file is empty or too small ({size} bytes).")
            return False
        return True
    except Exception as exc:
        print(f"Warning: edge_tts generation failed: {exc}")
        return False


def make_silent_audio(duration: float, fps: int = 44100) -> AudioArrayClip:
    samples = max(1, int(duration * fps))
    arr = np.zeros((samples, 2), dtype=np.float32)
    return AudioArrayClip(arr, fps=fps).set_duration(duration)


def load_voice_clip(script_text: str) -> AudioFileClip | AudioArrayClip:
    if safe_generate_voiceover(script_text, VOICE_PATH):
        try:
            clip = AudioFileClip(VOICE_PATH)
            if clip.duration <= 0:
                print("Warning: temp_voice.mp3 loaded but has zero duration.")
            else:
                print(
                    f"Voice clip ready: duration={clip.duration:.2f}s "
                    f"fps={getattr(clip, 'fps', 'unknown')} channels={getattr(clip, 'nchannels', 'unknown')}"
                )
                return clip
        except Exception as exc:
            print(f"Warning: failed to load temp voice clip: {exc}")
    estimated = max(18.0, min(52.0, len(script_text.split()) * 0.45))
    print(f"Warning: using silent fallback audio clip ({estimated:.2f}s).")
    return make_silent_audio(estimated)


def text_bbox_width(font, text: str) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def fit_font_size(text: str, font_path: str, start_size: int, max_width: int, min_size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = start_size
    while size > min_size:
        font = load_font(font_path, size)
        if text_bbox_width(font, text) <= max_width:
            return font
        size -= 2
    return load_font(font_path, min_size)


def wrap_text(text: str, font, max_width: int, max_lines: int | None = None) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if text_bbox_width(font, trial) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
            if max_lines and len(lines) >= max_lines:
                break
    if not max_lines or len(lines) < max_lines:
        lines.append(current)
    return lines[:max_lines] if max_lines else lines


def draw_text_with_shadow(draw, position, text: str, font, fill, shadow=(0, 0, 0, 160), offset=(2, 2)):
    x, y = position
    ox, oy = offset
    draw.text((x + ox, y + oy), text, font=font, fill=shadow)
    draw.text((x, y), text, font=font, fill=fill)


def draw_token_line(draw, x: int, y: int, text: str, font, max_width: int, default_fill=(245, 247, 250), line_gap=10):
    cursor_x = x
    cursor_y = y
    for raw in text.split():
        token = raw + " "
        key = raw.strip(".,!?():;[]{}\"'")
        fill = PLAYER_COLORS.get(key, default_fill)
        token_width = text_bbox_width(font, token)
        token_height = font.size + 6
        if cursor_x + token_width > x + max_width:
            cursor_y += token_height + line_gap
            cursor_x = x
        if key in PLAYER_COLORS:
            badge = (*fill, 54)
            rounded_box = [cursor_x - 6, cursor_y - 4, cursor_x + token_width + 4, cursor_y + token_height]
            draw.rounded_rectangle(rounded_box, radius=10, fill=badge, outline=fill, width=1)
        draw_text_with_shadow(draw, (cursor_x, cursor_y), token, font, fill)
        cursor_x += token_width
    return cursor_y


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def prepare_background(path: str, blur_radius: int) -> Image.Image:
    image = Image.open(path).convert("RGB")
    aspect = image.width / max(image.height, 1)
    target = W / H
    if aspect > target:
        new_height = H
        new_width = int(new_height * aspect)
    else:
        new_width = W
        new_height = int(new_width / max(aspect, 0.01))
    image = image.resize((new_width, new_height), Image.LANCZOS)
    left = max(0, (new_width - W) // 2)
    top = max(0, (new_height - H) // 2)
    cropped = image.crop((left, top, left + W, top + H))
    blurred = cropped.filter(ImageFilter.GaussianBlur(blur_radius))
    return Image.blend(blurred, Image.new("RGB", (W, H), (4, 8, 14)), 0.42)


def prepare_focus_image(path: str, layout: str) -> Image.Image:
    image = Image.open(path).convert("RGB")
    max_w = int(W * 0.92)
    max_h = int(H * (0.74 if layout == "hook" else 0.66))
    image.thumbnail((max_w, max_h), Image.LANCZOS)
    return image


def build_overlay(scene: SceneSpec, stats: dict, match_id: str, map_name: str, script_chunk: str) -> np.ndarray:
    accent = ACCENTS.get(scene.key, (255, 190, 0))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vg_draw = ImageDraw.Draw(vignette)
    for i in range(H):
        alpha = int(110 * (i / H) ** 1.8)
        vg_draw.line([(0, i), (W, i)], fill=(4, 6, 10, alpha))
    for i in range(260):
        alpha = int(200 * (1 - i / 260) ** 2.0)
        vg_draw.line([(0, i), (W, i)], fill=(6, 8, 14, alpha))
    for i in range(200):
        alpha = int(70 * (1 - i / 200) ** 2.2)
        vg_draw.line([(i, 0), (i, H)], fill=(0, 0, 0, alpha))
        vg_draw.line([(W - i, 0), (W - i, H)], fill=(0, 0, 0, alpha))
    overlay = Image.alpha_composite(overlay, vignette)
    draw = ImageDraw.Draw(overlay)

    draw.rectangle([(0, 0), (W, 8)], fill=accent)
    rounded(draw, [22, 22, W - 22, 102], 22, (8, 12, 20, 126), outline=accent, width=2)

    title_font = fit_font_size(scene.title, FONT_BOLD, 40, W - 80, 24)
    subtitle_font = fit_font_size(scene.subtitle, FONT_REG, 20, W - 96, 14)
    tiny_font = load_font(FONT_BOLD, 14)
    draw_text_with_shadow(draw, (36, 34), "CS2 DATA LAB", tiny_font, accent)
    draw_text_with_shadow(draw, (36, 56), scene.title, title_font, (250, 252, 255))
    draw_text_with_shadow(draw, (W - 36 - text_bbox_width(tiny_font, map_name.upper()), 36), map_name.upper(), tiny_font, (190, 196, 208))

    if scene.layout == "hook":
        rounded(draw, [28, 130, W - 28, 278], 26, (8, 12, 20, 170))
        hook_big = load_font(FONT_BOLD, 28)
        stat_font = load_font(FONT_BOLD, 22)
        draw_text_with_shadow(draw, (46, 150), scene.subtitle, hook_big, (245, 247, 250))
        draw_text_with_shadow(
            draw,
            (46, 206),
            f"{stats['rounds']} rounds  •  {stats['mongolz_kills']} vs {stats['mouz_kills']} kills",
            stat_font,
            accent,
        )
        rounded(draw, [28, H - 222, W - 28, H - 76], 26, (8, 12, 20, 196))
        draw_text_with_shadow(draw, (46, H - 204), "WHY IT MATTERS", tiny_font, (112, 214, 255))
        draw_token_line(
            draw,
            46,
            H - 174,
            f"{stats['first_kill']} эхний kill-ийг нээж, {stats['top_fragger']} хамгийн их frag авсан.",
            load_font(FONT_BOLD, 24),
            W - 92,
        )
    else:
        panel_y = H - (240 if scene.layout == "split" else 220)
        rounded(draw, [26, panel_y, W - 26, H - 72], 24, (8, 12, 20, 208))
        draw_text_with_shadow(draw, (44, panel_y + 18), scene.subtitle.upper(), tiny_font, accent)
        body_font = load_font(FONT_BOLD, 22 if len(script_chunk) < 140 else 20)
        lines = wrap_text(script_chunk, body_font, W - 92, max_lines=3)
        line_y = panel_y + 46
        for idx, line in enumerate(lines):
            fill = (255, 224, 146) if idx == 0 else (245, 247, 250)
            draw_token_line(draw, 44, line_y, line, body_font, W - 92, default_fill=fill, line_gap=6)
            line_y += body_font.size + 12
        if scene.layout == "split":
            rounded(draw, [28, 126, 332, 220], 22, (8, 12, 20, 196))
            draw_text_with_shadow(draw, (46, 146), "MATCH SNAPSHOT", tiny_font, accent)
            draw_text_with_shadow(draw, (46, 172), f"{stats['mongolz_kills']} : {stats['mouz_kills']} kills", load_font(FONT_BOLD, 24), (245, 247, 250))
            draw_token_line(
                draw,
                46,
                204,
                f"{stats['top_fragger']} top frag ({stats['top_kills']})",
                load_font(FONT_BOLD, 16),
                260,
                default_fill=(170, 176, 190),
                line_gap=4,
            )

    draw_text_with_shadow(draw, (28, H - 46), match_id.replace("_", " ").upper(), tiny_font, accent)
    draw_text_with_shadow(draw, (W - 122, H - 46), "CS2 SHORTS", tiny_font, accent)
    return np.array(overlay)


def focus_position(scene: SceneSpec, progress: float, focus_size: tuple[int, int]) -> tuple[float, float]:
    fw, fh = focus_size
    if scene.layout == "hook":
        base_x = (W - fw) / 2
        base_y = H * 0.31
    elif scene.layout == "split":
        base_x = (W - fw) / 2
        base_y = H * 0.30
    else:
        base_x = (W - fw) / 2
        base_y = H * 0.18
    drift_x, drift_y = scene.motion
    return (base_x + progress * drift_x * W, base_y + progress * drift_y * H)


def build_scene_clip(scene: SceneSpec, script_chunk: str, stats: dict, match_id: str, map_name: str, duration: float) -> CompositeVideoClip:
    background = prepare_background(scene.image, scene.blur)
    focus_image = prepare_focus_image(scene.image, scene.layout)
    overlay = build_overlay(scene, stats, match_id, map_name, script_chunk)

    bg_clip = ImageClip(np.array(background)).set_duration(duration)
    focus_clip = ImageClip(np.array(focus_image)).set_duration(duration)
    focus_clip = focus_clip.resize(lambda t: 1.0 + 0.05 * (t / max(duration, 0.01)))
    focus_clip = focus_clip.set_position(lambda t: focus_position(scene, t / max(duration, 0.01), focus_image.size))
    overlay_clip = ImageClip(overlay, transparent=True).set_duration(duration)

    clip = CompositeVideoClip([bg_clip, focus_clip, overlay_clip], size=(W, H)).set_duration(duration)
    return clip


def split_chunks_by_weight(lines: list[str], count: int) -> list[str]:
    if count <= 1:
        return [" ".join(lines)]
    if len(lines) <= count:
        return lines
    chunks = []
    total_chars = sum(len(line) for line in lines)
    target_chars = max(1, total_chars / count)
    bucket = []
    bucket_chars = 0
    for line in lines:
        bucket.append(line)
        bucket_chars += len(line)
        if bucket_chars >= target_chars and len(chunks) < count - 1:
            chunks.append(" ".join(bucket))
            bucket = []
            bucket_chars = 0
    if bucket:
        chunks.append(" ".join(bucket))
    return chunks


def allocate_durations(chunks: list[str], total_duration: float, min_duration: float = 4.2) -> list[float]:
    weights = []
    for chunk in chunks:
        weight = len(chunk) + chunk.count(",") * 12 + chunk.count(".") * 18 + chunk.count("?") * 20 + chunk.count("!") * 20
        weights.append(max(36, weight))
    remaining = max(total_duration - min_duration * len(chunks), 0.0)
    weight_sum = sum(weights) or 1
    return [min_duration + remaining * (weight / weight_sum) for weight in weights]


def build_audio_mix(voice_clip, scene_starts: list[float]) -> CompositeAudioClip:
    duration = voice_clip.duration
    fps = 22050
    t = np.linspace(0, duration, max(1, int(duration * fps)), endpoint=False)

    bed = (
        0.012 * np.sin(2 * np.pi * 120 * t)
        + 0.007 * np.sin(2 * np.pi * 240 * t)
        + 0.004 * np.sin(2 * np.pi * 360 * t)
    ).astype(np.float32)
    bed *= np.linspace(0.65, 0.92, len(t), dtype=np.float32)

    swoosh = np.zeros_like(t, dtype=np.float32)
    for start in scene_starts[1:]:
        mask = (t >= start) & (t < start + 0.18)
        local = t[mask] - start
        swoosh[mask] += 0.025 * np.sin(2 * np.pi * (220 + 1100 * local) * local) * np.exp(-12 * local)

    hit = np.zeros_like(t, dtype=np.float32)
    for start in scene_starts:
        mask = (t >= start + 0.12) & (t < start + 0.22)
        local = t[mask] - (start + 0.12)
        hit[mask] += 0.014 * np.sin(2 * np.pi * 420 * local) * np.exp(-26 * local)

    voice_base = voice_clip.set_fps(fps) if hasattr(voice_clip, "set_fps") else voice_clip
    layers = [voice_base]
    for channel in (bed, swoosh, hit):
        stereo = np.column_stack([channel, channel])
        layers.append(AudioArrayClip(stereo, fps=fps).set_duration(duration))
    return CompositeAudioClip(layers)


def attach_audio(video, voice_clip, scene_starts: list[float]):
    try:
        voice_primary = voice_clip.set_fps(44100) if hasattr(voice_clip, "set_fps") else voice_clip
        primary_video = video.set_audio(voice_primary)
        print("Audio attach mode: primary voice only")
        return primary_video
    except Exception as exc:
        print(f"Warning: primary voice attach failed: {exc}")

    try:
        mixed_audio = build_audio_mix(voice_clip, scene_starts)
        print("Audio attach mode: composite mix fallback")
        return video.set_audio(mixed_audio)
    except Exception as exc:
        print(f"Warning: composite audio mix failed: {exc}")

    print("Warning: no valid audio track attached; rendering silent video.")
    return video


def write_video(video, output_video: str):
    threads = max(2, min(8, (os.cpu_count() or 4)))
    try:
        video.write_videofile(
            output_video,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=threads,
            logger=None,
        )
    except Exception as exc:
        print(f"Warning: render with audio_codec='aac' failed: {exc}")
        print("Retrying render with audio_codec='libmp3lame'")
        video.write_videofile(
            output_video,
            fps=FPS,
            codec="libx264",
            audio_codec="libmp3lame",
            preset="ultrafast",
            threads=threads,
            logger=None,
        )


def main():
    if len(sys.argv) != 6:
        print("Usage: create_shorts_cli.py <script_file> <json_path> <heatmap_img> <awp_img> <output_video>")
        sys.exit(1)

    script_file, json_path, heatmap_img, awp_img, output_video = sys.argv[1:6]
    try:
        with open(script_file, "r", encoding="utf-8") as handle:
            script_text = clip_script(handle.read())
    except Exception as exc:
        print(f"Script файл уншихад алдаа гарлаа: {exc}")
        sys.exit(1)

    try:
        data = safe_json_load(json_path)
    except RuntimeError as exc:
        print(str(exc))
        sys.exit(1)

    match_id = data.get("match_id", "match")
    map_name = data.get("map", "de_mirage")
    stats = analyze_match(data)
    assets = find_assets(match_id, map_name, heatmap_img, awp_img)
    scenes = build_scenes(assets, stats)
    if not scenes:
        scenes = [SceneSpec("hook", "MATCH BREAKDOWN", "Гол мөчүүдийг харцгаая.", heatmap_img, "hook", (0.18, 0.18), 14, (0.03, 0.02))]

    voice = load_voice_clip(script_text)
    if voice.duration > 55:
        voice = voice.subclip(0, 55)
    target_duration = max(32.0, min(52.0, voice.duration))
    if voice.duration > target_duration:
        voice = voice.subclip(0, target_duration)

    sentences = split_sentences(script_text)
    chunks = split_chunks_by_weight(sentences, len(scenes))
    durations = allocate_durations(chunks, voice.duration)
    scene_starts = []
    current = 0.0
    clips = []
    for scene, chunk, duration in zip(scenes, chunks, durations):
        scene_starts.append(current)
        clip = build_scene_clip(scene, chunk, stats, match_id, map_name, duration)
        clip = clip.fx(fadein, 0.18).fx(fadeout, 0.18)
        clips.append(clip)
        current += duration

    video = concatenate_videoclips(clips, method="compose")
    video = attach_audio(video, voice, scene_starts)

    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    try:
        write_video(video, output_video)
    finally:
        if os.path.exists(VOICE_PATH):
            os.remove(VOICE_PATH)


if __name__ == "__main__":
    main()
