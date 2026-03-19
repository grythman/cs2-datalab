import json
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import os
import sys

# grythman/cs2-automation дээрх нарийвчилсан утгууд
MAP_CONFIGS = {
    "de_mirage": {
        "radar_image_path": "visuals/de_mirage_radar.png",
        "pos_x": -3230,
        "pos_y": 1713,
        "scale": 5.0,
    },
    "de_inferno": {
        "radar_image_path": "visuals/de_inferno_radar.png",
        "pos_x": -2087,
        "pos_y": 3870,
        "scale": 4.9,
    }
}

def generate_heatmap(json_file_path, output_image_path):
    with open(json_file_path, 'r') as f:
        data = json.load(f)

    map_name = data.get("map", "UNKNOWN")
    kills = data.get("kills", [])
    config = MAP_CONFIGS.get(map_name)

    if not config or not os.path.exists(config["radar_image_path"]):
        print(f"Алдаа: {map_name} тохиргоо эсвэл зураг олдсонгүй.")
        return

    radar_img = mpimg.imread(config["radar_image_path"])
    
    # Координат хөрвүүлэлт
    x_pixels = [(k["user_x"] - config["pos_x"]) / config["scale"] for k in kills if "user_x" in k]
    y_pixels = [(config["pos_y"] - k["user_y"]) / config["scale"] for k in kills if "user_y" in k]

    fig, ax = plt.subplots(figsize=(12, 12))
    ax.imshow(radar_img)
    
    # Heatmap - Цэгүүдийн нягтралыг өнгөөр харуулах
    if x_pixels:
        # cmap='hot' эсвэл 'inferno' нь CS2-т маш гоё харагддаг
        hb = ax.hexbin(x_pixels, y_pixels, gridsize=40, cmap='inferno', alpha=0.8, mincnt=1)
        plt.colorbar(hb, ax=ax, label='Алалтын тоо')
    
    ax.axis('off')
    plt.title(f"CS2 Data Lab: {map_name} Heatmap", color='white', fontsize=15)
    fig.patch.set_facecolor('#1a1a1a') # YouTube-д зориулсан бараан дэвсгэр
    
    plt.savefig(output_image_path, bbox_inches='tight', pad_inches=0, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Heatmap бэлэн боллоо: {output_image_path}")

if __name__ == "__main__":
    generate_heatmap(sys.argv[1], sys.argv[2])
