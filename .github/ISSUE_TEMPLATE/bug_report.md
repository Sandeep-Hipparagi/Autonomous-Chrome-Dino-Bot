---
name: Bug Report
about: Report an unexpected jump, crash, or detection flaw
title: "[BUG] "
labels: bug
assignees: ''
---

**Describe the Bug**
A clear and concise description of what the bug is (e.g., missed jump, false duck, premature jump, canvas anchoring failure).

**Environment Information:**
- OS: [e.g. Windows 11 23H2]
- Display Resolution & Scaling: [e.g. 1920x1080 @ 125% DPI]
- Monitor Setup: [e.g. Single Monitor / Multi-Monitor]
- Python Version (if running from source): [e.g. 3.11.9]
- Executable or Source: [e.g. `dino_bot.exe` v1.0.0 or `python dino_bot.py`]

**To Reproduce:**
Steps to reproduce the behavior:
1. Open Chrome and navigate to `chrome://dino`
2. Run `.\dist\dino_bot.exe` (or `python dino_bot.py`)
3. Observe obstacle sequence at score: [e.g. 2,400]

**Diagnostic Replay Frames:**
If available, attach or describe the collision frame saved to `./debug_deaths/` or the cause logged in `session_telemetry.csv` (e.g. `LANDING_CLIP_CLUSTER`, `LATE_JUMP_GROUND`).

**Additional Context:**
Any other context about the issue (e.g. Night mode transition active, clouds present).
