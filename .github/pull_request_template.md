## Description

Provide a summary of the changes introduced by this pull request. Explain the problem being solved or the feature being implemented.

Fixes #(issue)

## Type of Change

- [ ] Bug fix (non-breaking change fixing an unexpected jump, crash, or detection flaw)
- [ ] New feature (non-breaking change adding functionality or hardware support)
- [ ] Performance improvement (optimization reducing loop latency, capture latency, or CPU overhead)
- [ ] Refactoring / Code cleanup (no behavioral changes)
- [ ] Documentation / CI / Tooling update

## Performance & Benchmark Verification

Autonomous Dino Bot enforces strict latency budgets. Ensure all performance benchmarks pass before submission:

- [ ] **Vision Processing Latency:** `<= 1.0 ms` (Current benchmark: `~0.34 ms`)
- [ ] **Framebuffer Capture Latency:** `<= 5.0 ms` (Direct GDI canvas grab: `~0.06 ms`)
- [ ] **Zero Memory Leak / Frame Buffer Accumulation:** Verified in soak test
- [ ] **Unit Tests Passing:** `python test_dino_bot.py` (19/19 passing)

Please paste relevant benchmark output or telemetry summary:
```text
[Paste benchmark or test output here]
```

## Checklist

- [ ] My code adheres to the project's style guidelines.
- [ ] I have performed a self-review of my own code.
- [ ] I have commented complex logic, particularly asymptotic scaling, coordinate math, or Win32 calls.
- [ ] I have updated documentation and configuration defaults where appropriate.
- [ ] All new and existing unit tests pass locally with my changes.
- [ ] Any telemetry schema changes have been documented.
