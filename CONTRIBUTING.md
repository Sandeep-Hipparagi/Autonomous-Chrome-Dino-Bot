# Contributing to Autonomous Chrome Dino Bot

Thank you for your interest in contributing to the **Autonomous Chrome Dino Bot** project! This repository contains a high-performance, ultra-low-latency autonomous runner engineered to survive long endurance runs (>10,000+ score) in Google Chrome's offline runner (`chrome://dino`).

---

## 1. Development Principles

1. **Sub-Millisecond Heuristic Core:** Strictly avoid heavy machine learning frameworks (`torch`, `tensorflow`, `ultralytics`) or high-overhead vision APIs. All perception and state evaluation must remain sub-millisecond.
2. **Direct Memory Framebuffer Reads:** Always maintain low-latency screen capture (`AsyncFrameGrabber` with `mss`). Do not introduce blocking screenshot APIs.
3. **Observation-Driven Action:** The bot must never jump blindly or periodically; all keypresses must be strictly coordinated with measured obstacle mass, cluster width, and altitude bands.
4. **Hardware Scan-Code Primitives:** Maintain low-level native key injection with thread-safe cancellation and explicit airborne lockout guards.

---

## 2. Environment Setup

### Prerequisites
- **Python 3.10+** (Python 3.11, 3.12, 3.13, 3.14 supported)
- **Windows 10/11** (for hardware scan-code input injection and per-monitor DPI awareness)
- **Google Chrome** (`chrome://dino`)

### Local Setup
```powershell
# Clone the repository
git clone https://github.com/sandeep-hipparagi/Autonomous-Chrome-Dino-Bot.git
cd Autonomous-Chrome-Dino-Bot

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller pytest
```

---

## 3. Running Verification & Benchmarks

Before submitting any Pull Request, ensure that all tests pass and vision processing latency stays within target:

```powershell
# Run the 19-test verification suite
python test_dino_bot.py

# Run the 500-frame benchmark
python dino_bot.py --benchmark
```

Expected benchmark thresholds:
- **Vision Engine Latency:** Mean `< 0.5 ms` (>2,000 FPS)
- **Framebuffer Grab Latency:** Mean `< 5.0 ms` (>200 FPS)
- **Unit Tests:** 19/19 Passing

---

## 4. Building the Standalone Executable

To build the standalone zero-dependency Windows executable:
```powershell
pyinstaller --onefile --noconfirm --name dino_bot dino_bot.py
```
Verify the output in `dist/dino_bot.exe` and update the SHA-256 checksum:
```powershell
$hash = (Get-FileHash -Path dist/dino_bot.exe -Algorithm SHA256).Hash.ToLower()
"$hash  dino_bot.exe" | Out-File -FilePath dist/SHA256SUMS.txt -Encoding ascii
```

---

## 5. Submitting Changes

1. Fork the repository and create your feature branch: `git checkout -b feature/amazing-feature`.
2. Commit your changes with clear, descriptive commit messages.
3. Ensure code formatting is clean and tests pass without errors.
4. Open a Pull Request referencing any related issues.
