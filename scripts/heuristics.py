import json
import os
import sys

# Газрын зургийн бүсүүд (Жишээ: Mirage)
# Эдгээр координатыг чи өөрийнхөөрөө нарийвчилж болно
MIRAGE_ZONES = {
    "A_SITE": {"x": (100, 1000), "y": (-1000, 100)},
    "B_SITE": {"x": (-2500, -1500), "y": (-500, 500)},
    "MID": {"x": (-1000, 100), "y": (-500, 500)}
}

def get_zone(x, y):
    for zone, coord in MIRAGE_ZONES.items():
        if coord["x"][0] <= x <= coord["x"][1] and coord["y"][0] <= y <= coord["y"][1]:
            return zone
    return "UNKNOWN"

def analyze_match(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    kills = data.get("kills", [])
    if not kills:
        return "Дата хоосон байна."

    # 1. Entry Frag Analysis
    first_kill = kills[0]
    killer = first_kill.get("attacker_name")
    victim = first_kill.get("user_name")
    side = "T" if first_kill.get("attacker_team") == "Terrorist" else "CT"
    
    # 2. Map Control (Хаана ихэвчлэн үхэл болсон бэ?)
    zone_stats = {}
    for k in kills:
        zone = get_zone(k.get("user_x", 0), k.get("user_y", 0))
        zone_stats[zone] = zone_stats.get(zone, 0) + 1

    analysis = {
        "map": data.get("map"),
        "entry_kill": f"{killer} killed {victim} ({side})",
        "hot_zones": zone_stats
    }
    return analysis

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("JSON файлын замыг оруулна уу.")
    else:
        result = analyze_match(sys.argv[1])
        print(json.dumps(result, indent=4, ensure_ascii=False))
