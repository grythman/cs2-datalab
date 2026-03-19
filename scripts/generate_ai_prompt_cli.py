#!/usr/bin/env python3
import json
import argparse
from pathlib import Path

def translate_to_metaphor(data):
    """Техникийн өгөгдлийг сторителл метафор руу хөрвүүлэх"""
    narrative = []
    
    # Эдийн засгийн ROI (Utility Efficiency)
    if data.get("mid_pct", 0) > 50:
        narrative.append("Mid хяналтын 'инвестици' үр дүнгээ өгч, эдийн засгийн давуу талыг авчирлаа.")
    
    # Sub-tick болон Тайминг
    narrative.append("Sub-tick систем нь энэ дуэль дэх 15.625 миллисекундын зөрүүг 'Олимпын финиш' мэт нарийвчлалтай бүртгэж авсан байна.")
    
    return " ".join(narrative)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_json")
    parser.add_argument("output_txt")
    args = parser.parse_args()

    with open(args.input_json, 'r') as f:
        data = json.load(f)

    story = translate_to_metaphor(data)
    
    # Ultimate Storytelling Prompt бүтэц
    full_prompt = f"""
    IDENTITY: Чи бол CS2 Data Lab-ийн ахлах аналитик.
    DATA SUMMARY: {json.dumps(data)}
    STORYLINE: {story}
    TASK: Дээрх өгөгдөл дээр тулгуурлан YouTube Shorts-д зориулсан 60 секундын сонирхолтой скрипт Монгол хэл дээр бич. 
    Visual Cues ашигла: [CUE: HEATMAP_PATH], [CUE: SUBTICK_FREEZE].
    """
    
    Path(args.output_txt).write_text(full_prompt, encoding='utf-8')
    print(f"Prompt saved to {args.output_txt}")

if __name__ == "__main__":
    main()
