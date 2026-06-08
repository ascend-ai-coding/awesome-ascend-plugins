---
name: profiling-analysis-plugin
description: Ascend NPU profiling hub — analyze, collect, or memory-profile
argument-hint: <analyze|collect|mem-profile|mem-analyze|sweep> [args...]
allowed-tools: ["Bash", "Read", "Glob", "Grep", "remote.bash", "remote.read", "remote.artifact_pull", "remote.artifact_manifest", "remote.probe", "remote.ls", "remote.glob", "remote.grep"]
---

# Profiling Analysis Plugin

Ascend NPU profiling tools for vLLM serving scenarios.

## Sub-commands

Pass one of the following as the first argument:

### analyze
Analyze a collected Ascend profiling root or a collection manifest.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-analysis/scripts/profile_analyze.py \
  --machine <alias> --manifest <manifest-path>
```

See `skills/ascend-profiling-analysis/SKILL.md` for full options.

### sweep
Analyze multiple profiling roots under a remote directory.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-analysis/scripts/profile_sweep.py \
  --machine <alias> --search-root <remote-path>
```

### collect
Collect one Ascend torch-profiler case end-to-end.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-collection/scripts/collect_torch_profile_case.py \
  --machine <alias> --model <path> --tp <N> --tag <name> \
  --mode enforce_eager --request-kind text --benchmark-output-tokens 128
```

See `skills/ascend-profiling-collection/SKILL.md` for full options.

### mem-profile
Collect HBM memory profiling data for a vLLM service.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-memory-profiling/scripts/mem_collect.py \
  --machine <alias> --attach --tag <name>
```

### mem-analyze
Analyze collected memory profiling data.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-memory-profiling/scripts/mem_analyze.py \
  <run-dir>
```

## Prerequisites

- A managed remote Ascend NPU machine (added via machine-management)
- The machine must be ready (SSH + torch/torch_npu smoke test passing)
- For collection: the model weights must exist on the remote container
