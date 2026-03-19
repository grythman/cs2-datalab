#!/usr/bin/env python3
import sys
import os
import json
import matplotlib.pyplot as plt

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 vis_heatmap_cli.py <input.json> <map_image.png> <output.png>")
        sys.exit(2)

    input_file = sys.argv[1]
    map_file = sys.argv[2]
    output_file = sys.argv[3]

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        sys.exit(2)

    try:
        # JSON өгөгдлийг унших
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Өгөгдлийн бүтцийг автоматаар таних
        if isinstance(data, list):
            kills = data
        else:
            kills = data.get('kills', [])

        x_coords, y_coords = [], []
        
        # Координатуудыг цуглуулах
        for k in kills:
            if isinstance(k, dict):
                x, y = k.get('x'), k.get('y')
                if x is not None and y is not None:
                    try:
                        x_coords.append(float(x))
                        y_coords.append(float(y))
                    except ValueError:
                        pass

        # Зураг зурах (Plotting)
        fig, ax = plt.subplots(figsize=(10, 10))

        # Газрын зураг байгаа эсэхийг шалгах, байвал дэвсгэр болгох
        if os.path.exists(map_file):
            img = plt.imread(map_file)
            # Mirage газрын зургийн стандарт хязгаар (bounds)
            ax.imshow(img, extent=[-3230, 1710, -3360, 1270])
        else:
            print(f"Warning: Map image {map_file} not found. Drawing without background.")
            ax.set_facecolor('#1e1e1e') # Хар саарал дэвсгэр

        if x_coords and y_coords:
            # Heatmap зурах (Hexbin ашиглах)
            ax.hexbin(x_coords, y_coords, gridsize=40, cmap='inferno', mincnt=1, alpha=0.7)
        else:
            ax.text(0.5, 0.5, 'No valid coordinates found', color='white', ha='center', va='center', transform=ax.transAxes)

        ax.set_title(f"Match Heatmap - {len(x_coords)} Events", color='white')
        ax.set_xlim(-3230, 1710)
        ax.set_ylim(-3360, 1270)
        ax.axis('off')

        # Хадгалах
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#1e1e1e')
        plt.close()

        print(f"Success: Heatmap saved to {output_file}")
        sys.exit(0)

    except Exception as e:
        print(f"Error generating heatmap: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
