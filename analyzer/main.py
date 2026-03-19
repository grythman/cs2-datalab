import subprocess
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="CS2 Data Lab - Expert Tactical Analyzer")

# n8n-ээс ирэх бүх өгөгдлийг хүлээж авах загвар
class MasterPromptRequest(BaseModel):
    match_id: str
    map_name: str
    heatmap_file: str
    awp_file: str
    tactical_insight: str

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
        import json
        with open(output_features, "r") as f:
            insight = json.load(f)
        return {"status": "success", "insight": insight, "file": output_features}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-script-prompt")
async def generate_script_prompt(req: MasterPromptRequest):
    try:
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
3. **Tactical Insight:** {req.tactical_insight} (Тактикийн гол дүгнэлтүүд).

### TASK:
Дээрх өгөгдлийг ашиглан 60 секундын YouTube Shorts-ийн зохиол (Script) бич.
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
