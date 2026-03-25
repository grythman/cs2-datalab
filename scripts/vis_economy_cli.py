#!/usr/bin/env python3
import sys, os, json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

MONGOLZ = {"910", "Techno4K", "bLitz", "cobrazera", "mzinho"}
MOUZ    = {"Brollan", "Jimpphat", "Spinx", "torzsi", "xertioN"}

def get_team(name):
    if name in MONGOLZ: return "Mongolz"
    if name in MOUZ:    return "mouz"
    return "Unknown"

def main():
    if len(sys.argv) < 3:
        sys.exit(2)

    input_file, output_file = sys.argv[1], sys.argv[2]

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Economy өгөгдөл унших
    economy_raw = data.get('economy', [])
    round_end_raw = data.get('round_end', [])

    # player_spawn event-ээс spawn өгөгдөл авах
    spawns = []
    if economy_raw and isinstance(economy_raw, list):
        for item in economy_raw:
            if isinstance(item, list) and len(item) == 2:
                rows = item[1] if isinstance(item[1], list) else []
                spawns.extend(rows)

    # round_end event-ээс winner авах
    round_winners = []
    if round_end_raw and isinstance(round_end_raw, list):
        for item in round_end_raw:
            if isinstance(item, list) and len(item) == 2:
                rows = item[1] if isinstance(item[1], list) else []
                round_winners.extend(rows)

    if not spawns:
        print("Economy өгөгдөл байхгүй")
        sys.exit(1)

    # Tick-аар round ялгах — spawn tick-уудыг ашиглах
    ticks = sorted(set(s.get('tick', 0) for s in spawns))
    round_ticks = [ticks[0]]
    for t in ticks[1:]:
        if t - round_ticks[-1] > 500:
            round_ticks.append(t)

    # Round бүрийн багийн нийт equipment value тооцох
    mongolz_eq = []
    mouz_eq = []

    for rt in round_ticks:
        # Тухайн tick-тэй spawn-уудыг авах
        round_spawns = [s for s in spawns if abs(s.get('tick', 0) - rt) < 500]
        m_total = sum(s.get('user_current_equip_value', 0) or 0
                     for s in round_spawns if get_team(s.get('user_name', '')) == "Mongolz")
        mz_total = sum(s.get('user_current_equip_value', 0) or 0
                      for s in round_spawns if get_team(s.get('user_name', '')) == "mouz")
        mongolz_eq.append(m_total)
        mouz_eq.append(mz_total)

    rounds = list(range(1, len(round_ticks) + 1))

    # Зураг
    fig, ax = plt.subplots(figsize=(16, 7))
    fig.patch.set_facecolor('#0a0a0f')
    ax.set_facecolor('#0a0a0f')

    # Арын grid
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#2a2a3f', linewidth=0.5, alpha=0.7)
    ax.xaxis.grid(False)

    # Economy шугамууд
    ax.plot(rounds, mongolz_eq, color='#FFD700', linewidth=2.5,
            marker='o', markersize=5, label='Mongolz', zorder=3)
    ax.plot(rounds, mouz_eq, color='#FF4444', linewidth=2.5,
            marker='o', markersize=5, label='mouz', zorder=3)

    # Area fill
    ax.fill_between(rounds, mongolz_eq, alpha=0.15, color='#FFD700')
    ax.fill_between(rounds, mouz_eq, alpha=0.15, color='#FF4444')

    # Force buy threshold шугам
    ax.axhline(y=10000, color='#666', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.text(len(rounds) + 0.2, 10000, 'Full buy', color='#666', fontsize=9, va='center')

    ax.axhline(y=5000, color='#444', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.text(len(rounds) + 0.2, 5000, 'Force buy', color='#444', fontsize=9, va='center')

    # Eco round тэмдэглэх
    for i, (m, mz) in enumerate(zip(mongolz_eq, mouz_eq)):
        r = rounds[i]
        if m < 5000:
            ax.axvspan(r - 0.4, r + 0.4, alpha=0.15, color='#FFD700')
        if mz < 5000:
            ax.axvspan(r - 0.4, r + 0.4, alpha=0.15, color='#FF4444')

    # Тэнхлэг тохируулга
    ax.set_xlim(0.5, len(rounds) + 1.5)
    ax.set_ylim(0, max(max(mongolz_eq), max(mouz_eq)) * 1.2)
    ax.set_xticks(rounds)
    ax.set_xticklabels([str(r) for r in rounds], color='#888', fontsize=9)
    ax.tick_params(axis='y', colors='#888')

    # Halftime шугам
    half = len(rounds) // 2
    ax.axvline(x=half + 0.5, color='#FFD700', linewidth=1.5,
               linestyle=':', alpha=0.6)
    ax.text(half + 0.5, ax.get_ylim()[1] * 0.95, 'Halftime',
            color='#FFD700', fontsize=9, ha='center', alpha=0.8)

    # Y тэнхлэг — мөнгөний дүн
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${int(x):,}'))

    ax.set_xlabel('Round', color='#888', fontsize=11)
    ax.set_ylabel('Equipment Value', color='#888', fontsize=11)
    ax.set_title('Economy Graph — Mongolz vs mouz  |  DE_MIRAGE',
                 color='white', fontsize=14, pad=15)

    legend = ax.legend(facecolor='#1e1e1e', labelcolor='white',
                      fontsize=11, loc='upper right', framealpha=0.85)

    # Spines
    for spine in ax.spines.values():
        spine.set_color('#2a2a3f')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    plt.savefig(output_file, bbox_inches='tight', dpi=150, facecolor='#0a0a0f')
    plt.close()
    print(f"Success: {output_file}")
    sys.exit(0)

if __name__ == "__main__":
    main()
