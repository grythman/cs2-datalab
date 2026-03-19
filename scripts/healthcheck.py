from pathlib import Path

for p in ["/data/raw", "/data/parsed", "/data/visuals", "/app/scripts"]:
    print(f"{p}: {'OK' if Path(p).exists() else 'MISSING'}")
