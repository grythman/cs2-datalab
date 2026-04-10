#!/usr/bin/env python3
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageEnhance, ImageFilter
from scipy.ndimage import gaussian_filter

MAP_PARAMS = {
    "de_mirage": {"pos_x": -3230, "pos_y": 1713, "scale": 5.0},
    "de_inferno": {"pos_x": -2087, "pos_y": 3870, "scale": 4.9},
    "de_dust2": {"pos_x": -2476, "pos_y": 3239, "scale": 4.4},
    "de_ancient": {"pos_x": -2953, "pos_y": 2164, "scale": 5.0},
    "de_anubis": {"pos_x": -2796, "pos_y": 3328, "scale": 5.22},
    "de_nuke": {"pos_x": -3453, "pos_y": 2887, "scale": 7.0},
    "de_overpass": {"pos_x": -4831, "pos_y": 1781, "scale": 5.2},
    "de_vertigo": {"pos_x": -3168, "pos_y": 1762, "scale": 4.0},
}

TEAM_PLAYERS = {
    "Mongolz": {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"},
    "mouz": {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"},
}


def world_to_radar(wx, wy, pos_x, pos_y, scale):
    return (wx - pos_x) / scale, (pos_y - wy) / scale


def get_team(name):
    for team, players in TEAM_PLAYERS.items():
        if name in players:
            return team
    return "Unknown"


def load_map_image(map_file):
    if not os.path.exists(map_file):
        return None, 1024, 1024

    image = Image.open(map_file).convert("RGBA")
    image = ImageEnhance.Contrast(image).enhance(1.18)
    image = ImageEnhance.Color(image).enhance(0.96)
    image = ImageEnhance.Brightness(image).enhance(1.04)
    image = ImageEnhance.Sharpness(image).enhance(1.18)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=3))
    base = Image.blend(blurred, image, 0.94)
    return base, base.size[0], base.size[1]


def add_hotspot_badge(ax, hotspot_x, hotspot_y, hotspot_value):
    ax.scatter(
        [hotspot_x],
        [hotspot_y],
        s=240,
        facecolors="none",
        edgecolors="#FFF2A8",
        linewidths=2.2,
        alpha=0.95,
        zorder=5,
    )
    ax.scatter(
        [hotspot_x],
        [hotspot_y],
        s=60,
        c="#FFF2A8",
        alpha=0.95,
        zorder=6,
    )
    ax.text(
        hotspot_x + 18,
        hotspot_y - 18,
        f"Hot Zone\n{hotspot_value:.0f} intensity",
        color="white",
        fontsize=10,
        ha="left",
        va="top",
        bbox=dict(facecolor=(0.05, 0.07, 0.10, 0.88), edgecolor="#FFD34D", boxstyle="round,pad=0.35"),
        zorder=7,
    )


def draw_header(fig, map_name, total_kills, mongolz_kills, mouz_kills):
    fig.text(0.055, 0.955, "CS2 DATA LAB", color="#FFD34D", fontsize=13, fontweight="bold")
    fig.text(0.055, 0.925, f"KILL HEATMAP  •  {map_name.upper()}", color="white", fontsize=18, fontweight="bold")
    fig.text(
        0.945,
        0.952,
        f"TOTAL {total_kills}",
        color="#C8D1DC",
        fontsize=12,
        ha="right",
        fontweight="bold",
    )
    fig.text(0.055, 0.045, f"MONGOLZ {mongolz_kills}", color="#FFD34D", fontsize=11, fontweight="bold")
    fig.text(0.225, 0.045, f"MOUZ {mouz_kills}", color="#FF6A6A", fontsize=11, fontweight="bold")
    fig.text(0.945, 0.045, "Higher density = brighter core", color="#93A1B5", fontsize=10, ha="right")


def main():
    if len(sys.argv) < 4:
        sys.exit(2)

    input_file, map_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(input_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    map_name = data.get("map", "de_mirage")
    params = MAP_PARAMS.get(map_name, MAP_PARAMS["de_mirage"])

    raw = data.get("kills", [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw

    all_x, all_y = [], []
    mongolz_x, mongolz_y = [], []
    mouz_x, mouz_y = [], []

    for kill in kills:
        if not isinstance(kill, dict):
            continue
        wx = kill.get("attacker_X") or kill.get("attacker_x")
        wy = kill.get("attacker_Y") or kill.get("attacker_y")
        name = kill.get("attacker_name", "")
        if wx is None or wy is None:
            continue
        try:
            rx, ry = world_to_radar(float(wx), float(wy), params["pos_x"], params["pos_y"], params["scale"])
        except ValueError:
            continue

        all_x.append(rx)
        all_y.append(ry)
        team = get_team(name)
        if team == "Mongolz":
            mongolz_x.append(rx)
            mongolz_y.append(ry)
        elif team == "mouz":
            mouz_x.append(rx)
            mouz_y.append(ry)

    map_img, width, height = load_map_image(map_file)

    fig = plt.figure(figsize=(10.6, 10.6), facecolor="#06080D")
    ax = fig.add_axes([0.045, 0.085, 0.91, 0.84])
    ax.set_facecolor("#070A11")

    if map_img:
        ax.imshow(map_img, extent=[0, width, height, 0], zorder=1, alpha=0.98)

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)

    if len(all_x) > 1:
        bins = 72
        heatmap, _, _ = np.histogram2d(all_x, all_y, bins=bins, range=[[0, width], [0, height]])
        heatmap = gaussian_filter(heatmap.T, sigma=3.0)
        heatmap = np.power(heatmap, 0.92)
        low_cut = heatmap.max() * 0.04
        heatmap[heatmap < low_cut] = np.nan

        glow_cmap = LinearSegmentedColormap.from_list(
            "cs2heat_glow",
            ["#031321", "#0A4ED7", "#00C4FF", "#32FF7E", "#FFE600", "#FF7A00", "#FF1E1E"],
            N=512,
        )

        contour_data = np.nan_to_num(heatmap, nan=0.0)
        ax.imshow(
            heatmap,
            extent=[0, width, height, 0],
            origin="upper",
            cmap=glow_cmap,
            alpha=0.44,
            zorder=2,
            aspect="auto",
        )
        ax.contour(
            contour_data,
            levels=4,
            colors=["#A9DCFF", "#F8FF9A", "#FFD56B", "#FF7A3D"],
            linewidths=0.8,
            alpha=0.42,
            extent=[0, width, height, 0],
            origin="upper",
            zorder=3,
        )

        max_idx = np.unravel_index(np.nanargmax(heatmap), heatmap.shape)
        hotspot_y = (max_idx[0] + 0.5) * (height / bins)
        hotspot_x = (max_idx[1] + 0.5) * (width / bins)
        add_hotspot_badge(ax, hotspot_x, hotspot_y, np.nanmax(heatmap))

    ax.scatter(
        mongolz_x,
        mongolz_y,
        c="#FFD34D",
        s=10,
        alpha=0.18,
        edgecolors="none",
        zorder=4,
    )
    ax.scatter(
        mouz_x,
        mouz_y,
        c="#FF6A6A",
        s=10,
        alpha=0.18,
        edgecolors="none",
        zorder=4,
    )

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#111826")
        spine.set_linewidth(2)

    ax.set_xticks([])
    ax.set_yticks([])
    draw_header(fig, map_name, len(all_x), len(mongolz_x), len(mouz_x))

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, dpi=180, facecolor="#06080D", bbox_inches="tight", pad_inches=0.18)
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)


if __name__ == "__main__":
    main()
