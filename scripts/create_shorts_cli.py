#!/usr/bin/env python3
import asyncio
import json
import os
import re
import sys

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.audio.AudioClip import AudioArrayClip, CompositeAudioClip
from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

W, H = 720, 1280
MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
MOUZ = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
PLAYER_COLORS = {
    "910": (255, 200, 0),
    "Techno4K": (255, 200, 0),
    "bLitz": (255, 200, 0),
    "cobrazera": (255, 200, 0),
    "mzinho": (255, 200, 0),
    "Brollan": (255, 92, 92),
    "Jimpphat": (255, 92, 92),
    "Spinx": (255, 92, 92),
    "torzsi": (255, 92, 92),
    "xertioN": (255, 92, 92),
}


async def generate_voiceover(text, output_path):
    communicate = edge_tts.Communicate(text, "mn-MN-YesuiNeural")
    await communicate.save(output_path)


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def draw_rounded_rect(draw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        trial = f"{current} {word}"
        if font.getbbox(trial)[2] <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def text_width(font, text):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def clean_script_lines(script_text):
    text = re.sub(r"\s+", " ", script_text.strip())[:320]
    parts = re.split(r"(?<=[.!?])\s+", text)
    lines = [part.strip() for part in parts if part.strip()]
    if not lines:
        return [text] if text else ["CS2-ийн энэ тоглолт дээр юу болсон бэ?"]
    return lines


def chunk_lines(lines, target_chunks):
    if len(lines) <= target_chunks:
        return lines
    chunks = []
    size = max(1, len(lines) // target_chunks)
    current = []
    for line in lines:
        current.append(line)
        if len(current) >= size and len(chunks) < target_chunks - 1:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def limit_script_for_shorts(script_text):
    text = re.sub(r"\s+", " ", script_text.strip())
    if len(text) <= 520:
        return text
    truncated = text[:520]
    last_stop = max(truncated.rfind("."), truncated.rfind("!"), truncated.rfind("?"))
    if last_stop > 180:
        return truncated[: last_stop + 1]
    return truncated.rstrip() + "..."


def get_kills(jdata):
    raw = jdata.get("kills", [])
    if raw and isinstance(raw[0], list) and len(raw[0]) > 1:
        return raw[0][1]
    return raw


def count_team_kills(kills):
    mongolz_kills = 0
    mouz_kills = 0
    for kill in kills:
        if not isinstance(kill, dict):
            continue
        attacker = kill.get("attacker_name", "")
        if attacker in MONGOLZ:
            mongolz_kills += 1
        elif attacker in MOUZ:
            mouz_kills += 1
    return mongolz_kills, mouz_kills


def extract_rounds(kills):
    ordered = sorted(
        [kill for kill in kills if isinstance(kill, dict)],
        key=lambda item: item.get("tick", 0),
    )
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


def build_match_stats(jdata):
    kills = get_kills(jdata)
    mongolz_kills, mouz_kills = count_team_kills(kills)
    rounds = extract_rounds(kills)
    total_rounds = len(rounds)
    first_kill = rounds[0][0].get("attacker_name", "Unknown") if rounds else "Unknown"

    economy_raw = jdata.get("economy", [])
    economy_rows = []
    for item in economy_raw:
        if isinstance(item, list) and len(item) == 2 and isinstance(item[1], list):
            economy_rows.extend(item[1])

    max_equip = 0
    for row in economy_rows:
        equip = row.get("user_current_equip_value", 0) or row.get("current_equip_value", 0) or 0
        max_equip = max(max_equip, int(equip))

    return {
        "mongolz_kills": mongolz_kills,
        "mouz_kills": mouz_kills,
        "total_rounds": total_rounds,
        "first_kill": first_kill,
        "max_equip": max_equip,
    }


def collect_highlights(jdata, stats):
    kills = [k for k in get_kills(jdata) if isinstance(k, dict)]
    top_fragger = "Unknown"
    top_kills = 0
    scoreboard = {}
    for kill in kills:
        attacker = kill.get("attacker_name", "")
        if not attacker:
            continue
        scoreboard[attacker] = scoreboard.get(attacker, 0) + 1
        if scoreboard[attacker] > top_kills:
            top_fragger = attacker
            top_kills = scoreboard[attacker]
    return {
        "first_kill": stats["first_kill"],
        "top_fragger": top_fragger,
        "top_kills": top_kills,
    }


def find_visuals(json_path, match_id, map_name, heatmap_img, awp_img):
    visuals_dir = os.path.dirname(heatmap_img) or "/data/visuals"
    candidates = {
        "hook": heatmap_img,
        "heatmap": heatmap_img,
        "firstkill": f"{visuals_dir}/{match_id}_{map_name}_firstkill.png",
        "deathmap": f"{visuals_dir}/{match_id}_{map_name}_deathmap.png",
        "tactics": f"{visuals_dir}/{match_id}_{map_name}_tactics.png",
        "economy": f"{visuals_dir}/{match_id}_{map_name}_economy.png",
        "utility": f"{visuals_dir}/{match_id}_{map_name}_utility.png",
        "awp": awp_img,
        "clutch": f"{visuals_dir}/{match_id}_{map_name}_clutch_round_45.png",
        "round": f"{visuals_dir}/{match_id}_{map_name}_round_26.png",
    }
    available = {}
    for key, path in candidates.items():
        if path and os.path.exists(path):
            available[key] = path

    if not available:
        available["hook"] = heatmap_img
    return available


def scene_catalog(available, stats):
    base = [
        ("hook", "ЭНЭ ТОГЛОЛТЫН ХЭМНЭЛ", "Яг хаанаас тоглолт эргэсэн бэ?"),
        ("heatmap", "KILL HEATMAP", "Хамгийн халуун бүсүүд"),
        ("firstkill", "FIRST KILL", f"Эхний цохилтыг {stats['first_kill']} нээсэн"),
        ("deathmap", "DEATH MAP", "Хаана их уналт болсон"),
        ("tactics", "TACTICAL FLOW", "Map control ба rotation"),
        ("economy", "ECONOMY SWING", "Мөнгөний давуу тал хэрхэн шилжсэн"),
        ("utility", "UTILITY PRESSURE", "Flash, smoke, molotov шахалт"),
        ("awp", "AWP CONTROL", "Снайпер хяналтын бүсүүд"),
        ("round", "KEY ROUND", "Momentum эргэсэн мөч"),
        ("clutch", "CLUTCH MOMENT", "Тоглолтын даралттай төгсгөл"),
    ]
    scenes = []
    for key, title, subtitle in base:
        if key in available:
            scenes.append({"key": key, "title": title, "subtitle": subtitle, "image": available[key]})
    return scenes[:7] if len(scenes) > 7 else scenes


def scene_transition_label(scene_key):
    labels = {
        "hook": "HOOK",
        "heatmap": "HOT ZONE",
        "firstkill": "ENTRY",
        "deathmap": "TRADE MAP",
        "tactics": "ROTATION",
        "economy": "ECON",
        "utility": "UTILITY",
        "awp": "AWP LINE",
        "round": "KEY ROUND",
        "clutch": "CLUTCH",
    }
    return labels.get(scene_key, "CUT")


def background_frame(path, zoom, drift_x, drift_y):
    base = Image.new("RGB", (W, H), (10, 12, 18))
    if not path or not os.path.exists(path):
        return base

    image = Image.open(path).convert("RGB")
    image_ratio = image.width / max(image.height, 1)
    target_ratio = W / H

    if image_ratio > target_ratio:
        new_height = H
        new_width = int(new_height * image_ratio)
    else:
        new_width = W
        new_height = int(new_width / max(image_ratio, 0.01))

    scale = max(1.0, zoom)
    new_width = int(new_width * scale)
    new_height = int(new_height * scale)
    image = image.resize((new_width, new_height), Image.LANCZOS)

    max_x = max(0, new_width - W)
    max_y = max(0, new_height - H)
    left = int(max_x * drift_x)
    top = int(max_y * drift_y)
    crop = image.crop((left, top, left + W, top + H))
    base.paste(crop, (0, 0))
    return base


def draw_overlay(image, progress):
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for i in range(H):
        alpha = int(150 * min(1.0, (i / H) ** 1.4))
        draw.line([(0, i), (W, i)], fill=(4, 6, 12, alpha))
    for i in range(360):
        alpha = int(210 * (1 - i / 360) ** 1.8)
        draw.line([(0, i), (W, i)], fill=(8, 10, 16, alpha))

    accent_x = int(W * (0.15 + 0.7 * progress))
    draw.rectangle([(accent_x, 88), (min(W, accent_x + 160), 96)], fill=(255, 188, 0, 230))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def draw_transition_overlay(draw, scene_key, progress):
    pulse = int(130 + 60 * np.sin(progress * np.pi))
    color = (255, 188, 0) if scene_key in {"hook", "heatmap", "economy"} else (80, 210, 255)
    draw.rectangle([(0, 0), (W, 10)], fill=(*color, min(255, pulse)))
    label = scene_transition_label(scene_key)
    font = load_font(FONT_BOLD, 16)
    x2 = W - 20
    x1 = x2 - 126
    y1 = 82
    y2 = y1 + 34
    draw_rounded_rect(draw, [x1, y1, x2, y2], 14, (14, 18, 28), outline=color, width=2)
    draw.text(((x1 + x2) / 2, y1 + 7), label, font=font, fill=color, anchor="ma")


def draw_header(draw, map_name, scene_title, section_index, total_sections):
    font_logo = load_font(FONT_BOLD, 20)
    font_tag = load_font(FONT_BOLD, 16)
    draw.rectangle([(0, 0), (W, 64)], fill=(8, 10, 16))
    draw.text((24, 18), "CS2 DATA LAB", font=font_logo, fill=(255, 196, 0))
    draw.text((W - 24, 20), map_name.upper(), font=font_tag, fill=(170, 176, 190), anchor="ra")
    draw.text((24, 92), scene_title, font=load_font(FONT_BOLD, 38), fill=(245, 247, 250))
    draw.text(
        (24, 136),
        f"{section_index}/{total_sections} ANALYSIS CUT",
        font=load_font(FONT_BOLD, 16),
        fill=(255, 196, 0),
    )


def draw_stats(draw, stats, progress):
    font_small = load_font(FONT_REGULAR, 16)
    font_stat = load_font(FONT_BOLD, 24)
    x1 = 24
    x2 = W - 24
    y = 170
    draw_rounded_rect(draw, [x1, y, x2, y + 88], 20, (12, 14, 24, 210), outline=(40, 46, 60), width=2)
    metrics = [
        ("MONGOLZ", stats["mongolz_kills"], (255, 200, 0)),
        ("MOUZ", stats["mouz_kills"], (255, 92, 92)),
        ("ROUNDS", stats["total_rounds"], (112, 214, 255)),
    ]
    width = x2 - x1
    x_positions = [x1 + width * 0.17, x1 + width * 0.5, x1 + width * 0.83]
    for (label, value, color), x in zip(metrics, x_positions):
        draw.text((x, y + 20), label, font=font_small, fill=color, anchor="mm")
        draw.text((x, y + 56), str(value), font=font_stat, fill=(245, 247, 250), anchor="mm")

    bar_y = y + 78
    draw.rectangle([(x1 + 16, bar_y), (x2 - 16, bar_y + 4)], fill=(34, 38, 52))
    draw.rectangle([(x1 + 16, bar_y), (x1 + 16 + int((x2 - x1 - 32) * progress), bar_y + 4)], fill=(255, 196, 0))


def draw_scene_subtitle(draw, subtitle, body_text, progress):
    title_font = load_font(FONT_BOLD, 18)
    body_font = load_font(FONT_BOLD, 24)
    label_font = load_font(FONT_REGULAR, 14)

    x1 = 24
    x2 = W - 24
    box_y = H - 250
    box_h = 180
    draw_rounded_rect(draw, [x1, box_y, x2, box_y + box_h], 22, (12, 16, 24, 214), outline=(50, 56, 70), width=2)
    draw.text((x1 + 18, box_y + 16), subtitle.upper(), font=label_font, fill=(255, 196, 0))

    lines = wrap_text(body_text, body_font, x2 - x1 - 36)
    lines = lines[:3]
    y = box_y + 42
    active_idx = min(len(lines) - 1, int(progress * max(1, len(lines)))) if lines else 0
    for idx, line in enumerate(lines):
        fill = (255, 216, 120) if idx == active_idx else (245, 247, 250)
        if idx == active_idx:
            draw_rounded_rect(draw, [x1 + 10, y - 5, x2 - 10, y + 32], 12, (255, 188, 0, 28))
        draw.text((x1 + 18, y), line, font=body_font, fill=fill)
        y += 34

    glow_width = int((x2 - x1 - 36) * progress)
    draw.rectangle([(x1 + 18, box_y + box_h - 18), (x1 + 18 + glow_width, box_y + box_h - 12)], fill=(255, 196, 0))
    draw.text((x1 + 18, box_y + box_h - 38), "DATA-DRIVEN SHORTS", font=title_font, fill=(150, 156, 170))


def draw_highlighted_text(draw, x, y, text, font, default_fill, max_width):
    tokens = text.split()
    cx = x
    for token in tokens:
        raw = token.strip()
        key = raw.strip(".,!?():;[]{}\"'")
        fill = PLAYER_COLORS.get(key, default_fill)
        token_text = f"{raw} "
        token_w = text_width(font, token_text)
        if cx + token_w > x + max_width:
            y += 48
            cx = x
        if key in PLAYER_COLORS:
            draw_rounded_rect(draw, [cx - 6, y - 6, cx + token_w, y + 38], 12, (*fill, 45))
        draw.text((cx, y), token_text, font=font, fill=fill)
        cx += token_w
    return y


def draw_player_highlights(draw, highlights, progress):
    font_title = load_font(FONT_BOLD, 14)
    font_body = load_font(FONT_BOLD, 16)
    x1, y1, x2, y2 = 24, 300, int(W * 0.52), 386
    draw_rounded_rect(draw, [x1, y1, x2, y2], 24, (12, 16, 24, 216), outline=(48, 56, 70), width=2)
    draw.text((x1 + 24, y1 + 18), "PLAYER FOCUS", font=font_title, fill=(112, 214, 255))
    pulse = 8 * np.sin(progress * np.pi * 2)
    line_y = draw_highlighted_text(
        draw,
        x1 + 24,
        int(y1 + 54 + pulse),
        f"Entry: {highlights['first_kill']}",
        font_body,
        (245, 247, 250),
        x2 - x1 - 24,
    )
    draw_highlighted_text(
        draw,
        x1 + 24,
        line_y + 18,
        f"Top frag: {highlights['top_fragger']} ({highlights['top_kills']})",
        font_body,
        (245, 247, 250),
        x2 - x1 - 24,
    )


def draw_footer(draw):
    footer_font = load_font(FONT_BOLD, 14)
    draw.text((W // 2, H - 18), "LIKE • COMMENT • SUBSCRIBE", font=footer_font, fill=(255, 196, 0), anchor="mm")


def make_scene_frame(scene, script_chunk, stats, highlights, match_id, map_name, scene_index, total_scenes, progress):
    zoom = 1.08 + 0.06 * progress
    drift_x = min(1.0, 0.18 + 0.10 * scene_index + progress * 0.18)
    drift_y = min(1.0, 0.10 + (scene_index % 3) * 0.14 + progress * 0.08)
    frame = background_frame(scene["image"], zoom, drift_x, drift_y)
    frame = draw_overlay(frame, progress)
    draw = ImageDraw.Draw(frame)

    draw_header(draw, map_name, scene["title"], scene_index + 1, total_scenes)
    draw_transition_overlay(draw, scene["key"], progress)
    draw_stats(draw, stats, progress)

    badge_font = load_font(FONT_BOLD, 16)
    draw_rounded_rect(draw, [24, 270, W - 180, 316], 16, (20, 24, 32, 225), outline=(48, 56, 72), width=2)
    draw.text((40, 286), match_id.replace("_", " ").upper(), font=badge_font, fill=(220, 224, 232))
    draw.text((40, 304), scene["subtitle"], font=load_font(FONT_REGULAR, 13), fill=(150, 156, 170))

    panel_y = 410
    panel_x1 = 24
    panel_x2 = W - 24
    panel_h = 380
    draw_rounded_rect(draw, [panel_x1, panel_y, panel_x2, panel_y + panel_h], 20, (255, 255, 255, 18))
    mini = background_frame(scene["image"], 1.02 + progress * 0.08, 0.35, 0.25).resize((panel_x2 - panel_x1 - 24, panel_h - 24), Image.LANCZOS)
    frame.paste(mini, (panel_x1 + 12, panel_y + 12))
    frame = draw_overlay(frame, progress * 0.4)
    draw = ImageDraw.Draw(frame)
    draw.rectangle([(panel_x1 + 12, panel_y + 12), (panel_x2 - 12, panel_y + panel_h - 12)], outline=(255, 196, 0), width=2)

    pulse_radius = 22 + int(10 * abs(np.sin(progress * np.pi * 3)))
    pulse_x = int(W * 0.78) - (scene_index % 2) * 44
    pulse_y = int(H * 0.46) + (scene_index % 3) * 52
    draw.ellipse(
        [(pulse_x - pulse_radius, pulse_y - pulse_radius), (pulse_x + pulse_radius, pulse_y + pulse_radius)],
        outline=(255, 196, 0),
        width=3,
    )
    draw.ellipse(
        [(pulse_x - 8, pulse_y - 8), (pulse_x + 8, pulse_y + 8)],
        fill=(255, 196, 0),
    )

    draw_player_highlights(draw, highlights, progress)
    draw_scene_subtitle(draw, scene["subtitle"], script_chunk, progress)
    draw_footer(draw)
    return np.array(frame)


def allocate_durations(audio_duration, scene_count):
    if scene_count <= 0:
        return []
    base = audio_duration / scene_count
    durations = []
    for idx in range(scene_count):
        weight = 1.18 if idx == 0 else (0.88 if idx == scene_count - 1 else 1.0)
        durations.append(base * weight)
    total = sum(durations) or 1.0
    scale = audio_duration / total
    return [duration * scale for duration in durations]


def build_scene_clips(scenes, script_chunks, stats, highlights, match_id, map_name, audio_duration):
    durations = allocate_durations(audio_duration, len(scenes))
    clips = []
    for index, scene in enumerate(scenes):
        script_chunk = script_chunks[min(index, len(script_chunks) - 1)]
        duration = max(2.6, durations[index])
        frame = make_scene_frame(
            scene,
            script_chunk,
            stats,
            highlights,
            match_id,
            map_name,
            index,
            len(scenes),
            0.55 if index else 0.35,
        )
        clip = ImageClip(frame).set_duration(duration)
        if index > 0:
            clip = clip.fx(fadein, 0.25)
        if index < len(scenes) - 1:
            clip = clip.fx(fadeout, 0.25)
        clips.append(clip)
    return clips


def build_audio_layers(voice_clip):
    layers = [voice_clip]
    duration = voice_clip.duration
    fps = 22050
    t = np.linspace(0, duration, int(duration * fps), endpoint=False)

    bed = 0.02 * np.sin(2 * np.pi * 110 * t) + 0.01 * np.sin(2 * np.pi * 220 * t)
    envelope = np.linspace(0.35, 0.9, len(t))
    bed = (bed * envelope).astype(np.float32)
    bed_stereo = np.column_stack([bed, bed])
    layers.append(AudioArrayClip(bed_stereo, fps=fps).set_duration(duration))

    hit = np.zeros_like(t, dtype=np.float32)
    hit_points = np.linspace(0.4, max(0.5, duration - 0.6), 5)
    for point in hit_points:
        mask = (t >= point) & (t < point + 0.09)
        hit[mask] += 0.045 * np.sin(2 * np.pi * 880 * (t[mask] - point)) * np.exp(-28 * (t[mask] - point))
    hit_stereo = np.column_stack([hit, hit])
    layers.append(AudioArrayClip(hit_stereo, fps=fps).set_duration(duration))
    return CompositeAudioClip(layers)


def main():
    if len(sys.argv) != 6:
        sys.exit(1)

    script_file = sys.argv[1]
    json_path = sys.argv[2]
    heatmap_img = sys.argv[3]
    awp_img = sys.argv[4]
    output_video = sys.argv[5]

    with open(script_file, "r", encoding="utf-8") as handle:
        script_text = limit_script_for_shorts(handle.read().strip())

    with open(json_path, "r", encoding="utf-8") as handle:
        jdata = json.load(handle)

    match_id = jdata.get("match_id", "match")
    map_name = jdata.get("map", "de_mirage")
    stats = build_match_stats(jdata)
    highlights = collect_highlights(jdata, stats)
    visuals = find_visuals(json_path, match_id, map_name, heatmap_img, awp_img)
    scenes = scene_catalog(visuals, stats)
    if not scenes:
        scenes = [{"key": "hook", "title": "MATCH BREAKDOWN", "subtitle": "Гол мөчүүд", "image": heatmap_img}]

    temp_audio = "/data/videos/temp_voice.mp3"
    if os.path.exists(temp_audio):
        os.remove(temp_audio)

    print("Generating voiceover...")
    asyncio.run(generate_voiceover(script_text, temp_audio))

    audio = AudioFileClip(temp_audio)
    max_duration = 40
    if audio.duration > max_duration:
        audio = audio.subclip(0, max_duration)
    print(f"Audio duration: {audio.duration:.1f}s")

    script_chunks = chunk_lines(clean_script_lines(script_text), len(scenes))
    clips = build_scene_clips(scenes, script_chunks, stats, highlights, match_id, map_name, audio.duration)
    final_audio = build_audio_layers(audio)
    video = concatenate_videoclips(clips, method="compose").set_audio(final_audio)

    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    print("Rendering upgraded shorts...")
    video.write_videofile(
        output_video,
        fps=20,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        logger=None,
    )

    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    print("Done!")


if __name__ == "__main__":
    main()
