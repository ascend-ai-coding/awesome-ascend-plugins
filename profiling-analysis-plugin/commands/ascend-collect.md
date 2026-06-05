---
name: ascend-collect
description: Collect an Ascend NPU torch-profiler case end-to-end
argument-hint: --machine <alias> --model <path> --tag <name>
allowed-tools: ["Bash", "Read", "Glob", "Grep", "remote.bash", "remote.read", "remote.artifact_pull", "remote.artifact_manifest", "remote.probe", "remote.ls"]
---

# Collect Ascend Profiling Case

Collect one torch-profiler case on a workspace-managed remote NPU container.
This starts a profiled vLLM service, brackets a workload with profile
control, and verifies the output.

```bash
py -3 ${CLAUDE_PLUGIN_ROOT}/skills/ascend-profiling-collection/scripts/collect_torch_profile_case.py \
  --machine <alias> --model <path> --tp <N> --tag <name> \
  --mode enforce_eager --request-kind text --benchmark-output-tokens 128
```

Common options:
- `--machine <alias>`: Remote machine alias
- `--session-id <id>`: Use a managed session instead
- `--model <path>`: Model path on the remote container
- `--tp <N>`: Tensor parallelism degree
- `--tag <name>`: Tag for this collection run
- `--mode <mode>`: vLLM enforce_eager or eager mode
- `--request-kind <kind>`: text or chat
- `--benchmark-output-tokens <N>`: Output token count for benchmark
- `--profiler-config <json>`: Custom profiler configuration

See `skills/ascend-profiling-collection/SKILL.md` for full documentation.
