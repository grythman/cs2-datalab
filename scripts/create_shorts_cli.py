#!/usr/bin/env python3
import sys, os, asyncio, json
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (ImageClip, AudioFileClip, CompositeVideoClip,
                             concatenate_videoclips, VideoClip)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

W, H = 1080, 1920

async def generate_voiceover(text, output_path):
    communicate = edge_tts.Communicate(text, "mn-MN-YesuiNeural")
    await communicate.save(output_path)

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)
    draw.ellipse([x1, y1, x1+2*radius, y1+2*radius], fill=fill)
    draw.ellipse([x2-2*radius, y1, x2, y1+2*radius], fill=fill)
    draw.ellipse([x1, y2-2*radius, x1+2*radius, y2], fill=fill)
    draw.ellipse([x2-2*radius, y2-2*radius, x2, y2], fill=fill)

def make_frame(bg_path, section, match_id, map_name,
               mongolz_kills=0, mouz_kills=0, zoom=1.0):
    img = Image.new("RGB", (W, H), (8, 8, 12))
    draw = ImageDraw.Draw(img)

    # Арын зураг — zoom эффекттэй
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        bw = int(W * zoom)
        bh = int(W * zoom)
        bg = bg.resize((bw, bh), Image.LANCZOS)
        x_off = (bw - W) // 2
        y_off_img = (H - W) // 2
        bg_crop = bg.crop((x_off, x_off, x_off + W, x_off + W))
        img.paste(bg_crop, (0, y_off_img))

    # Дээд gradient overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for i in range(420):
        a = int(220 * (1 - i/420)**1.5)
        ov_draw.rectangle([(0, i), (W, i+1)], fill=(8, 8, 12, a))
    for i in range(500):
        y = H - 500 + i
        a = int(240 * (i/500)**1.2)
        ov_draw.rectangle([(0, y), (W, y+1)], fill=(8, 8, 12, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
    font_logo   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
    font_title  = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 78)
    font_sub    = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44)
    font_stat   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
    font_label  = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)

    # Дээд хэсэг — лого + map
    draw.rectangle([(0, 0), (W, 90)], fill=(8, 8, 12))
    draw.text((40, 28), "CS2 DATA LAB", font=font_logo, fill=(255, 200, 0))
    map_text = map_name.upper()
    draw.text((W-40, 28), map_text, font=font_logo, fill=(180, 180, 180),
              anchor="ra")
    # Шар зураас
    draw.rectangle([(0, 90), (W, 95)], fill=(255, 200, 0))

    # Section title
    if section == "hook":
        draw.text((40, 115), "ТАКТИКИЙН", font=font_title, fill=(255, 255, 255))
        draw.text((40, 205), "ШИНЖИЛГЭЭ", font=font_title, fill=(255, 200, 0))
        # Match badge
        draw_rounded_rect(draw, [40, 310, 420, 370], 12, (30, 30, 40))
        draw.text((230, 340), match_id, font=font_label,
                  fill=(200, 200, 200), anchor="mm")

    elif section == "heatmap":
        draw.text((40, 115), "KILL", font=font_title, fill=(255, 255, 255))
        draw.text((40, 205), "HEATMAP", font=font_title, fill=(255, 100, 30))
        draw.text((40, 300), "Хамгийн идэвхтэй бүс", font=font_sub,
                  fill=(180, 180, 180))

    elif section == "awp":
        draw.text((40, 115), "AWP", font=font_title, fill=(255, 255, 255))
        draw.text((40, 205), "CONTROL", font=font_title, fill=(0, 200, 255))
        draw.text((40, 300), "Снайпер хяналтын цэгүүд", font=font_sub,
                  fill=(180, 180, 180))

    # Доод stats panel
    panel_y = H - 460
    draw.rectangle([(0, panel_y), (W, panel_y + 4)], fill=(255, 200, 0))

    # Mongolz stats
    draw_rounded_rect(draw, [40, panel_y+20, 500, panel_y+200], 16, (20, 20, 30))
    draw.text((270, panel_y+60), "MONGOLZ", font=font_label,
              fill=(255, 200, 0), anchor="mm")
    draw.text((270, panel_y+140), str(mongolz_kills), font=font_stat,
              fill=(255, 200, 0), anchor="mm")
    draw.text((270, panel_y+185), "kills", font=font_label,
              fill=(150, 150, 150), anchor="mm")

    # mouz stats
    draw_rounded_rect(draw, [580, panel_y+20, W-40, panel_y+200], 16, (20, 20, 30))
    draw.text((810, panel_y+60), "MOUZ", font=font_label,
              fill=(255, 80, 80), anchor="mm")
    draw.text((810, panel_y+140), str(mouz_kills), font=font_stat,
              fill=(255, 80, 80), anchor="mm")
    draw.text((810, panel_y+185), "kills", font=font_label,
              fill=(150, 150, 150), anchor="mm")

    # VS текст
    draw.text((W//2, panel_y+110), "VS", font=font_sub,
              fill=(100, 100, 100), anchor="mm")

    # CTA доод талд
    draw.text((W//2, H-60), "SUBSCRIBE • CS2 DATA LAB",
              font=font_label, fill=(255, 200, 0), anchor="mm")

    return np.array(img)

def make_zoom_clip(bg_path, section, match_id, map_name,
                   mongolz_kills, mouz_kills, duration,
                   zoom_start=1.0, zoom_end=1.15):
    """Zoom эффекттэй clip"""
    def make_t(t):
        progress = t / max(duration, 0.01)
        zoom = zoom_start + (zoom_end - zoom_start) * progress
        return make_frame(bg_path, section, match_id, map_name,
                          mongolz_kills, mouz_kills, zoom=zoom)
    clip = VideoClip(make_t, duration=duration)
    return clip

def main():
    if len(sys.argv) != 6:
        sys.exit(1)

    script_file  = sys.argv[1]
    json_path    = sys.argv[2]
    heatmap_img  = sys.argv[3]
    awp_img      = sys.argv[4]
    output_video = sys.argv[5]

    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read().strip()

    match_id, map_name = "MATCH", "de_mirage"
    mongolz_kills, mouz_kills = 0, 0
    try:
        with open(json_path, "r") as f:
            jdata = json.load(f)
        match_id = jdata.get("match_id", match_id).replace("_", " ").upper()
        map_name = jdata.get("map", map_name)
        raw = jdata.get("kills", [])
        kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw
        MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
        MOUZ    = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}
        for k in kills:
            if not isinstance(k, dict):
                continue
            name = k.get('attacker_name', '')
            if name in MONGOLZ:
                mongolz_kills += 1
            elif name in MOUZ:
                mouz_kills += 1
    except:
        pass

    temp_audio = "/data/videos/temp_voice.mp3"
    print("Generating voiceover...")
    asyncio.run(generate_voiceover(script_text, temp_audio))

    audio = AudioFileClip(temp_audio)
    total = audio.duration
    print(f"Duration: {total:.1f}s")

    d1 = total * 0.12
    d2 = total * 0.53
    d3 = total * 0.35

    print("Rendering frames...")
    clip1 = make_zoom_clip(heatmap_img, "hook",    match_id, map_name,
                           mongolz_kills, mouz_kills, d1, 1.0, 1.08)
    clip2 = make_zoom_clip(heatmap_img, "heatmap", match_id, map_name,
                           mongolz_kills, mouz_kills, d2, 1.08, 1.18)
    clip3 = make_zoom_clip(awp_img,    "awp",      match_id, map_name,
                           mongolz_kills, mouz_kills, d3, 1.0, 1.1)

    # Fade transition
    clip1 = clip1.fx(fadeout, 0.4)
    clip2 = clip2.fx(fadein, 0.4).fx(fadeout, 0.4)
    clip3 = clip3.fx(fadein, 0.4)

    video = concatenate_videoclips([clip1, clip2, clip3], method="compose")
    video = video.set_audio(audio)

    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    print(f"Rendering video...")
    video.write_videofile(
        output_video, fps=24, codec="libx264",
        audio_codec="aac", preset="ultrafast", logger=None
    )

    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    print("Done!")

if __name__ == "__main__":
    main()
