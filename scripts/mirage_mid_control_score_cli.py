#!/usr/bin/env python3
import json
import os
import sys
from collections import Counter


def extract_rows(payload):
    if isinstance(payload, list) and payload:
        if isinstance(payload[0], list) and len(payload[0]) > 1 and isinstance(payload[0][1], list):
            return payload[0][1]
        return payload
    return []


def estimate_rounds(kills):
    ordered = sorted([kill for kill in kills if isinstance(kill, dict)], key=lambda item: item.get("tick", 0))
    if not ordered:
        return []
    rounds = []
    current = [ordered[0]]
    for kill in ordered[1:]:
        if kill.get("tick", 0) - current[-1].get("tick", 0) > 1000:
            rounds.append(current)
            current = [kill]
        else:
            current.append(kill)
    rounds.append(current)
    return rounds


def score_story_angles(match_id, map_name, kills, economy_rows, round_end_rows, mid_pct, mid_kills):
    rounds = estimate_rounds(kills)
    total_kills = max(len(kills), 1)

    weapon_counts = Counter(kill.get("weapon") for kill in kills if isinstance(kill, dict) and kill.get("weapon"))
    awp_kills = weapon_counts.get("awp", 0)
    awp_share = awp_kills / total_kills

    first_attackers = [round_kills[0].get("attacker_name", "Unknown") for round_kills in rounds if round_kills]
    first_attacker_counts = Counter(first_attackers)
    entry_player, entry_count = first_attacker_counts.most_common(1)[0] if first_attacker_counts else ("Unknown", 0)
    entry_share = entry_count / max(len(rounds), 1)

    equip_values = [row.get("user_current_equip_value") for row in economy_rows if isinstance(row, dict)]
    equip_values = [value for value in equip_values if isinstance(value, (int, float))]
    low_buy_count = sum(1 for value in equip_values if value < 2500)
    full_buy_count = sum(1 for value in equip_values if value >= 4500)
    economy_swing_score = (low_buy_count + full_buy_count) / max(len(equip_values), 1)

    round_winners = Counter(row.get("winner") for row in round_end_rows if isinstance(row, dict) and row.get("winner"))
    round_end_total = sum(round_winners.values())
    pressure_score = min(round_winners.values()) / round_end_total if round_winners and round_end_total else 0.0

    angles = [
        {
            "id": "mid_control_decided_map",
            "label": "Mid control decided the map",
            "score": round(mid_pct / 100, 3),
            "reason": f"{round(mid_pct, 2)}% of coordinate-valid kills came from Mirage mid pressure zones.",
            "evidence": {
                "mid_pct": round(mid_pct, 2),
                "mid_kills": mid_kills,
            },
        },
        {
            "id": "first_pick_set_tempo",
            "label": "First pick set the tempo",
            "score": round(entry_share, 3),
            "reason": f"{entry_player} opened {entry_count} of {max(len(rounds), 1)} estimated rounds.",
            "evidence": {
                "entry_player": entry_player,
                "entry_rounds": entry_count,
                "entry_share": round(entry_share, 3),
            },
        },
        {
            "id": "economy_broke_momentum",
            "label": "Economy broke the momentum",
            "score": round(economy_swing_score, 3),
            "reason": f"{low_buy_count} low-buy and {full_buy_count} full-buy snapshots show repeated gear swings.",
            "evidence": {
                "low_buy_count": low_buy_count,
                "full_buy_count": full_buy_count,
                "economy_samples": len(equip_values),
            },
        },
        {
            "id": "awp_locked_key_angles",
            "label": "AWP locked key angles",
            "score": round(awp_share, 3),
            "reason": f"AWP accounted for {awp_kills} kills out of {total_kills} total frags.",
            "evidence": {
                "awp_kills": awp_kills,
                "awp_share": round(awp_share, 3),
            },
        },
        {
            "id": "round_finish_pressure_mattered",
            "label": "Round finish pressure mattered",
            "score": round(pressure_score, 3),
            "reason": f"Round-end wins were split {dict(round_winners)} across the available rounds.",
            "evidence": {
                "round_winners": dict(round_winners),
                "estimated_rounds": len(rounds),
            },
        },
    ]

    ranked = sorted(angles, key=lambda item: item["score"], reverse=True)
    return {
        "match_id": match_id,
        "map": map_name,
        "primary_angle": ranked[0] if ranked else None,
        "story_angles": ranked[:3],
        "angle_summary": " | ".join(angle["label"] for angle in ranked[:3]),
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 mirage_mid_control_score_cli.py <input.json> <output.json>")
        sys.exit(2)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if isinstance(data, list):
            kills = extract_rows(data)
            match_id = os.path.basename(input_file).replace(".json", "")
            map_name = "unknown"
            economy_rows = []
            round_end_rows = []
        else:
            kills = extract_rows(data.get("kills", []))
            match_id = data.get("match_id", "unknown")
            map_name = data.get("map", "unknown")
            economy_rows = extract_rows(data.get("economy", []))
            round_end_rows = extract_rows(data.get("round_end", []))

        mid_kills = 0
        valid_kills = 0

        for kill in kills:
            if not isinstance(kill, dict):
                continue
            x = kill.get("attacker_X")
            y = kill.get("attacker_Y")
            if x is None or y is None:
                continue
            try:
                x = float(x)
                y = float(y)
            except (TypeError, ValueError):
                continue
            valid_kills += 1
            if -1000 < x < 1000 and -1000 < y < 1000:
                mid_kills += 1

        total_kills = valid_kills if valid_kills > 0 else 1
        mid_pct = (mid_kills / total_kills) * 100

        features = {
            "match_id": match_id,
            "map": map_name,
            "total_kills": len(kills),
            "valid_kills_with_coords": valid_kills,
            "mid_kills": mid_kills,
            "mid_pct": round(mid_pct, 2),
            "tactical_assessment": "Strong Mid Presence" if mid_pct > 20 else "Weak Mid Presence",
        }
        features.update(score_story_angles(match_id, map_name, kills, economy_rows, round_end_rows, mid_pct, mid_kills))

        with open(output_file, "w", encoding="utf-8") as handle:
            json.dump(features, handle, indent=4)

        print(f"Successfully processed {valid_kills} valid kills out of {len(kills)}. Tactical summary saved.")
        sys.exit(0)
    except Exception as exc:
        print(f"Data processing error: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
