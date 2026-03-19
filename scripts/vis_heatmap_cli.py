#!/usr/bin/env python3
import sys, os, json
import numpy as np
import matplotlib.pyplot as plt
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

def world_to_radar(wx, wy, pos_x, pos_y, scale):
    rx = (wx - pos_x) / scale
    ry = (pos_y - wy) / scale
    return rx, ry

def main():
    if len(sys.argv) < 4:
        print("Usage: vis_heatmap_cli.py <input.json> <map.png> <output.png>")
        sys.exit(2)

    input_file, map_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    map_name = data.get('map', 'de_mirage')
    params = MAP_PARAMS.get(map_name, MAP_PARAMS['de_mirage'])

    raw = data.get('kills', [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw

    x_coords, y_coords = [], []
    for k in kills:
        if isinstance(k, dict):
            wx = k.get('attacker_X') or k.get('attacker_x')
            wy = k.get('attacker_Y') or k.get('attacker_y')
            if wx is not None and wy is not None:
                try:
                    rx, ry = world_to_radar(float(wx), float(wy),
                                            params['pos_x'], params['pos_y'], params['scale'])
                    x_coords.append(rx)
                    y_coords.append(ry)
                except ValueError:
                    pass

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor('#1e1e1e')
    ax.set_facecolor('#1e1e1e')

    if os.path.exists(map_file):
        img = Image.open(map_file).convert("RGBA")
        w, h = img.size
        ax.imshow(img, extent=[0, w, h, 0])
        ax.set_xlim(0, w)
        ax.set_ylim(h, 0)
    else:
        ax.set_xlim(0, 1024)
        ax.set_ylim(1024, 0)
        w, h = 1024, 1024

    if x_coords and y_coords:
        ax.hexbin(x_coords, y_coords, gridsize=40, cmap='inferno',
                  mincnt=1, alpha=0.75, extent=[0, w, 0, h])
    else:
        ax.text(0.5, 0.5, 'No valid coordinates found',
                color='white', ha='center', va='center', transform=ax.transAxes)

    ax.set_title(f"Match Heatmap - {len(x_coords)} Events", color='white')
    ax.axis('off')

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#1e1e1e')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
