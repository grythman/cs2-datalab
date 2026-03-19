import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import os

def main():
    try:
        if len(sys.argv) < 3:
            print("Usage: python3 visualize_awp_cli.py <json_path> <output_path>")
            sys.exit(1)

        json_path = sys.argv[1]
        output_path = sys.argv[2]

        if not os.path.exists(json_path):
            print(f"Error: JSON file not found at {json_path}")
            sys.exit(1)

        with open(json_path, 'r') as f:
            data = json.load(f)

        # УХААЛАГ ШҮҮЛТ: Data нь жагсаалт эсвэл хайрцаг байхаас үл хамааран kills-ийг олно
        kills = []
        if isinstance(data, list):
            # Хэрэв дата нь жагсаалт бол (Жишээ нь: раундуудын жагсаалт)
            for item in data:
                if isinstance(item, dict):
                    kills.extend(item.get('kills', []))
        elif isinstance(data, dict):
            # Хэрэв дата нь хайрцаг бол
            kills = data.get('kills', [])

        # Хэрэв kills дотроо өөрөө жагсаалт биш бол (цөөн тохиолдолд)
        if not isinstance(kills, list):
            kills = []

        awp_kills = [k for k in kills if isinstance(k, dict) and k.get('weapon') == 'awp']

        if not awp_kills:
            plt.figure(figsize=(10, 10))
            plt.text(0.5, 0.5, 'No AWP Kills Found', ha='center', fontsize=15)
            plt.savefig(output_path)
            print("Success: No AWP kills, created placeholder.")
            return

        # Координат авахдаа алдаанаас сэргийлэх
        coords = []
        for k in awp_kills:
            x = k.get('attacker_pos_x')
            y = k.get('attacker_pos_y')
            if x is not None and y is not None:
                coords.append({'x': x, 'y': y})

        if not coords:
            print("Error: AWP kills found but positions are missing.")
            sys.exit(1)

        df = pd.DataFrame(coords)

        # Зураг зурах
        plt.figure(figsize=(10, 10))
        plt.scatter(df['x'], df['y'], c='red', s=100, alpha=0.7, edgecolors='white', label='AWP Position')
        plt.title('AWP Attacker Map Positions')
        plt.grid(True, linestyle=':', alpha=0.5)
        plt.legend()
        
        plt.savefig(output_path)
        plt.close()
        print(f"Success: AWP visualization saved to {output_path}")

    except Exception as e:
        print(f"Runtime Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
