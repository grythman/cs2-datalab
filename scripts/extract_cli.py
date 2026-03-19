import argparse
from pathlib import Path
import json
import pandas as pd

from demoparser2 import DemoParser


def main():
    parser = argparse.ArgumentParser(description="Extract basic CS2 demo data")
    parser.add_argument("demo_file", help="Path to .dem file")
    parser.add_argument("output_csv", help="Path to output CSV")
    parser.add_argument("--summary-json", dest="summary_json", default=None, help="Optional summary JSON path")
    args = parser.parse_args()

    demo_path = Path(args.demo_file)
    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    if not demo_path.exists():
        raise FileNotFoundError(f"Demo file not found: {demo_path}")

    dp = DemoParser(str(demo_path))

    df = dp.parse_event(
        "player_death",
        player=["X", "Y", "team_name", "name"],
        other=["total_rounds_played"],
    )

    rename_map = {
        "user_name": "victim_name",
        "user_team_name": "victim_team",
        "user_X": "victim_x",
        "user_Y": "victim_y",
        "attacker_name": "attacker_name",
        "attacker_team_name": "attacker_team",
        "attacker_X": "attacker_x",
        "attacker_Y": "attacker_y",
    }

    for old, new in rename_map.items():
        if old in df.columns:
            df = df.rename(columns={old: new})

    wanted_cols = [c for c in [
        "tick",
        "total_rounds_played",
        "attacker_name",
        "attacker_team",
        "attacker_x",
        "attacker_y",
        "victim_name",
        "victim_team",
        "victim_x",
        "victim_y",
        "weapon",
        "headshot",
    ] if c in df.columns]

    if wanted_cols:
        df = df[wanted_cols]

    df.to_csv(out_csv, index=False)

    summary = {
        "demo_file": str(demo_path),
        "rows": int(len(df)),
        "columns": list(df.columns),
        "output_csv": str(out_csv),
    }

    if args.summary_json:
        summary_path = Path(args.summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
