#!/usr/bin/env python3
import sys, os, json
import matplotlib.pyplot as plt
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

TEAM_PLAYERS = {
    "Mongolz": {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"},
    "mouz":    {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"},
}

def world_to_radar(wx, wy, pos_x, pos_y, scale):
    return (wx - pos_x) / scale, (pos_y - wy) / scale

def get_team(name):
    for team, players in TEAM_PLAYERS.items():
        if name in players:
            return team
    return "Unknown"

def main():
    if len(sys.argv) < 3:
        sys.exit(2)

    json_path, output_path = sys.argv[1], sys.argv[2]

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    map_name = data.get('map', 'de_mirage')
    params = MAP_PARAMS.get(map_name, MAP_PARAMS['de_mirage'])

    raw = data.get('kills', [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw

    mongolz_x, mongolz_y = [], []
    mouz_x, mouz_y = [], []

    for k in kills:
        if not isinstance(k, dict) or k.get('weapon') != 'awp':
            continue
        wx = k.get('attacker_X') or k.get('attacker_x')
        wy = k.get('attacker_Y') or k.get('attacker_y')
        name = k.get('attacker_name', '')
        if wx is None or wy is None:
            continue
        try:
            rx, ry = world_to_radar(float(wx), float(wy),
                                    params['pos_x'], params['pos_y'], params['scale'])
            team = get_team(name)
            if team == "Mongolz":
                mongolz_x.append(rx)
                mongolz_y.append(ry)
            elif team == "mouz":
                mouz_x.append(rx)
                mouz_y.append(ry)
        except ValueError:
            pass

    map_file = f"/data/scripts/maps/{map_name}.png"
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
        ax.imshow(img, extent=[0, w, h, 0])
    else:
        w, h = 1024, 1024

    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)

    if mongolz_x:
        ax.scatter(mongolz_x, mongolz_y, c='#FFD700', s=150, alpha=0.9,
                   edgecolors='white', linewidths=0.8,
                   label=f'Mongolz ({len(mongolz_x)})', zorder=3, marker='*')
    if mouz_x:
        ax.scatter(mouz_x, mouz_y, c='#FF4444', s=120, alpha=0.9,
                   edgecolors='white', linewidths=0.8,
                   label=f'mouz ({len(mouz_x)})', zorder=3, marker='*')

    total = len(mongolz_x) + len(mouz_x)

    # Текст legend
    ax.text(w - 20, 30, f'★ Mongolz  {len(mongolz_x)} AWP kill',
            color='#FFD700', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#1e1e1e', alpha=0.7, edgecolor='none'))
    ax.text(w - 20, 65, f'★ mouz  {len(mouz_x)} AWP kill',
            color='#FF4444', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#1e1e1e', alpha=0.7, edgecolor='none'))

    ax.set_title(f"AWP Positions — {total} kills  |  Mongolz vs mouz",
                 color='white', fontsize=13, pad=10)
    ax.axis('off')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', dpi=150, facecolor='#1e1e1e')
    plt.close()
    print(f"Success: {output_path}")

if __name__ == "__main__":
    main()
