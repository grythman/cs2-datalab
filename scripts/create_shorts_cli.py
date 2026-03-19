import sys
import os
import asyncio
import edge_tts
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

async def generate_voiceover(text, output_path):
    # Монгол хэлний хамгийн шилдэг AI хоолой: mn-MN-YesuiNeural
    voice = "mn-MN-YesuiNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def main():
    if len(sys.argv) != 6:
        print("Usage: python create_shorts_cli.py <script_file> <json_path> <heatmap_img> <awp_img> <output_video>")
        sys.exit(1)

    script_file = sys.argv[1]
    heatmap_img = sys.argv[3]
    awp_img = sys.argv[4]
    output_video = sys.argv[5]

    try:
        # 1. Текст унших
        with open(script_file, "r", encoding="utf-8") as f:
            script_text = f.read().strip()
        
        if not script_text:
            raise ValueError("Script файл хоосон байна.")

        # 2. Аудио үүсгэх (Async ажиллагаатай)
        temp_audio = "/data/videos/temp_voice.mp3"
        print(f"Generating professional Mongolian voiceover...")
        asyncio.run(generate_voiceover(script_text, temp_audio))

        # 3. Видео эвлүүлж эхлэх
        audio_clip = AudioFileClip(temp_audio)
        total_duration = audio_clip.duration

        print(f"Total duration: {total_duration}s. Processing images...")
        half_duration = total_duration / 2
        
        clip1 = ImageClip(heatmap_img).set_duration(half_duration)
        clip2 = ImageClip(awp_img).set_duration(half_duration)

        video = concatenate_videoclips([clip1, clip2], method="compose")
        video = video.set_audio(audio_clip)

        # 4. Хадгалах
        print(f"Rendering final video: {output_video}...")
        video.write_videofile(
            output_video, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac",
            preset="ultrafast",
            logger=None
        )

        # 5. Цэвэрлэгээ
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
        print("Success! Your video is ready.")

    except Exception as e:
        print(f"Error generating shorts: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
