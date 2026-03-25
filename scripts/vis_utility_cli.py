#!/usr/bin/env python3
import sys, os, json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
import numpy as np
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

def draw_heatmap(ax, points, w, h, color, alpha=0.5):
    if len(points) < 2:
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    heatmap, _, _ = np.histogram2d(xs, ys, bins=40, range=[[0, w], [0, h]])
    heatmap = gaussian_filter(heatmap.T, sigma=3.0)
    heatmap[heatmap < heatmap.max() * 0.1] = np.nan
    cmap = LinearSegmentedColormap.from_list('util', ['#000000', color], N=256)
    ax.imshow(heatmap, extent=[0, w, h, 0], origin='upper',
              cmap=cmap, alpha=alpha, zorder=2, aspect='auto')

def main():
    if len(sys.argv) < 4:
        sys.exit(2)

    input_file, map_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    map_name = data.get('map', 'de_mirage')
    params = MAP_PARAMS.get(map_name, MAP_PARAMS['de_mirage'])
    utility = data.get('utility', {})

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
    else:
        w, h = 1024, 1024
        img = None

    # 4 panel: Flash, Smoke, HE, Inferno
    fig, axes = plt.subplots(2, 2, figsize=(20, 20))
    fig.patch.set_facecolor('#0a0a0f')

    panels = [
        ("flashbang_detonate",   "FLASH",   "#00BFFF", axes[0][0]),
        ("smokegrenade_detonate","SMOKE",   "#90EE90", axes[0][1]),
        ("hegrenade_detonate",   "HE GRENADE", "#FF6347", axes[1][0]),
        ("inferno_startburn",    "MOLOTOV / INCENDIARY", "#FF4500", axes[1][1]),
    ]

    for event_key, title, color, ax in panels:
        ax.set_facecolor('#0a0a0f')

        if img:
            ax.imshow(img, extent=[0, w, h, 0], zorder=1, alpha=0.75)
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)

        rows = utility.get(event_key, [])

        mongolz_pts = []
        mouz_pts    = []
        all_pts     = []

        for r in rows:
            wx = r.get('x')
            wy = r.get('y')
            name = r.get('user_name', '')
            if wx is None or wy is None:
                continue
            rx, ry = world_to_radar(float(wx), float(wy),
                                    params['pos_x'], params['pos_y'], params['scale'])
            all_pts.append((rx, ry))
            team = get_team(name)
            if team == "Mongolz":
                mongolz_pts.append((rx, ry))
            elif team == "mouz":
                mouz_pts.append((rx, ry))

        # Heatmap
        draw_heatmap(ax, all_pts, w, h, color, alpha=0.5)

        # Цэгүүд багаар
        if mongolz_pts:
            ax.scatter([p[0] for p in mongolz_pts],
                      [p[1] for p in mongolz_pts],
                      c='#FFD700', s=35, alpha=0.8,
                      edgecolors='#0a0a0f', linewidths=0.3, zorder=4)
        if mouz_pts:
            ax.scatter([p[0] for p in mouz_pts],
                      [p[1] for p in mouz_pts],
                      c='#FF4444', s=35, alpha=0.8,
                      edgecolors='#0a0a0f', linewidths=0.3, zorder=4)

        # Legend текст
        ax.text(w - 15, 25,
                f'🟡 Mongolz {len(mongolz_pts)}   🔴 mouz {len(mouz_pts)}',
                color='white', fontsize=11, ha='right', va='top',
                bbox=dict(facecolor='#0a0a0f', alpha=0.75, edgecolor='none'))

        ax.set_title(f"{title} — {len(all_pts)} total",
                    color='white', fontsize=14, fontweight='bold', pad=10)
        ax.axis('off')

    plt.suptitle(f"Utility Map — {map_name.upper()}  |  Mongolz vs mouz",
                color='white', fontsize=16, y=0.02)
    plt.tight_layout(rect=[0, 0.03, 1, 1])

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#0a0a0f')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
