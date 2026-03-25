#!/usr/bin/env python3
import sys, os, json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from scipy.ndimage import gaussian_filter
from PIL import Image

MAP_PARAMS = {
    "de_mirage":  {"pos_x": -3230, "pos_y": 1713,  "scale": 5.0},
    "de_inferno": {"pos_x": -2087, "pos_y": 3870,  "scale": 4.9},
    "de_dust2":   {"pos_x": -2476, "pos_y": 3239,  "scale": 4.4},
    "de_ancient": {"pos_x": -2953, "pos_y": 2164,  "scale": 5.0},
    "de_anubis":  {"pos_x": -2796, "pos_y": 3328,  "scale": 5.22},
    "de_nuke":    {"pos_x": -3453, "pos_y": 2887,  "scale": 7.0},
    "de_overpass":{"pos_x": -4831, "pos_y": 1781,  "scale": 5.2},
    "de_vertigo": {"pos_x": -3168, "pos_y": 1762,  "scale": 4.0},
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

    mongolz_x, mongolz_y = [], []
    mouz_x,    mouz_y    = [], []
    all_x,     all_y     = [], []

    for k in kills:
        if not isinstance(k, dict):
            continue
        # victim байрлал — user_X, user_Y
        wx = k.get('user_X') or k.get('user_x')
        wy = k.get('user_Y') or k.get('user_y')
        name = k.get('user_name', '')
        if wx is None or wy is None:
            continue
        try:
            rx, ry = world_to_radar(float(wx), float(wy),
                                    params['pos_x'], params['pos_y'], params['scale'])
            all_x.append(rx)
            all_y.append(ry)
            team = get_team(name)
            if team == "Mongolz":
                mongolz_x.append(rx)
                mongolz_y.append(ry)
            elif team == "mouz":
                mouz_x.append(rx)
                mouz_y.append(ry)
        except ValueError:
            pass

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
    else:
        w, h = 1024, 1024
        img = None

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')

    if img:
        ax.imshow(img, extent=[0, w, h, 0], zorder=1)

    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)

    # Death heatmap — нягтрал
    if len(all_x) > 1:
        heatmap, _, _ = np.histogram2d(all_x, all_y, bins=60,
                                        range=[[0, w], [0, h]])
        heatmap = gaussian_filter(heatmap.T, sigma=2.5)
        heatmap[heatmap < heatmap.max() * 0.05] = np.nan

        # Цэнхэр-ягаан өнгө — kill map-аас ялгаатай
        cmap = LinearSegmentedColormap.from_list(
            'deathmap', ['#000080', '#4B0082', '#8B00FF', '#FF00FF', '#FF1493'], N=256)

        ax.imshow(heatmap, extent=[0, w, h, 0], origin='upper',
                  cmap=cmap, alpha=0.55, zorder=2, aspect='auto')

    # Баг тус бүрийн үхлийн цэг
    if mongolz_x:
        ax.scatter(mongolz_x, mongolz_y, c='#FFD700', s=45, alpha=0.85,
                   edgecolors='#1e1e1e', linewidths=0.5,
                   zorder=4)
    if mouz_x:
        ax.scatter(mouz_x, mouz_y, c='#FF4444', s=45, alpha=0.85,
                   edgecolors='#1e1e1e', linewidths=0.5,
                   zorder=4)

    # Legend
    ax.text(w - 20, 30, f'🟡 Mongolz  {len(mongolz_x)} үхэл',
            color='#FFD700', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#1e1e1e', alpha=0.7, edgecolor='none'))
    ax.text(w - 20, 65, f'🔴 mouz  {len(mouz_x)} үхэл',
            color='#FF4444', fontsize=12, ha='right', va='top',
            bbox=dict(facecolor='#1e1e1e', alpha=0.7, edgecolor='none'))

    ax.set_title(f"Death Map — {len(all_x)} үхэл  |  Mongolz vs mouz",
                 color='white', fontsize=13, pad=10)
    ax.axis('off')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#1e1e1e')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
