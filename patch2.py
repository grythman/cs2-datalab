import re
with open("scripts/create_shorts_cli.py", "r") as f:
    code = f.read()

# Update render_subtitle logic to be 1-line subtitle
if "def render_subtitle" in code:
    code = re.sub(
        r'margin = 60\n    max_width = W - 2 \* margin(.*?)words = re\.split',
        'margin = 40\n    max_width = W - 2 * margin\n    # 1-line subtitle system\n    words = re.split',
        code,
        flags=re.DOTALL
    )

with open("scripts/create_shorts_cli.py", "w") as f:
    f.write(code)
