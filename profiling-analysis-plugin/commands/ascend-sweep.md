---
name: ascend-sweep
description: Sweep and analyze multiple Ascend profiling roots
argument-hint: --machine <alias> --search-root <remote-path>
allowed-tools: ["Bash", "Read", "Glob", "Grep", "remote.bash", "remote.read", "remote.artifact_pull", "remote.artifact_manifest", "remote.probe", "remote.ls"]
---

# Sweep Ascend Profiling Roots

Analyze multiple profiling roots under a remote directory in batch.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-analysis/scripts/profile_sweep.py \
  --machine <alias> --search-root <remote-path>
```

See `skills/ascend-profiling-analysis/SKILL.md` for full documentation.
