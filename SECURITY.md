# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Autonomous Chrome Dino Bot is an offline desktop automation tool that interacts directly with the local display and input subsystem via native Win32/GDI calls (`SendInput`, `BitBlt`). It does not open network ports, transmit data externally, or execute remote code.

If you discover a security vulnerability or unsafe local memory access behavior:
1. Please open a Private Security Advisory on GitHub or contact the maintainers directly.
2. Provide detailed steps to reproduce the issue, including operating system version and monitor configuration.
3. We will respond promptly within 48 hours to confirm the report and work on a coordinated fix.
