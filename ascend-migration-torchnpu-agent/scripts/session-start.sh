#!/usr/bin/env bash
# ==============================================================================
# SessionStart hook — injects NPU migration context reminders.
# Runs at the beginning of every Claude Code session when the plugin is active.
#
# NOTE: As a "command" type hook, stdout is displayed in the terminal.
# It does NOT inject content into Claude's system prompt directly.
# The primary mechanism for context is the agent/skills system.
# ==============================================================================

echo "[ascend-migration] Plugin active — Ascend NPU migration rules loaded."

cat << 'CONTEXT'

--- Ascend NPU Migration Context ---

You have the ascend-migration-torchnpu-agent plugin active.
When performing model migration tasks, remember:

  Mandatory Principles:
  1. Follow 5-step workflow: Analysis → CPU Baseline → NPU Migration → Verification → Report
  2. Never skip steps — each step depends on the previous one
  3. Verify on CPU first before NPU migration
  4. Use official docs at hiascend.com for latest version info
  5. Never fabricate data — all results must come from actual execution
  6. Prioritize mirrors — use ModelScope/HF-mirror, not HuggingFace directly

  Available Skills:
  - migration-ascend-torchnpu-skills                        — overall workflow
  - migration-ascend-torchnpu-skills-migration-execution    — code changes & interface replacement
  - migration-ascend-torchnpu-skills-environment-setup      — Docker/CANN/torch_npu installation
  - migration-ascend-torchnpu-skills-torch-npu-reference    — API compatibility lookup
  - migration-ascend-torchnpu-skills-troubleshooting        — error diagnosis

  Key Device Mappings:
    cuda→npu  |  nccl→hccl  |  DataParallel→DDP  |  cudnn→delete
    torch.cuda.amp → torch.npu.amp

  Trigger: /ascend-migration-torchnpu-agent
  Or say: "migrate this model to run on Ascend NPU"

CONTEXT
