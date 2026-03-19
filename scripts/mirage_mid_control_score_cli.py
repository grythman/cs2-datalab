#!/usr/bin/env python3
import json
import sys
import os

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 mirage_mid_control_score_cli.py <input.json> <output.json>")
        sys.exit(2)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. Өгөгдлийн бүтцийг автоматаар таних (List vs Dict)
        if isinstance(data, list):
            kills = data
            match_id = os.path.basename(input_file).replace('.json', '')
            map_name = "unknown"
        else:
            kills = data.get('kills', [])
            match_id = data.get('match_id', 'unknown')
            map_name = data.get('map', 'unknown')
        
        # 2. Координатыг аюулгүйгээр шалгаж тоолох
        mid_kills = 0
        valid_kills = 0
        
        for k in kills:
            if isinstance(k, dict):
                x = k.get('x')
                y = k.get('y')
                
                if x is not None and y is not None:
                    try:
                        x, y = float(x), float(y)
                        valid_kills += 1
                        # Mirage Mid бүсийн барцаг багцаалсан хязгаар
                        if -1000 < x < 1000 and -1000 < y < 1000:
                            mid_kills += 1
                    except ValueError:
                        pass

        total_kills = valid_kills if valid_kills > 0 else 1
        mid_pct = (mid_kills / total_kills) * 100

        features = {
            "match_id": match_id,
            "map": map_name,
            "total_kills": len(kills),
            "valid_kills_with_coords": valid_kills,
            "mid_kills": mid_kills,
            "mid_pct": round(mid_pct, 2),
            "tactical_assessment": "Strong Mid Presence" if mid_pct > 20 else "Weak Mid Presence"
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(features, f, indent=4)
            
        print(f"Successfully processed {valid_kills} valid kills out of {len(kills)}. Mid Control Score saved.")
        sys.exit(0)
        
    except Exception as e:
        print(f"Data processing error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
