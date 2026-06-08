---
name: ascend-analyze
description: Analyze an Ascend NPU profiling root or manifest
argument-hint: --machine <alias> --manifest <path> | --local-profile-root <path>
allowed-tools: ["Bash", "Read", "Glob", "Grep", "remote.bash", "remote.read", "remote.artifact_pull", "remote.artifact_manifest", "remote.probe", "remote.ls"]
---

# Analyze Ascend Profiling Data

Analyze collected Ascend torch-profiler output and produce traceable reports.

## Remote mode (profiling data on a remote NPU machine)

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-analysis/scripts/profile_analyze.py \
  --machine <alias> --manifest <manifest-path>
```

## Local mode (profiling data on the local machine)

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-analysis/scripts/profile_analyze.py \
  --local-profile-root <local-path>
```

Common options:
- `--manifest <path>`: Path to a collection manifest JSON (remote mode)
- `--remote-profile-root <path>`: Direct path to a remote profiling root (remote mode)
- `--local-profile-root <path>`: Direct path to a local profiling root (local mode, no remote needed)
- `--tag <name>`: Tag for the local output directory
- `--local-output-dir <path>`: Explicit local output directory
- `--remote-timeout <seconds>`: Timeout for remote analysis (default 3600)
- `--overwrite`: Overwrite existing output directory
- `--skip-html`: Skip HTML report rendering
- `--report-mode summary|full-raw`: HTML report depth (default: full-raw)
- `--from-stage <stage>` / `--to-stage <stage>` / `--only-stage <stage>`: Stage selection

See `skills/ascend-profiling-analysis/SKILL.md` for full documentation.
