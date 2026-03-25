#!/usr/bin/env python3
import sys, os, json
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from PIL import Image

MAP_PARAMS = {
    "de_mirage":  {"pos_x": -3230, "pos_y": 1713, "scale": 5.0},
    "de_inferno": {"pos_x": -2087, "pos_y": 3870, "scale": 4.9},
    "de_dust2":   {"pos_x": -2476, "pos_y": 3239, "scale": 4.4},
    "de_ancient": {"pos_x": -2953, "pos_y": 2164, "scale": 5.0},
    "de_anubis":  {"pos_x": -2796, "pos_y": 3328, "scale": 5.22},
    "de_nuke":    {"pos_x": -3453, "pos_y": 2887, "scale": 7.0},
    "de_overpass":{"pos_x": -4831, "pos_y": 1781, "scale": 5.2},
    "de_vertigo": {"pos_x": -3168, "pos_y": 1762, "scale": 4.0},
}

MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
MOUZ    = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}

def world_to_radar(wx, wy, pos_x, pos_y, scale):
    return (wx - pos_x) / scale, (pos_y - wy) / scale

def get_team(name):
    if name in MONGOLZ: return "Mongolz"
    if name in MOUZ:    return "mouz"
    return "Unknown"

def main():
    if len(sys.argv) < 4:
        sys.exit(2)

    input_file, map_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    map_name = data.get('map', 'de_mirage')
    params = MAP_PARAMS.get(map_name, MAP_PARAMS['de_mirage'])

    raw = data.get('kills', [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw

    # Round-уудыг tick gap-аар ялгах
    sorted_kills = sorted([k for k in kills if isinstance(k, dict)],
                          key=lambda k: k.get('tick', 0))
    rounds = []
    if sorted_kills:
        current = [sorted_kills[0]]
        for k in sorted_kills[1:]:
            if k.get('tick', 0) - current[-1].get('tick', 0) > 1000:
                rounds.append(current)
                current = [k]
            else:
                current.append(k)
        rounds.append(current)

    # Round бүрийн эхний kill
    mongolz_fk_x, mongolz_fk_y = [], []
    mouz_fk_x,    mouz_fk_y    = [], []
    mongolz_win, mouz_win = 0, 0

    for r in rounds:
        first = r[0]
        name = first.get('attacker_name', '')
        wx = first.get('attacker_X')
        wy = first.get('attacker_Y')
        if wx is None or wy is None:
            continue
        rx, ry = world_to_radar(float(wx), float(wy),
                                params['pos_x'], params['pos_y'], params['scale'])
        team = get_team(name)
        if team == "Mongolz":
            mongolz_fk_x.append(rx)
            mongolz_fk_y.append(ry)
            mongolz_win += 1
        elif team == "mouz":
            mouz_fk_x.append(rx)
            mouz_fk_y.append(ry)
            mouz_win += 1

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('#0a0a0f')
    ax.set_facecolor('#0a0a0f')

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
        ax.imshow(img, extent=[0, w, h, 0], zorder=1, alpha=0.8)
    else:
        w, h = 1024, 1024

    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)

    # Mongolz first kill цэгүүд
    if mongolz_fk_x:
        ax.scatter(mongolz_fk_x, mongolz_fk_y,
                   c='#FFD700', s=180, alpha=0.9,
                   edgecolors='white', linewidths=0.8,
                   label=f'Mongolz first kill ({mongolz_win})',
                   zorder=4, marker='*')

    # mouz first kill цэгүүд
    if mouz_fk_x:
        ax.scatter(mouz_fk_x, mouz_fk_y,
                   c='#FF4444', s=180, alpha=0.9,
                   edgecolors='white', linewidths=0.8,
                   label=f'mouz first kill ({mouz_win})',
                   zorder=4, marker='*')

    # Stat текст
    total = mongolz_win + mouz_win
    mongolz_pct = int(mongolz_win / total * 100) if total else 0
    mouz_pct    = int(mouz_win    / total * 100) if total else 0

    ax.text(w - 20, 30,
            f'★ Mongolz  {mongolz_win} FK  ({mongolz_pct}%)',
            color='#FFD700', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#0a0a0f', alpha=0.75, edgecolor='none'))
    ax.text(w - 20, 65,
            f'★ mouz  {mouz_win} FK  ({mouz_pct}%)',
            color='#FF4444', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#0a0a0f', alpha=0.75, edgecolor='none'))

    ax.set_title(f"First Kill Map — {total} rounds  |  Mongolz vs mouz",
                 color='white', fontsize=14, pad=12)
    ax.axis('off')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#0a0a0f')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
