import sys
import os
import json
from demoparser2 import DemoParser

def main():
    if len(sys.argv) < 2:
        print("Алдаа: Демо файлын нэрийг оруулна уу. Ж: match.dem")
        sys.exit(1)

    filename = sys.argv[1]
    raw_path = f"/data/raw/{filename}"
    parsed_path = f"/data/parsed/{filename}.json"

    if not os.path.exists(raw_path):
        print(f"Алдаа: Файл олдсонгүй -> {raw_path}")
        sys.exit(1)

    print(f"[{filename}] Парс хийж эхэллээ...")

    try:
        parser = DemoParser(raw_path)
        header = parser.parse_header()
        
        kills_df = parser.parse_events("player_death")
        kills_data = kills_df.to_dict(orient="records") if not kills_df.empty else []

        result = {
            "match_info": {
                "map": header.get("map_name", "unknown"),
                "server_name": header.get("server_name", "unknown"),
                "total_kills": len(kills_data)
            },
            "kills": kills_data
        }

        with open(parsed_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        print(f"Амжилттай! Үр дүн хадгалагдлаа: {parsed_path}")

    except Exception as e:
        print(f"Парс хийх үед алдаа гарлаа: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
