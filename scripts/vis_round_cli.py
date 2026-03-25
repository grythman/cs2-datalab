#!/usr/bin/env python3
import sys, os, json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
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
    if len(sys.argv) < 5:
        print("Usage: vis_round_cli.py <input.json> <map.png> <output.png> <round_num>")
        sys.exit(2)

    input_file = sys.argv[1]
    map_file   = sys.argv[2]
    output_file = sys.argv[3]
    target_round = int(sys.argv[4])

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

    if target_round < 1 or target_round > len(rounds):
        print(f"Round {target_round} байхгүй. Нийт: {len(rounds)}")
        sys.exit(1)

    round_kills = rounds[target_round - 1]

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
    else:
        w, h = 1024, 1024
        img = None

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('#0a0a0f')
    ax.set_facecolor('#0a0a0f')

    if img:
        ax.imshow(img, extent=[0, w, h, 0], zorder=1, alpha=0.8)

    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)

    # Kill бүрийг дараалалаар харуулах
    for i, k in enumerate(round_kills):
        wx_a = k.get('attacker_X')
        wy_a = k.get('attacker_Y')
        wx_v = k.get('user_X')
        wy_v = k.get('user_Y')
        attacker = k.get('attacker_name', '')
        victim   = k.get('user_name', '')
        weapon   = k.get('weapon', '')
        headshot = k.get('headshot', False)

        if not all([wx_a, wy_a, wx_v, wy_v]):
            continue

        ax_r, ay_r = world_to_radar(float(wx_a), float(wy_a),
                                     params['pos_x'], params['pos_y'], params['scale'])
        vx_r, vy_r = world_to_radar(float(wx_v), float(wy_v),
                                     params['pos_x'], params['pos_y'], params['scale'])

        a_team = get_team(attacker)
        v_team = get_team(victim)

        a_color = '#FFD700' if a_team == "Mongolz" else '#FF4444'
        v_color = '#FFD700' if v_team == "Mongolz" else '#FF4444'

        # Attacker — од
        ax.scatter(ax_r, ay_r, c=a_color, s=200, alpha=0.95,
                   edgecolors='white', linewidths=0.8,
                   marker='*', zorder=4)

        # Victim — X тэмдэг
        ax.scatter(vx_r, vy_r, c=v_color, s=120, alpha=0.9,
                   edgecolors='white', linewidths=0.8,
                   marker='X', zorder=4)

        # Буудсан шугам
        ax.annotate("", xy=(vx_r, vy_r), xytext=(ax_r, ay_r),
                    arrowprops=dict(arrowstyle="-|>",
                                   color=a_color,
                                   alpha=0.6,
                                   lw=1.2), zorder=3)

        # Kill дугаар
        mid_x = (ax_r + vx_r) / 2
        mid_y = (ay_r + vy_r) / 2
        hs = "💀" if headshot else ""
        ax.text(mid_x, mid_y, f"{i+1}{hs}",
                color='white', fontsize=9, ha='center', va='center',
                bbox=dict(facecolor='#0a0a0f', alpha=0.6, edgecolor='none'),
                zorder=5)

    # Legend
    ax.scatter([], [], c='#FFD700', s=150, marker='*', label='Mongolz attacker')
    ax.scatter([], [], c='#FF4444', s=150, marker='*', label='mouz attacker')
    ax.scatter([], [], c='white', s=80, marker='X', label='Victim')
    ax.legend(facecolor='#1e1e1e', labelcolor='white',
              fontsize=11, loc='upper right', framealpha=0.85)

    # Kill жагсаалт — доод талд
    kill_text = "  →  ".join([
        f"{i+1}. {k.get('attacker_name','?')} ➜ {k.get('user_name','?')} ({k.get('weapon','')})"
        for i, k in enumerate(round_kills)
    ])
    ax.text(w/2, h - 10, kill_text,
            color='white', fontsize=8, ha='center', va='bottom',
            bbox=dict(facecolor='#0a0a0f', alpha=0.75, edgecolor='none'),
            wrap=True, zorder=5)

    ax.set_title(f"Round {target_round} — {len(round_kills)} kill  |  {map_name.upper()}",
                 color='white', fontsize=14, pad=12)
    ax.axis('off')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#0a0a0f')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
