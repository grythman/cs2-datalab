#!/usr/bin/env python3
import json
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
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

TEAM_COLORS = {
    "Mongolz": "#FFD34D",
    "mouz": "#FF6A6A",
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
    image = ImageEnhance.Sharpness(image).enhance(1.16)
    blurred = image.filter(ImageFilter.GaussianBlur(radius=3))
    base = Image.blend(blurred, image, 0.95)
    return base, base.size[0], base.size[1]


def draw_header(fig, map_name, total_awp, mongolz_awp, mouz_awp):
    fig.text(0.055, 0.955, "CS2 DATA LAB", color="#7FDBFF", fontsize=13, fontweight="bold")
    fig.text(0.055, 0.925, f"AWP CONTROL  •  {map_name.upper()}", color="white", fontsize=18, fontweight="bold")
    fig.text(0.945, 0.952, f"TOTAL {total_awp}", color="#C8D1DC", fontsize=12, ha="right", fontweight="bold")
    fig.text(0.055, 0.045, f"MONGOLZ {mongolz_awp}", color="#FFD34D", fontsize=11, fontweight="bold")
    fig.text(0.225, 0.045, f"MOUZ {mouz_awp}", color="#FF6A6A", fontsize=11, fontweight="bold")
    fig.text(0.945, 0.045, "Larger glow = stronger sniper presence", color="#93A1B5", fontsize=10, ha="right")


def annotate_hotspot(ax, points, color, label):
    if not points:
        return
    xs, ys = zip(*points)
    center_x = float(np.mean(xs))
    center_y = float(np.mean(ys))
    ax.scatter([center_x], [center_y], s=230, facecolors="none", edgecolors=color, linewidths=2.2, alpha=0.95, zorder=6)
    ax.scatter([center_x], [center_y], s=56, c=color, alpha=0.95, zorder=7)
    ax.text(
        center_x + 18,
        center_y - 18,
        label,
        color="white",
        fontsize=10,
        ha="left",
        va="top",
        bbox=dict(facecolor=(0.05, 0.07, 0.10, 0.88), edgecolor=color, boxstyle="round,pad=0.35"),
        zorder=8,
    )


def density_map(points, width, height, bins=72, sigma=3.2):
    if len(points) < 2:
        return None
    xs, ys = zip(*points)
    hist, _, _ = np.histogram2d(xs, ys, bins=bins, range=[[0, width], [0, height]])
    hist = gaussian_filter(hist.T, sigma=sigma)
    if np.nanmax(hist) <= 0:
        return None
    hist[hist < np.nanmax(hist) * 0.07] = np.nan
    return hist


def main():
    if len(sys.argv) < 3:
        sys.exit(2)

    json_path, output_path = sys.argv[1], sys.argv[2]

    with open(json_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)

    map_name = data.get("map", "de_mirage")
    params = MAP_PARAMS.get(map_name, MAP_PARAMS["de_mirage"])
    raw = data.get("kills", [])
    kills = raw[0][1] if raw and isinstance(raw[0], list) and len(raw[0]) > 1 else raw

    team_points = {"Mongolz": [], "mouz": []}

    for kill in kills:
        if not isinstance(kill, dict) or kill.get("weapon") != "awp":
            continue
        wx = kill.get("attacker_X") or kill.get("attacker_x")
        wy = kill.get("attacker_Y") or kill.get("attacker_y")
        if wx is None or wy is None:
            continue
        try:
            rx, ry = world_to_radar(float(wx), float(wy), params["pos_x"], params["pos_y"], params["scale"])
        except ValueError:
            continue
        team = get_team(kill.get("attacker_name", ""))
        if team in team_points:
            team_points[team].append((rx, ry))

    map_file = f"/data/scripts/maps/{map_name}.png"
    map_img, width, height = load_map_image(map_file)

    fig = plt.figure(figsize=(10.6, 10.6), facecolor="#06080D")
    ax = fig.add_axes([0.045, 0.085, 0.91, 0.84])
    ax.set_facecolor("#070A11")

    if map_img:
        ax.imshow(map_img, extent=[0, width, height, 0], zorder=1, alpha=0.99)

    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)

    for team, points in team_points.items():
        if not points:
            continue
        color = TEAM_COLORS[team]
        density = density_map(points, width, height)
        if density is not None:
            cmap = plt.matplotlib.colors.LinearSegmentedColormap.from_list(
                f"{team}_awp",
                ["#000000", color],
                N=256,
            )
            ax.imshow(
                density,
                extent=[0, width, height, 0],
                origin="upper",
                cmap=cmap,
                alpha=0.22 if team == "Mongolz" else 0.18,
                zorder=2,
                aspect="auto",
            )

        xs, ys = zip(*points)
        ax.scatter(
            xs,
            ys,
            c=color,
            s=110 if team == "Mongolz" else 98,
            alpha=0.9,
            edgecolors="white",
            linewidths=0.9,
            marker="*",
            zorder=4,
        )
        ax.scatter(
            xs,
            ys,
            c=color,
            s=320,
            alpha=0.08,
            edgecolors="none",
            zorder=3,
        )

        annotate_hotspot(ax, points, color, f"{team}\nAWP Lane")

    total_awp = len(team_points["Mongolz"]) + len(team_points["mouz"])
    draw_header(fig, map_name, total_awp, len(team_points["Mongolz"]), len(team_points["mouz"]))

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#111826")
        spine.set_linewidth(2)

    ax.set_xticks([])
    ax.set_yticks([])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=180, facecolor="#06080D", bbox_inches="tight", pad_inches=0.18)
    plt.close()
    print(f"Success: {output_path}")


if __name__ == "__main__":
    main()
