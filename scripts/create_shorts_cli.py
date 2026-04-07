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
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
MOUZ = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}
PLAYER_COLORS = {name: (255, 205, 0) for name in MONGOLZ} | {name: (255, 90, 90) for name in MOUZ}


async def generate_voiceover(text, output_path):
    communicate = edge_tts.Communicate(text, "mn-MN-YesuiNeural")
    await communicate.save(output_path)


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def wrap_text(text, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    for word in words[1:]:
        test = f"{cur} {word}"
        if font.getbbox(test)[2] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def clean_script(text):
    text = re.sub(r"\s+", " ", text.strip())
    text = text[:650]
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if not parts:
        return ["CS2 тоглолтын гол мөчүүдийг харцгаая."]
    return parts


def clip_script(text):
    text = re.sub(r"\s+", " ", text.strip())
    if len(text) <= 650:
        return text
    cut = text[:650]
    last = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"))
    return cut[: last + 1] if last > 180 else cut + "..."


def split_chunks(lines, target):
    if len(lines) <= target:
        return lines
    out = []
    size = max(1, round(len(lines) / target))
    buf = []
    for line in lines:
        buf.append(line)
        if len(buf) >= size and len(out) < target - 1:
            out.append(" ".join(buf))
            buf = []
    if buf:
        out.append(" ".join(buf))
    return out


def get_kills(data):
    raw = data.get("kills", [])
    return raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw


def extract_rounds(kills):
    ordered = sorted([k for k in kills if isinstance(k, dict)], key=lambda k: k.get("tick", 0))
    if not ordered:
        return []
    rounds = []
    cur = [ordered[0]]
    for kill in ordered[1:]:
        if kill.get("tick", 0) - cur[-1].get("tick", 0) > 1000:
            rounds.append(cur)
            cur = [kill]
        else:
            cur.append(kill)
    rounds.append(cur)
    return rounds


def analyze(data):
    kills = get_kills(data)
    rounds = extract_rounds(kills)
    score = {}
    mk = mz = 0
    for kill in kills:
        if not isinstance(kill, dict):
            continue
        name = kill.get("attacker_name", "")
        score[name] = score.get(name, 0) + 1
        if name in MONGOLZ:
            mk += 1
        elif name in MOUZ:
            mz += 1
    top_fragger = max(score, key=score.get) if score else "Unknown"
    first = rounds[0][0].get("attacker_name", "Unknown") if rounds else "Unknown"
    return {
        "mongolz_kills": mk,
        "mouz_kills": mz,
        "rounds": len(rounds),
        "first_kill": first,
        "top_fragger": top_fragger,
        "top_kills": score.get(top_fragger, 0),
    }


def find_assets(match_id, map_name, heatmap_img, awp_img):
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
    return {k: v for k, v in assets.items() if v and os.path.exists(v)}


def build_scenes(assets, stats):
    base = [
        ("hook", "MOUZ VS MONGOLZ", "Mirage дээр momentum хаана эргэсэн бэ?"),
        ("heatmap", "HEATMAP", "Хамгийн халуун тулаан mid дээр төвлөрсөн."),
        ("firstkill", "FIRST KILL", f"{stats['first_kill']} эхний цохилтыг нээсэн."),
        ("deathmap", "DEATH MAP", "Trade pattern ба уналтын бүсүүд."),
        ("economy", "ECONOMY", "Мөнгөний давуу тал tempo-г шийдсэн."),
        ("utility", "UTILITY", "Flash ба smoke pressure map control-ийг нээсэн."),
        ("awp", "AWP LINES", "Снайперын хяналт choke point-уудыг түгжсэн."),
        ("round", "KEY ROUND", "Momentum shift-ийг round map дээр харуулъя."),
        ("clutch", "CLUTCH", f"{stats['top_fragger']} даралттай мөчийг хаасан."),
    ]
    scenes = [{"key": k, "title": t, "subtitle": s, "image": assets[k]} for k, t, s in base if k in assets]
    return scenes[:6] if len(scenes) > 6 else scenes


def bg_image(path, zoom=1.0, focus_x=0.5, focus_y=0.5, mode="cover"):
    from PIL import ImageFilter
    if not path or not os.path.exists(path):
        return Image.new("RGB", (W, H), (8, 12, 18))
    src = Image.open(path).convert("RGB")
    aspect = src.width / max(src.height, 1)
    target = W / H
    if mode == "fit":
        if aspect > target:
            ch, cw = H, int(H * aspect)
        else:
            cw, ch = W, int(W / max(aspect, 0.01))
        bg = src.resize((cw, ch), Image.LANCZOS)
        bg = bg.crop(((cw - W) // 2, (ch - H) // 2, (cw + W) // 2, (ch + H) // 2))
        img = Image.blend(bg.filter(ImageFilter.GaussianBlur(30)), Image.new("RGB", (W, H), (0, 0, 0)), 0.6)
        
        if aspect > target:
            nw = W
            nh = int(nw / max(aspect, 0.01))
        else:
            nh = H
            nw = int(nh * aspect)
        nw = int(nw * zoom)
        nh = int(nh * zoom)
        src = src.resize((nw, nh), Image.LANCZOS)
        x = (W - nw) // 2
        y = (H - nh) // 2
        img.paste(src, (x, y))
    else:
        if aspect > target:
            nh = H
            nw = int(nh * aspect)
        else:
            nw = W
            nh = int(nw / max(aspect, 0.01))
        nw = int(nw * zoom)
        nh = int(nh * zoom)
        src = src.resize((nw, nh), Image.LANCZOS)
        max_x = max(0, nw - W)
        max_y = max(0, nh - H)
        left = int(max_x * focus_x)
        top = int(max_y * focus_y)
        img = Image.new("RGB", (W, H), (8, 12, 18))
        img.paste(src.crop((left, top, left + W, top + H)), (0, 0))
    return img


def add_overlay(img, strength=1.0):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    for i in range(H):
        a = int(140 * strength * (i / H) ** 2)
        draw.line([(0, i), (W, i)], fill=(6, 8, 14, a))
    for i in range(260):
        a = int(180 * strength * (1 - i / 260) ** 2)
        draw.line([(0, i), (W, i)], fill=(4, 6, 12, a))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


def draw_tokens(draw, x, y, text, font, max_width, default=(245, 247, 250), line_gap=12):
    cx = x
    cy = y
    for raw in text.split():
        key = raw.strip(".,!?():;[]{}\"'")
        fill = PLAYER_COLORS.get(key, default)
        token = raw + " "
        tw = font.getbbox(token)[2]
        if cx + tw > x + max_width:
            cy += font.size + line_gap
            cx = x
        if key in PLAYER_COLORS:
            rounded(draw, [cx - 4, cy - 4, cx + tw + 2, cy + font.size + 2], 8, (*fill, 50), outline=fill, width=1)
        draw.text((cx, cy), token, font=font, fill=fill)
        cx += tw
    return cy


def draw_hook(draw, scene, stats, match_id, map_name):
    title = load_font(FONT_BOLD, 52)
    sub = load_font(FONT_BOLD, 24)
    mini = load_font(FONT_REG, 16)
    draw.text((28, 64), "CS2 DATA LAB", font=mini, fill=(255, 200, 0))
    draw.text((28, 118), scene["title"], font=title, fill=(255, 255, 255))
    draw.text((28, 178), map_name.upper(), font=sub, fill=(255, 200, 0))
    rounded(draw, [28, 250, W - 28, 372], 26, (10, 14, 22, 215))
    draw.text((46, 276), scene["subtitle"], font=load_font(FONT_BOLD, 28), fill=(245, 247, 250))
    draw.text((46, 320), f"{stats['rounds']} rounds  •  {stats['mongolz_kills']} vs {stats['mouz_kills']} kills", font=sub, fill=(150, 158, 172))
    rounded(draw, [28, H - 230, W - 28, H - 70], 28, (10, 14, 22, 210))
    draw.text((46, H - 208), "WHY IT MATTERS", font=mini, fill=(112, 214, 255))
    draw_tokens(draw, 46, H - 176, f"{stats['first_kill']} нээлтийг хийж, {stats['top_fragger']} хамгийн их frag авсан.", load_font(FONT_BOLD, 28), W - 90)
    draw.text((28, H - 36), match_id.replace("_", " ").upper(), font=mini, fill=(255, 200, 0))


def draw_fullscreen_scene(draw, scene, script_chunk, accent, top_label):
    mini = load_font(FONT_BOLD, 14)
    title = load_font(FONT_BOLD, 34)
    body = load_font(FONT_BOLD, 26)
    draw.text((28, 28), top_label, font=mini, fill=accent)
    draw.text((28, 58), scene["title"], font=title, fill=(250, 252, 255))
    rounded(draw, [20, 18, W - 20, 106], 20, (0, 0, 0, 0), outline=accent, width=2)
    rounded(draw, [28, H - 250, W - 28, H - 70], 26, (10, 14, 22, 220))
    draw.text((46, H - 222), scene["subtitle"].upper(), font=mini, fill=accent)
    lines = wrap_text(script_chunk, body, W - 92)[:3]
    y = H - 192
    for i, line in enumerate(lines):
        fill = (255, 220, 130) if i == 0 else (245, 247, 250)
        draw_tokens(draw, 46, y, line, body, W - 92, default=fill, line_gap=8)
        y += 40


def draw_split_scene(draw, scene, script_chunk, stats, accent):
    mini = load_font(FONT_BOLD, 14)
    title = load_font(FONT_BOLD, 28)
    body = load_font(FONT_BOLD, 24)
    rounded(draw, [28, 28, W - 28, 92], 18, (10, 14, 22, 210))
    draw.text((46, 48), scene["title"], font=title, fill=(250, 252, 255))
    draw.text((46, 76), scene["subtitle"], font=mini, fill=accent)
    rounded(draw, [28, 108, W - 28, 208], 24, (10, 14, 22, 215))
    draw.text((46, 128), "MATCH SNAPSHOT", font=mini, fill=accent)
    draw.text((46, 158), f"{stats['mongolz_kills']} : {stats['mouz_kills']} kills", font=title, fill=(245, 247, 250))
    draw.text((46, 192), f"Top frag: {stats['top_fragger']} ({stats['top_kills']})", font=mini, fill=(170, 176, 190))
    rounded(draw, [28, H - 220, W - 28, H - 70], 24, (10, 14, 22, 220))
    lines = wrap_text(script_chunk, body, W - 92)[:3]
    y = H - 192
    for line in lines:
        draw_tokens(draw, 46, y, line, body, W - 92)
        y += 36


def make_scene_frame(scene, script_chunk, stats, match_id, map_name, idx):
    focus_x = [0.15, 0.45, 0.3, 0.58, 0.22, 0.48][idx % 6]
    focus_y = [0.12, 0.25, 0.4, 0.18, 0.35, 0.22][idx % 6]
    fit_scenes = {"heatmap", "firstkill", "deathmap", "economy", "utility", "awp", "round", "clutch"}
    if scene["key"] in fit_scenes:
        bg = bg_image(scene["image"], zoom=0.96, mode="fit")
    else:
        bg = bg_image(scene["image"], zoom=1.06, focus_x=focus_x, focus_y=focus_y, mode="cover")
    img = add_overlay(bg, 1.0)
    draw = ImageDraw.Draw(img)
    accents = {
        "heatmap": (255, 190, 0),
        "firstkill": (255, 210, 90),
        "deathmap": (255, 90, 190),
        "economy": (80, 220, 130),
        "utility": (80, 210, 255),
        "awp": (120, 220, 255),
        "round": (255, 140, 80),
        "clutch": (255, 90, 90),
        "hook": (255, 190, 0),
    }
    accent = accents.get(scene["key"], (255, 190, 0))
    if scene["key"] == "hook":
        draw_hook(draw, scene, stats, match_id, map_name)
    elif scene["key"] in {"economy", "utility", "firstkill"}:
        draw_split_scene(draw, scene, script_chunk, stats, accent)
    else:
        draw_fullscreen_scene(draw, scene, script_chunk, accent, map_name.upper())
    draw.rectangle([(0, 0), (W, 8)], fill=accent)
    draw.text((W - 26, H - 36), "CS2 SHORTS", font=load_font(FONT_BOLD, 14), fill=accent, anchor="ra")
    return np.array(img)


def allocate_durations(total, count):
    base = total / max(count, 1)
    weights = [1.2] + [1.0] * max(0, count - 2) + ([0.9] if count > 1 else [])
    weights = weights[:count]
    s = sum(weights) or 1
    return [total * w / s for w in weights]


def build_voice_mix(voice):
    fps = 22050
    t = np.linspace(0, voice.duration, int(voice.duration * fps), endpoint=False)
    hit = np.zeros_like(t, dtype=np.float32)
    for point in np.linspace(0.6, max(0.8, voice.duration - 0.8), 6):
        m = (t >= point) & (t < point + 0.08)
        hit[m] += 0.015 * np.sin(2 * np.pi * 300 * (t[m] - point)) * np.exp(-30 * (t[m] - point))
    layers = [
        voice,
        AudioArrayClip(np.column_stack([hit, hit]), fps=fps).set_duration(voice.duration),
    ]
    return CompositeAudioClip(layers)


def main():
    if len(sys.argv) != 6:
        sys.exit(1)

    script_file, json_path, heatmap_img, awp_img, output_video = sys.argv[1:6]
    script_text = clip_script(open(script_file, encoding="utf-8").read().strip())
    data = json.load(open(json_path, encoding="utf-8"))
    match_id = data.get("match_id", "match")
    map_name = data.get("map", "de_mirage")
    stats = analyze(data)
    assets = find_assets(match_id, map_name, heatmap_img, awp_img)
    scenes = build_scenes(assets, stats) or [{"key": "hook", "title": "MATCH BREAKDOWN", "subtitle": "Гол мөчүүд", "image": heatmap_img}]

    temp_audio = "/data/videos/temp_voice.mp3"
    if os.path.exists(temp_audio):
        os.remove(temp_audio)

    asyncio.run(generate_voiceover(script_text, temp_audio))
    voice = AudioFileClip(temp_audio)
    if voice.duration > 42:
        voice = voice.subclip(0, 42)
    if voice.duration < 35:
        target = 35
    else:
        target = min(42, voice.duration)
    if voice.duration > target:
        voice = voice.subclip(0, target)

    chunks = split_chunks(clean_script(script_text), len(scenes))
    durations = allocate_durations(voice.duration, len(scenes))
    clips = []
    for i, scene in enumerate(scenes):
        frame = make_scene_frame(scene, chunks[min(i, len(chunks) - 1)], stats, match_id, map_name, i)
        clip = ImageClip(frame).set_duration(durations[i])
        if i > 0:
            clip = clip.fx(fadein, 0.15)
        if i < len(scenes) - 1:
            clip = clip.fx(fadeout, 0.15)
        clips.append(clip)

    video = concatenate_videoclips(clips, method="compose").set_audio(build_voice_mix(voice))
    os.makedirs(os.path.dirname(output_video), exist_ok=True)
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


if __name__ == "__main__":
    main()
