---
name: ascend-mem-profile
description: Profile HBM memory usage on Ascend NPU
argument-hint: --machine <alias> --attach --tag <name>
allowed-tools: ["Bash", "Read", "Glob", "Grep", "remote.bash", "remote.read", "remote.artifact_pull", "remote.artifact_manifest", "remote.probe", "remote.ls"]
---

# Ascend Memory Profiling — Collection

Profile and attribute HBM memory usage on Ascend NPU for vLLM serving.
Breaks down memory into fixed overhead, model weights, KV cache, HCCL
buffers, activations, and runtime.

**Standalone mode** (default):
```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-memory-profiling/scripts/mem_collect.py \
  --machine <alias> --model <path> --tp <N> --tag <name>
```

**Attach mode** (attach to an already-running service):
```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-memory-profiling/scripts/mem_collect.py \
  --machine <alias> --attach --tag <name>
```

Common options:
- `--machine <alias>`: Remote machine alias
- `--session-id <id>`: Use a managed session instead
- `--attach`: Attach to an already-running vLLM service
- `--model <path>`: Model path (standalone mode only)
- `--tp <N>`: Tensor parallelism degree
- `--tag <name>`: Tag for this profiling run

See `skills/ascend-memory-profiling/SKILL.md` for full documentation.
