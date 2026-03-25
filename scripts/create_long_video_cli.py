#!/usr/bin/env python3
import sys, os, asyncio, json
import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (ImageClip, AudioFileClip, CompositeVideoClip,
                             concatenate_videoclips, VideoClip, ColorClip, TextClip)
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

W, H = 1920, 1080

async def generate_voiceover(text, output_path):
    """Урт текстийг хэсэг хэсгээр үүсгэж нэгтгэх"""
    import tempfile
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    chunk_size = 5
    chunks = [". ".join(sentences[i:i+chunk_size]) + "." 
              for i in range(0, len(sentences), chunk_size)]
    
    temp_files = []
    for i, chunk in enumerate(chunks):
        tmp = f"{output_path}.part{i}.mp3"
        communicate = edge_tts.Communicate(chunk, "mn-MN-YesuiNeural")
        await communicate.save(tmp)
        if os.path.exists(tmp) and os.path.getsize(tmp) > 100:
            temp_files.append(tmp)
    
    if not temp_files:
        raise ValueError("Voiceover үүсгэхэд бүх хэсэг алдаатай")
    
    # ffmpeg-ээр нэгтгэх
    import subprocess as sp
    list_file = f"{output_path}.list.txt"
    with open(list_file, "w") as f:
        for tf in temp_files:
            f.write(f"file '{tf}'\n")
    sp.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file,
            "-c", "copy", output_path, "-y"], 
           capture_output=True)
    
    # Цэвэрлэх
    for tf in temp_files:
        if os.path.exists(tf): os.remove(tf)
    if os.path.exists(list_file): os.remove(list_file)

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def make_section_frame(bg_path, section_title, section_sub,
                       match_id, map_name, progress=0.0):
    img = Image.new("RGB", (W, H), (8, 8, 12))
    draw = ImageDraw.Draw(img)

    # Арын зураг
    if os.path.exists(bg_path):
        bg = Image.open(bg_path).convert("RGB")
        zoom = 1.0 + progress * 0.08
        bw = int(W * zoom)
        bh = int(H * zoom)
        bg = bg.resize((bw, bh), Image.LANCZOS)
        x_off = (bw - W) // 2
        y_off = (bh - H) // 2
        bg_crop = bg.crop((x_off, y_off, x_off + W, y_off + H))
        img.paste(bg_crop, (0, 0))

    # Доод gradient overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    for i in range(300):
        a = int(220 * (i / 300) ** 1.5)
        ov.rectangle([(0, H - 300 + i), (W, H - 300 + i + 1)], fill=(8, 8, 12, a))
    # Зүүн overlay
    for i in range(500):
        a = int(200 * (1 - i / 500) ** 1.2)
        ov.rectangle([(i, 0), (i + 1, H)], fill=(8, 8, 12, a))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    font_big   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    font_med   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
    font_small = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    font_logo  = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)

    # Дээд лого мөр
    draw.rectangle([(0, 0), (W, 70)], fill=(8, 8, 15))
    draw.text((40, 20), "CS2 DATA LAB", font=font_logo, fill=(255, 200, 0))
    draw.text((W - 40, 20), f"{match_id}  ·  {map_name.upper()}", 
              font=font_logo, fill=(150, 150, 150), anchor="ra")
    draw.rectangle([(0, 70), (W, 75)], fill=(255, 200, 0))

    # Section title — зүүн доод
    draw.text((60, H - 220), section_title,
              font=font_big, fill=(255, 255, 255))
    draw.text((60, H - 130), section_sub,
              font=font_med, fill=(255, 200, 0))

    # Progress bar
    bar_w = int(W * progress)
    draw.rectangle([(0, H - 4), (W, H)], fill=(30, 30, 40))
    draw.rectangle([(0, H - 4), (bar_w, H)], fill=(255, 200, 0))

    return np.array(img)

def make_intro_frame(match_id, map_name, mongolz_kills, mouz_kills):
    img = Image.new("RGB", (W, H), (8, 8, 12))
    draw = ImageDraw.Draw(img)

    font_title  = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 96)
    font_sub    = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
    font_stat   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
    font_label  = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    font_logo   = load_font("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)

    # Лого
    draw.rectangle([(0, 0), (W, 70)], fill=(8, 8, 15))
    draw.text((40, 20), "CS2 DATA LAB", font=font_logo, fill=(255, 200, 0))
    draw.rectangle([(0, 70), (W, 75)], fill=(255, 200, 0))

    # Гол title
    draw.text((W // 2, 220), "ТАКТИКИЙН ДҮРСЛЭЛ",
              font=font_title, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, 320), map_name.upper(),
              font=font_sub, fill=(255, 200, 0), anchor="mm")

    # VS хэсэг
    cx = W // 2
    # Mongolz
    draw.rectangle([(cx - 500, 420), (cx - 20, 680)], fill=(20, 20, 30))
    draw.rectangle([(cx - 500, 420), (cx - 20, 460)], fill=(40, 35, 10))
    draw.text((cx - 260, 440), "MONGOLZ", font=font_label,
              fill=(255, 200, 0), anchor="mm")
    draw.text((cx - 260, 580), str(mongolz_kills), font=font_stat,
              fill=(255, 200, 0), anchor="mm")
    draw.text((cx - 260, 655), "kills", font=font_label,
              fill=(150, 150, 150), anchor="mm")

    # VS
    draw.text((cx, 550), "VS", font=font_sub,
              fill=(80, 80, 80), anchor="mm")

    # mouz
    draw.rectangle([(cx + 20, 420), (cx + 500, 680)], fill=(20, 20, 30))
    draw.rectangle([(cx + 20, 420), (cx + 500, 460)], fill=(40, 10, 10))
    draw.text((cx + 260, 440), "MOUZ", font=font_label,
              fill=(255, 80, 80), anchor="mm")
    draw.text((cx + 260, 580), str(mouz_kills), font=font_stat,
              fill=(255, 80, 80), anchor="mm")
    draw.text((cx + 260, 655), "kills", font=font_label,
              fill=(150, 150, 150), anchor="mm")

    # Match ID
    draw.text((W // 2, 760), match_id.replace("_", " ").upper(),
              font=font_label, fill=(100, 100, 100), anchor="mm")

    # CTA доод
    draw.rectangle([(0, H - 60), (W, H)], fill=(15, 15, 20))
    draw.text((W // 2, H - 30), "SUBSCRIBE  ·  CS2 DATA LAB  ·  LIKE & COMMENT",
              font=font_label, fill=(255, 200, 0), anchor="mm")

    return np.array(img)

def zoom_clip(bg_path, section_title, section_sub,
              match_id, map_name, duration):
    def make_t(t):
        progress = t / max(duration, 0.01)
        return make_section_frame(bg_path, section_title, section_sub,
                                  match_id, map_name, progress)
    return VideoClip(make_t, duration=duration)

def main():
    if len(sys.argv) < 3:
        print("Usage: create_long_video_cli.py <json_path> <output_video> [visuals_dir]")
        sys.exit(1)

    json_path    = sys.argv[1]
    output_video = sys.argv[2]
    visuals_dir  = sys.argv[3] if len(sys.argv) > 3 else "/data/visuals"
    script_file  = sys.argv[4] if len(sys.argv) > 4 else None

    with open(json_path, "r") as f:
        jdata = json.load(f)

    match_id = jdata.get("match_id", "match")
    map_name = jdata.get("map", "de_mirage")

    # Kill тоо тооцоолох
    MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
    MOUZ    = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}
    raw = jdata.get("kills", [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw
    mongolz_kills = sum(1 for k in kills if isinstance(k, dict) and k.get("attacker_name") in MONGOLZ)
    mouz_kills    = sum(1 for k in kills if isinstance(k, dict) and k.get("attacker_name") in MOUZ)

    # Визуализацийн файлууд
    def vpath(suffix):
        return f"{visuals_dir}/{match_id}_{map_name}_{suffix}.png"

    sections = [
        (vpath("heatmap"),   "KILL HEATMAP",   "Хаана их тулаан болсон",    90),
        (vpath("deathmap"),  "DEATH MAP",       "Хаана их үхэл болсон",      60),
        (vpath("tactics"),   "ТАКТИКИЙН ЗАМ",  "2 багийн довтолгоо",        120),
        (vpath("awp"),       "AWP POSITIONS",   "Снайпер хяналтын цэгүүд",   90),
        (vpath("economy"),   "ECONOMY GRAPH",   "Мөнгөний давуу тал",        90),
        (vpath("utility"),   "UTILITY MAP",     "Flash • Smoke • Molotov",   90),
        (vpath("round45"),   "ROUND 45 CLUTCH", "xertioN 1v3 clutch",        90),
    ]

    # AWP файлын нэр өөр байна
    awp_path = f"{visuals_dir}/{match_id}_awp_positions.png"

    clips = []

    # Intro — 30 сек
    intro_frame = make_intro_frame(match_id, map_name, mongolz_kills, mouz_kills)
    intro = ImageClip(intro_frame).set_duration(30)
    clips.append(intro.fx(fadeout, 0.5))

    # Section бүр
    for i, (img_path, title, sub, dur) in enumerate(sections):
        # AWP зам засах
        if "awp" in img_path:
            img_path = awp_path

        if not os.path.exists(img_path):
            print(f"WARNING: {img_path} байхгүй — алгасав")
            continue

        clip = zoom_clip(img_path, title, sub, match_id, map_name, dur)
        clip = clip.fx(fadein, 0.4).fx(fadeout, 0.4)
        clips.append(clip)

    # Outro — 30 сек
    outro_frame = make_intro_frame(match_id, map_name, mongolz_kills, mouz_kills)
    outro = ImageClip(outro_frame).set_duration(30)
    clips.append(outro.fx(fadein, 0.5))

    if not clips:
        print("Clip байхгүй!")
        sys.exit(1)

    # Voiceover script үүсгэх
    # Gemini-аас авсан script ашиглах
    if script_file and os.path.exists(script_file):
        with open(script_file, "r", encoding="utf-8") as sf:
            script = sf.read().strip()
    else:
        script = f"""
    Сайн байцгаана уу! CS2 Data Lab-д тавтай морилно уу.
    Өнөөдөр бид {match_id.replace('_', ' ')} тоглолтын {map_name} map-ийн дүн шинжилгээг хийнэ.
    Mongolz {mongolz_kills} kill хийхэд mouz {mouz_kills} kill хийсэн энэ тоглолтод юу болсныг харцгаая.
    Эхлээд kill heatmap-ийг харвал хамгийн их тулаан mid болон A site-д болсон байна.
    Death map-аас харахад Mongolz {mongolz_kills} удаа унасан нь mouz-ийн {mouz_kills}-аас хамаагүй их байна.
    Тактикийн зургаас хоёр баг mid-г эзэмшихийг оролдсон нь харагдаж байна.
    AWP positions-аас mouz-ийн снайперууд mid болон A connector-ийг хянасан байна.
    Economy graph-аас mouz санхүүгийн давуу талтай байсан нь тодорхой харагдаж байна.
    Utility map-аас mouz HE grenade хамаагүй их ашигласан байна.
    Сүүлийн round-д xertioN гайхалтай clutch хийж тоглолтыг дуусгасан.
    Энэ видео таалагдсан бол like дараарай. Subscribe хийгээд дараагийн шинжилгээг алдалгүй үзээрэй!
    """

    temp_audio = f"/data/videos/temp_long_voice.mp3"
    # Хуучин файл устгах
    if os.path.exists(temp_audio):
        os.remove(temp_audio)
    print("Generating voiceover...")
    asyncio.run(generate_voiceover(script.strip(), temp_audio))
    # Файл үүссэн эсэх шалгах
    import time
    time.sleep(2)
    if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1000:
        raise ValueError(f"Voiceover файл үүсгэхэд алдаа гарлаа: {temp_audio}")
    print(f"Audio file size: {os.path.getsize(temp_audio)} bytes")

    audio = AudioFileClip(temp_audio)
    total_clip_dur = sum(c.duration for c in clips)
    print(f"Total clip duration: {total_clip_dur:.1f}s, Audio: {audio.duration:.1f}s")

    video = concatenate_videoclips(clips, method="compose")

    # Audio-г clip уртад тааруулах
    if audio.duration < video.duration:
        from moviepy.audio.fx.audio_loop import audio_loop
        audio = audio_loop(audio, duration=video.duration)
    else:
        audio = audio.subclip(0, video.duration)

    video = video.set_audio(audio)

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
