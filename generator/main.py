import subprocess
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class RenderRequest(BaseModel):
    match_id: str
    map_name: str

class ShortsRequest(BaseModel):
    match_id: str
    map_name: str
    script_text: str

@app.post("/render-heatmap")
async def render_heatmap(req: RenderRequest):
    try:
        json_path = f"/data/parsed/{req.match_id}_{req.map_name}.json"
        map_path = f"/data/scripts/maps/{req.map_name}.png"
        output_path = f"/data/visuals/{req.match_id}_{req.map_name}_heatmap.png"

        command = ["python3", "/data/scripts/vis_heatmap_cli.py", json_path, map_path, output_path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "file": os.path.basename(output_path)}
        raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/render-awp")
async def render_awp(req: RenderRequest):
    try:
        json_path = f"/data/parsed/{req.match_id}_{req.map_name}.json"
        # Бодит нэршилд тааруулав: _awp_positions.png
        output_path = f"/data/visuals/{req.match_id}_awp_positions.png"
        
        command = ["python3", "/data/scripts/visualize_awp_cli.py", json_path, output_path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "file": os.path.basename(output_path)}
        raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/create-shorts")
async def create_shorts(req: ShortsRequest):
    try:
        script_file = f"/data/scripts/{req.match_id}_script.txt"
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(req.script_text)

        json_path = f"/data/parsed/{req.match_id}_{req.map_name}.json"
        heatmap_img = f"/data/visuals/{req.match_id}_{req.map_name}_heatmap.png"
        awp_img = f"/data/visuals/{req.match_id}_awp_positions.png"
        output_video = f"/data/videos/{req.match_id}_short.mp4"
        
        command = [
            "python3", "/data/scripts/create_shorts_cli.py", 
            script_file, json_path, heatmap_img, awp_img, output_video
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "file": f"{req.match_id}_short.mp4"}
        raise HTTPException(status_code=500, detail=result.stderr)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
