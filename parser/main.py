from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import subprocess
import glob
import shutil
import asyncio
from playwright.async_api import async_playwright
from demoparser2 import DemoParser
import pandas as pd

app = FastAPI(title="CS2 Data Lab - Hardened Engine")

def force_to_json_friendly(data):
    """Pandas, Numpy болон Tuple объектуудыг JSON-д албадан хувиргах Ultimate шүүлтүүр"""
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return json.loads(data.to_json(orient="records" if isinstance(data, pd.DataFrame) else "index"))
    if isinstance(data, dict):
        return {str(k): force_to_json_friendly(v) for k, v in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [force_to_json_friendly(i) for i in data]
    if hasattr(data, 'item'):
        return data.item()
    return data

class ProcessRequest(BaseModel):
    demo_url: str
    filename: str

@app.post("/process")
async def process_match(req: ProcessRequest):
    parsed_dir = "/data/parsed"
    raw_dir = "/data/raw"
    os.makedirs(parsed_dir, exist_ok=True)
    os.makedirs(raw_dir, exist_ok=True)

    # 1. CACHE CHECK: Parse хийгдсэн JSON файл байгаа эсэхийг шалгах
    # Хэрэв {filename}_ эхлэлтэй ямар нэгэн JSON байвал өмнө нь амжилттай хийгдсэн гэж үзнэ
    existing_jsons = glob.glob(f"{parsed_dir}/{req.filename}_*.json")
    if existing_jsons:
        print(f"✅ CACHE HIT: '{req.filename}' аль хэдийн боловсруулагдсан байна. Татах шатыг алгаслаа.")
        processed_maps = []
        for j in existing_jsons:
            # Файлын нэрнээс map_name-ийг сугалах (Жишээ нь: mouz_vs_mongolz_cluj_de_mirage.json -> de_mirage)
            base_name = os.path.basename(j).replace(".json", "")
            map_name = base_name.replace(f"{req.filename}_", "")
            processed_maps.append(map_name)
        
        return {"status": "success", "processed_maps": processed_maps, "cached": True}

    # 2. CACHE MISS: Байхгүй бол шинээр татаж, задлах руу орно
    print(f"📥 CACHE MISS: '{req.filename}' татаж эхэллээ...")
    raw_rar_path = f"{raw_dir}/{req.filename}.rar"
    extract_dir = f"{raw_dir}/{req.filename}_extracted"
    
    if os.path.exists(raw_rar_path): os.remove(raw_rar_path)
    if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
    os.makedirs(extract_dir, exist_ok=True)

    try:
        # Playwright ашиглан HLTV-г давах
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
            page = await context.new_page()
            async with page.expect_download(timeout=300000) as download_info:
                try: await page.goto(req.demo_url)
                except Exception as e:
                    if "Download is starting" not in str(e): print(f"Download log: {e}")
            download = await download_info.value
            await download.save_as(raw_rar_path)
            await browser.close()
        
        print("✅ Татаж дууслаа, архив задалж байна...")
        subprocess.run(['unar', '-f', '-o', extract_dir, raw_rar_path], check=True, stdout=subprocess.DEVNULL)
        if os.path.exists(raw_rar_path): os.remove(raw_rar_path)

        dem_files = glob.glob(f"{extract_dir}/**/*.dem", recursive=True)
        if not dem_files: raise HTTPException(status_code=404, detail=".dem олдсонгүй.")

        print("⚙️ Өгөгдөл олборлож байна (Parsing)...")
        processed_maps = []
        for dem_file in dem_files:
            parser = DemoParser(dem_file)
            
            header_data = force_to_json_friendly(parser.parse_header())
            kills_data = force_to_json_friendly(parser.parse_events(["player_death"]))
            
            if isinstance(header_data, list) and len(header_data) > 0:
                header_data = header_data[0]
            
            map_name = header_data.get("map_name", "unknown") if isinstance(header_data, dict) else "unknown"
            parsed_path = f"{parsed_dir}/{req.filename}_{map_name}.json"
            
            with open(parsed_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "match_id": req.filename,
                    "map": map_name,
                    "header": header_data,
                    "kills": kills_data
                }, f, ensure_ascii=False, indent=4)
            
            processed_maps.append(map_name)

        print("✅ Parsing бүрэн дууслаа.")
        return {"status": "success", "processed_maps": processed_maps, "cached": False}

    except Exception as e:
        print(f"❌ ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))
