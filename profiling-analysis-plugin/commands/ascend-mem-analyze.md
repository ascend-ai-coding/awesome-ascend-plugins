---
name: ascend-mem-analyze
description: Analyze collected Ascend memory profiling data
argument-hint: <run-dir>
allowed-tools: ["Bash", "Read", "Glob", "Grep"]
---

# Ascend Memory Profiling — Analysis

Analyze previously collected HBM memory profiling data and produce a
breakdown report.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-memory-profiling/scripts/mem_analyze.py \
  <run-dir>
```

Where `<run-dir>` is the local directory created by `ascend-mem-profile`
containing the collected CSV and log files.

See `skills/ascend-memory-profiling/SKILL.md` for full documentation.
