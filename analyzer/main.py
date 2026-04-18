import subprocess
import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="CS2 Data Lab - Expert Tactical Analyzer")

# n8n-ээс ирэх бүх өгөгдлийг хүлээж авах загвар
class MasterPromptRequest(BaseModel):
    match_id: str
    map_name: str
    heatmap_file: str
    awp_file: str
    tactical_insight: Any

class AnalysisRequest(BaseModel):
    match_id: str
    map_name: str

@app.post("/analyze-tactics")
async def analyze_tactics(req: AnalysisRequest):
    input_json = f"/data/parsed/{req.match_id}_{req.map_name}.json"
    output_features = f"/data/features/{req.match_id}_tactical_summary.json"
    try:
        subprocess.run(["python3", "/data/scripts/mirage_mid_control_score_cli.py", input_json, output_features], check=True)
        # Үр дүнг нь уншаад буцаавал n8n-д ашиглахад илүү амар
        with open(output_features, "r") as f:
            insight = json.load(f)
        return {
            "status": "success",
            "insight": insight,
            "primary_angle": insight.get("primary_angle"),
            "story_angles": insight.get("story_angles", []),
            "file": output_features,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-script-prompt")
async def generate_script_prompt(req: MasterPromptRequest):
    try:
        insight = req.tactical_insight if isinstance(req.tactical_insight, dict) else {"raw": req.tactical_insight}
        primary_angle = insight.get("primary_angle") or {}
        story_angles = insight.get("story_angles") or []
        angle_lines = "\n".join(
            f"- {angle.get('label')}: {angle.get('reason')}"
            for angle in story_angles
            if isinstance(angle, dict)
        ) or "- No ranked angles available"

        # Промптын бүтэц: Role -> Context -> Data -> Task -> Format
        master_prompt = f"""
### ROLE: CS2 VIRAL CONTENT STRATEGIST & PRO ANALYST
Чи бол CS2-ийн тоглолтын өгөгдлийг ашиглан YouTube Shorts-д зориулсан Viral контент бүтээх мастер.

### CONTEXT:
- Match: {req.match_id}
- Map: {req.map_name}

### INPUT DATA:
1. **Heatmap:** {req.heatmap_file} (Тоглолтын хамгийн идэвхтэй цэгүүд).
2. **AWP Meta:** {req.awp_file} (AWP-ийн хяналтын бүсүүд).
3. **Tactical Insight:** {json.dumps(insight, ensure_ascii=False)} (Тактикийн гол дүгнэлтүүд).
4. **Primary Narrative Angle:** {primary_angle.get('label', 'Unknown')} :: {primary_angle.get('reason', 'No reason')}
5. **Supporting Angles:**
{angle_lines}

### TASK:
Дээрх өгөгдлийг ашиглан 60 секундын YouTube Shorts-ийн зохиол (Script) бич.
Скрипт нь нэг гол thesis-тэй байна. Гол thesis нь `Primary Narrative Angle` дээр төвлөрнө.
Бүтэц:
- 0-3 сек: **HOOK** - Үзэгчдийг шууд татах "Crazy" баримт эсвэл асуулт.
- 3-50 сек: **BODY** - Өгөгдөл дээр суурилсан аналитик тайлбар. (Gamer хэллэг ашигла: clutch, rotate, save).
- 50-60 сек: **CTA** - Subscribe хийхийг уриалж, хэлэлцүүлэг өрнүүлэх.

### CONSTRAINTS:
- Хэл: Монгол. Тон: Эрчимтэй, сонирхолтой.
- Зөвхөн бэлэн болсон Скриптийг буцаа.
"""
        return {
            "status": "success",
            "master_prompt": master_prompt.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
