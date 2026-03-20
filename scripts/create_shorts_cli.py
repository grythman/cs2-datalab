#!/usr/bin/env python3
import sys, os, asyncio, json
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (ImageClip, AudioFileClip, CompositeVideoClip,
                             concatenate_videoclips, TextClip, ColorClip)

W, H = 1080, 1920  # YouTube Shorts хэмжээ

async def generate_voiceover(text, output_path):
    communicate = edge_tts.Communicate(text, "mn-MN-YesuiNeural")
    await communicate.save(output_path)

def make_frame(bg_path, title, stat, color=(255, 165, 0)):
    """CS2 style frame үүсгэх"""
    img = Image.new("RGB", (W, H), (10, 10, 15))
    draw = ImageDraw.Draw(img)

    # Арын зураг (heatmap/awp) — дунд хэсэгт
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        # 1080x1080 болгон resize
        bg = bg.resize((W, W), Image.LANCZOS)
        # Дунд байрлуул
        y_offset = (H - W) // 2
        img.paste(bg, (0, y_offset))

    # Дээд overlay — gradient
    for i in range(350):
        alpha = int(255 * (1 - i / 350))
        draw.rectangle([(0, i), (W, i+1)], fill=(10, 10, 15, alpha))

    # Доод overlay
    for i in range(400):
        y = H - 400 + i
        alpha = int(255 * (i / 400))
        draw.rectangle([(0, y), (W, y+1)], fill=(10, 10, 15, alpha))

    # Шар зураас — дээд хэсэгт
    draw.rectangle([(0, 120), (W, 125)], fill=color)

    # Title текст
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    except:
        font_big = font_med = font_small = ImageFont.load_default()

    # CS2 DATA LAB лого
    draw.text((40, 40), "CS2 DATA LAB", font=font_small, fill=color)
    draw.text((W-260, 40), "MONGOLZ", font=font_small, fill=(255, 255, 255))

    # Гол title
    draw.text((40, 140), title, font=font_big, fill=(255, 255, 255))

    # Stat хэсэг — доод талд
    draw.rectangle([(0, H-380), (W, H-370)], fill=color)
    draw.text((40, H-360), stat, font=font_med, fill=(255, 255, 255))

    return np.array(img)

def split_script(text, n=3):
    """Зохиолыг n хэсэгт хуваах"""
    sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]
    chunk = max(1, len(sentences) // n)
    parts = []
    for i in range(0, len(sentences), chunk):
        parts.append('. '.join(sentences[i:i+chunk]) + '.')
    return parts[:n]

def main():
    if len(sys.argv) != 6:
        print("Usage: create_shorts_cli.py <script_file> <json_path> <heatmap_img> <awp_img> <output_video>")
        sys.exit(1)

    script_file = sys.argv[1]
    json_path   = sys.argv[2]
    heatmap_img = sys.argv[3]
    awp_img     = sys.argv[4]
    output_video = sys.argv[5]

    with open(script_file, "r", encoding="utf-8") as f:
        script_text = f.read().strip()

    # Match мэдээлэл JSON-аас авах
    match_id, map_name = "MATCH", "de_mirage"
    try:
        with open(json_path, "r") as f:
            jdata = json.load(f)
        match_id = jdata.get("match_id", match_id).replace("_", " ").upper()
        map_name = jdata.get("map", map_name)
    except:
        pass

    # Voiceover үүсгэх
    temp_audio = "/data/videos/temp_voice.mp3"
    print("Generating Mongolian voiceover...")
    asyncio.run(generate_voiceover(script_text, temp_audio))

    audio_clip = AudioFileClip(temp_audio)
    total_dur = audio_clip.duration
    print(f"Duration: {total_dur:.1f}s")

    # 3 хэсэгт хуваах
    part1_dur = total_dur * 0.15   # Hook — 15%
    part2_dur = total_dur * 0.55   # Heatmap — 55%
    part3_dur = total_dur * 0.30   # AWP — 30%

    # Frame үүсгэх
    hook_frame   = make_frame(heatmap_img,
                              "ТАКТИКИЙН ШИНЖИЛГЭЭ",
                              f"{match_id} · {map_name.upper()}")

    heat_frame   = make_frame(heatmap_img,
                              "KILL HEATMAP",
                              "Хамгийн идэвхтэй бүс",
                              color=(255, 100, 0))

    awp_frame    = make_frame(awp_img,
                              "AWP POSITIONS",
                              "Снайпер хяналтын цэгүүд",
                              color=(0, 200, 255))

    clips = [
        ImageClip(hook_frame).set_duration(part1_dur),
        ImageClip(heat_frame).set_duration(part2_dur),
        ImageClip(awp_frame).set_duration(part3_dur),
    ]

    video = concatenate_videoclips(clips, method="compose")
    video = video.set_audio(audio_clip)

    os.makedirs(os.path.dirname(output_video), exist_ok=True)
    print(f"Rendering {output_video}...")
    video.write_videofile(
        output_video, fps=24, codec="libx264",
        audio_codec="aac", preset="ultrafast", logger=None
    )

    if os.path.exists(temp_audio):
        os.remove(temp_audio)

    print("Done!")

if __name__ == "__main__":
    main()
