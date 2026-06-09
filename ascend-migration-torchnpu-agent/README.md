# Ascend Migration torch_npu Agent

Claude Code plugin for migrating deep learning models from CPU/GPU to Huawei Ascend NPU via the `torch_npu` adaptation layer.

## Overview

This plugin automates the end-to-end NPU migration workflow:

```
Analysis → CPU Baseline → NPU Migration → Verification → Report
```

It handles device mapping (cuda→npu), interface replacement, mixed precision
adaptation, distributed training conversion (nccl→hccl, DP→DDP),
environment setup (Docker + CANN + torch_npu), and verification reporting.

**Platform: Claude Code only.** This plugin is built exclusively for the Claude Code
agent ecosystem and uses its native hooks, skills, and agent features.

---

## Installation

Published in the [awesome-ascend-plugins](https://github.com/ascend-ai-coding/awesome-ascend-plugins) marketplace.

### One-Click Install

```bash
# Add the awesome-ascend-plugins marketplace (one-time setup)
claude plugins marketplace add https://github.com/ascend-ai-coding/awesome-ascend-plugins

# Install this plugin
claude plugins install ascend-migration-torchnpu-agent@awesome-ascend-plugins
```

### Local Development Install

```bash
git clone https://github.com/ascend-ai-coding/awesome-ascend-plugins.git
cd awesome-ascend-plugins

# Add as local marketplace
claude plugins marketplace add .

# Install this plugin
claude plugins install ascend-migration-torchnpu-agent@awesome-ascend-plugins
```

### Verify Installation

```bash
claude plugins list | grep ascend-migration
```

Expected output:
```
  ❯ ascend-migration-torchnpu-agent@claude-plugins-official
    Version: 2.0.0
    Status: ✔ enabled
```

### Uninstall

```bash
claude plugins uninstall ascend-migration-torchnpu-agent
```

---

## Plugin Structure

```
ascend-migration-torchnpu-agent/
├── .claude-plugin/
│   └── plugin.json                           # Plugin metadata (v2.0.0)
├── agents/
│   └── ascend-migration-torchnpu-agent.md    # Agent definition
├── skills/
│   ├── migration-ascend-torchnpu-skills/                     # Main: workflow orchestration
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-migration-execution/ # Code migration
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-environment-setup/   # Environment setup
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-torch-npu-reference/ # API reference
│   │   └── SKILL.md
│   └── migration-ascend-torchnpu-skills-troubleshooting/    # Error diagnosis
│       └── SKILL.md
├── templates/
│   └── migration-report-template.md          # Report output template
├── hooks/
│   └── hooks.json                            # SessionStart inline hook
├── LICENSE                                   # MIT
└── README.md                                 # This file
```

---

## Usage

### Triggering the Agent

The agent activates automatically when you use any of these keywords or phrases:

| Trigger Type | Example |
|---|---|
| **Natural language** | "migrate this model to run on Ascend NPU" |
| | "adapt my training script from CUDA to torch_npu" |
| | "set up an Ascend NPU environment for this project" |
| | "check if my PyTorch model's interfaces are supported on NPU" |
| | "convert this CUDA model to NPU" |
| | "install CANN toolkit" |
| **Slash command** | `/ascend-migration-torchnpu-agent` |

### Available Skills

Once the agent is active, it can load these specialized skills:

| Skill | When to Use |
|---|---|
| `migration-ascend-torchnpu-skills` | Overall migration strategy, 5-step workflow guidance |
| `migration-ascend-torchnpu-skills-migration-execution` | Actual code changes: device mapping, interface replacement |
| `migration-ascend-torchnpu-skills-environment-setup` | Docker/CANN/torch_npu installation, version matrix |
| `migration-ascend-torchnpu-skills-torch-npu-reference` | API compatibility lookup, torch_npu equivalents |
| `migration-ascend-torchnpu-skills-troubleshooting` | Error diagnosis, OOM, precision issues |

### Typical Session Flow

```
1. User: "migrate this YOLO model to NPU"
2. Claude loads ascend-migration-torchnpu-agent
3. Agent executes Step 1: Code Analysis → identifies interfaces
4. Agent loads environment-setup skill → sets up Docker + CANN
5. Agent loads migration-execution skill → replaces cuda with npu
6. Agent runs Step 4: Verification → validates precision
7. Agent runs Step 5: Report → generates complete migration report
```

---

## Capabilities

| Area | Coverage |
|---|---|
| **Device mapping** | cuda→npu, nccl→hccl, DataParallel→DDP, cudnn→delete |
| **Mixed precision** | torch.cuda.amp → torch.npu.amp |
| **Autocast adaptation** | NPU autocast float32 → explicit .float() conversion |
| **Distributed training** | HCCL backend, context parallelism |
| **Optimizers** | NpuFusedSGD, NpuFusedAdamW, NpuFusedAdam |
| **Environment** | Docker (vllm-ascend images), manual CANN/torch_npu install |
| **Version matrix** | CANN 7.0~9.0 × PyTorch 2.0~2.10 × torch_npu |
| **Third-party libs** | transformers, accelerate, peft, trl (with Ascend-native support) |
| **Model access** | ModelScope, HF-mirror, HuggingFace |
| **Verification** | Precision comparison, layer-by-layer validation |
| **Custom kernels** | Triton-Ascend compatibility, BSA/FA kernel adaptation |
| **Memory optimization** | CPU offload, multi-GPU context parallelism |
| **Debugging** | Interface support query, error pattern recognition |

---

## Hooks

This plugin uses a `SessionStart` hook that injects NPU migration context
into every session, ensuring consistent behavior.

---

## Safety

- Never modifies third-party library source code
- Requires user confirmation for system-level operations
- Declares untested status when no NPU hardware is available
- Prioritizes mirrors (pip, ModelScope) for restricted network environments
- All migration reports use verified execution data, never fabricated

---

## Requirements

- Claude Code CLI v1.0.0+
- No additional system dependencies (all handled by skills at runtime)

---

## License

MIT — see [LICENSE](./LICENSE)
