#!/usr/bin/env python3
import sys, os, json
import numpy as np
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

    # Тус бүр баг → round-ын эхний kill байрлал
    mongolz_entry = []  # T entry цэгүүд
    mouz_entry    = []  # mouz entry цэгүүд
    mongolz_defense = []
    mouz_defense    = []

    for r in rounds:
        first = r[0]
        attacker = first.get('attacker_name', '')
        victim   = first.get('user_name', '')
        wx_a = first.get('attacker_X')
        wy_a = first.get('attacker_Y')
        wx_v = first.get('user_X')
        wy_v = first.get('user_Y')

        if wx_a and wy_a:
            rx, ry = world_to_radar(float(wx_a), float(wy_a),
                                    params['pos_x'], params['pos_y'], params['scale'])
            team = get_team(attacker)
            if team == "Mongolz":
                mongolz_entry.append((rx, ry))
            elif team == "mouz":
                mouz_entry.append((rx, ry))

        if wx_v and wy_v:
            rx, ry = world_to_radar(float(wx_v), float(wy_v),
                                    params['pos_x'], params['pos_y'], params['scale'])
            victim_team = get_team(victim)
            if victim_team == "Mongolz":
                mongolz_defense.append((rx, ry))
            elif victim_team == "mouz":
                mouz_defense.append((rx, ry))

    # 2 panel зураг
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))
    fig.patch.set_facecolor('#0a0a0f')

    titles = ["MONGOLZ тактикийн зам", "MOUZ тактикийн зам"]
    entries = [mongolz_entry, mouz_entry]
    defenses = [mouz_defense, mongolz_defense]
    colors_e = ['#FFD700', '#FF4444']
    colors_d = ['#FF4444', '#FFD700']
    labels_e = ['Mongolz entry', 'mouz entry']
    labels_d = ['mouz defense', 'Mongolz defense']

    for idx, ax in enumerate(axes):
        ax.set_facecolor('#0a0a0f')

        if os.path.exists(map_file):
            img = Image.open(map_file).convert("RGBA")
            w, h = img.size
            ax.imshow(img, extent=[0, w, h, 0], zorder=1, alpha=0.85)
        else:
            w, h = 1024, 1024

        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)

        # Defense цэгүүд — жижиг дугуй
        if defenses[idx]:
            dx = [p[0] for p in defenses[idx]]
            dy = [p[1] for p in defenses[idx]]
            ax.scatter(dx, dy, c=colors_d[idx], s=80, alpha=0.5,
                      edgecolors='white', linewidths=0.3,
                      label=labels_d[idx], zorder=2, marker='o')

        # Entry цэгүүд — од хэлбэр, том
        if entries[idx]:
            ex = [p[0] for p in entries[idx]]
            ey = [p[1] for p in entries[idx]]
            ax.scatter(ex, ey, c=colors_e[idx], s=200, alpha=0.9,
                      edgecolors='white', linewidths=0.5,
                      label=labels_e[idx], zorder=4, marker='*')

            # Хамгийн их давтагдсан газрыг тэмдэглэх
            from collections import Counter
            grid_size = 80
            grid_counts = Counter()
            for x, y in entries[idx]:
                gx, gy = int(x // grid_size), int(y // grid_size)
                grid_counts[(gx, gy)] += 1

            if grid_counts:
                hot_gx, hot_gy = grid_counts.most_common(1)[0][0]
                hot_x = hot_gx * grid_size + grid_size // 2
                hot_y = hot_gy * grid_size + grid_size // 2
                ax.add_patch(plt.Circle((hot_x, hot_y), 55,
                             color=colors_e[idx], alpha=0.25, zorder=3))
                ax.add_patch(plt.Circle((hot_x, hot_y), 55,
                             fill=False, edgecolor=colors_e[idx],
                             linewidth=2, zorder=3))

        legend = ax.legend(facecolor='#1e1e1e', labelcolor='white',
                          fontsize=11, loc='upper right', framealpha=0.85)

        ax.set_title(titles[idx], color='white', fontsize=15,
                    fontweight='bold', pad=12)
        ax.axis('off')

    plt.suptitle(f"Тактикийн шинжилгээ — {map_name.upper()}  |  ★ = Entry  ● = Defense",
                color='white', fontsize=13, y=0.02)

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#0a0a0f')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
