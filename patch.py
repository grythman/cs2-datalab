import re
with open("scripts/create_shorts_cli.py", "r") as f:
    code = f.read()

beat_code = """
BEAT_DURATIONS = {
    "hook": 3.0,
    "setup": 4.0,
    "proof": 8.0,
    "swing": 5.0,
    "payoff": 6.0,
    "close": 4.0
}

def allocate_beat_durations(total_duration, num_scenes):
    # Fallback if unmatch
    if num_scenes == 0:
        return []
    base_beats = [3.0, 4.0, 8.0, 5.0, 6.0, 4.0] 
    if num_scenes <= len(base_beats):
        beats = base_beats[:num_scenes]
    else:
        beats = base_beats + [4.0] * (num_scenes - len(base_beats))
        
    s = sum(beats)
    return [b/s * total_duration for b in beats]
"""

if "def allocate_scene_durations" in code:
    code = re.sub(
        r"def allocate_scene_durations\(total_duration:(.*?)\]:",
        beat_code + "\ndef allocate_scene_durations(total_duration: float, num_scenes: int) -> list[float]:\n    return allocate_beat_durations(total_duration, num_scenes)\n    # legacy -> ",
        code,
        flags=re.DOTALL | re.MULTILINE
    )

with open("scripts/create_shorts_cli.py", "w") as f:
    f.write(code)
