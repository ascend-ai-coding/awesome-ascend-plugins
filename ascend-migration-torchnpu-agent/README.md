# Ascend Migration torch_npu Agent

A **Claude Code** and **OpenCode** plugin that automates converting deep learning models from CPU/GPU to **Huawei Ascend NPU** using the `torch_npu` adaptation layer.

The workflow follows: **Analysis → CPU Baseline → NPU Migration → Verification → Report**

## Quick Start

```bash
git clone https://github.com/Gongdayao/awesome-ascend-plugins
cd awesome-ascend-plugins/ascend-migration-torchnpu-agent
./install.sh
```

Restart Claude Code (or OpenCode), then trigger the agent:

- **Claude Code:** `/ascend-migration-torchnpu-agent`
- **Natural language:** *"migrate this model to run on Ascend NPU"*

## Installation

### Prerequisites

- **Claude Code** (>= 2.0.0) or **OpenCode**
- `git`, `bash`, `python3` (available by default on macOS and most Linux distributions)
- Access to a Huawei Ascend NPU environment if you intend to actually run migrated models (the plugin will work for code transformation without one, but marks results as untested)

### Automatic Installation (Recommended)

```bash
git clone https://github.com/Gongdayao/awesome-ascend-plugins
cd awesome-ascend-plugins/ascend-migration-torchnpu-agent
./install.sh
```

The installer auto-detects whether Claude Code and/or OpenCode are available and installs for all found tools. Options:

```bash
./install.sh --claude     # Claude Code only
./install.sh --opencode   # OpenCode only
./install.sh --uninstall  # Remove the plugin
```

### Manual Installation

If `install.sh` doesn't work for your setup, follow the manual steps:

<details>
<summary><b>Claude Code — manual steps</b></summary>

```bash
# 1. Copy agent
mkdir -p ~/.claude/agents
cp agents/ascend-migration-torchnpu-agent.md ~/.claude/agents/

# 2. Copy skills
mkdir -p ~/.claude/skills
cp -r skills/* ~/.claude/skills/

# 3. Install scripts
mkdir -p ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts
cp scripts/*.sh ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/
chmod +x ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/*.sh
```

Then add the hooks from `hooks/hooks.json` → `manual_setup.settings_snippet` into your `~/.claude/settings.json`, replacing `{PLUGIN_ROOT}` with the absolute path to `~/.claude/plugins-installed/ascend-migration-torchnpu-agent`.
</details>

<details>
<summary><b>OpenCode — manual steps</b></summary>

```bash
cp -r skills/* ~/.config/opencode/skills/
cp agents/ascend-migration-torchnpu-agent.md ~/.config/opencode/agents/
```
</details>

## What Gets Installed

| Path | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin metadata |
| `agents/ascend-migration-torchnpu-agent.md` | Subagent definition |
| `skills/` (5 subdirectories) | Workflow, code migration, environment setup, API reference, troubleshooting |
| `templates/migration-report-template.md` | Report output format |
| `hooks/hooks.json` | Hook configuration reference |
| `scripts/session-start.sh` | Session start hook — displays NPU migration rules |
| `scripts/post-edit.sh` | Post-edit hook — scans for residual CUDA references |

## Key Capabilities

| Area | What It Handles |
|------|----------------|
| **Device mapping** | cuda→npu, nccl→hccl, DataParallel→DDP, cudnn→removal |
| **Mixed precision** | Converts `torch.cuda.amp` → `torch.npu.amp` |
| **Optimizers** | NpuFusedSGD, NpuFusedAdamW, NpuFusedAdam |
| **Environment** | Docker with CANN images or manual driver/CANN/torch_npu install |
| **Version support** | CANN 7.0–9.0 × PyTorch 2.0–2.10 × torch_npu |
| **Third-party libs** | transformers, accelerate, peft, trl (Ascend-native support) |
| **Verification** | Precision comparison tools and layer-by-layer validation |

## Device Mapping Quick Reference

| CUDA (original) | NPU (target) | Notes |
|-----------------|--------------|-------|
| `.cuda()` / `.to('cuda')` | `.npu()` / `.to('npu')` | Tensor/model transfer |
| `torch.cuda.is_available()` | `torch.npu.is_available()` | Device check |
| `torch.cuda.amp.autocast()` | `torch.npu.amp.autocast()` | Mixed precision |
| `torch.cuda.amp.GradScaler()` | `torch.npu.amp.GradScaler()` | Gradient scaling |
| `backend="nccl"` | `backend="hccl"` | Distributed comm |
| `DataParallel` | `DistributedDataParallel` | DP unsupported on NPU |
| `torch.backends.cudnn.*` | Delete/condition-skip | Not available |

## Troubleshooting

### `./install.sh` fails

- Ensure `python3` is available: `python3 --version`
- Ensure `bash` >= 4.0: `bash --version`
- Run with explicit tool flag: `./install.sh --claude`

### Agent does not appear after installation

- Restart Claude Code / OpenCode
- Verify agent file exists: `ls ~/.claude/agents/ascend-migration-torchnpu-agent.md`
- Verify skills exist: `ls ~/.claude/skills/migration-ascend-torchnpu-skills/SKILL.md`

### `claude plugins install .` doesn't work

This is expected. Claude Code 2.x currently supports installing plugins only from configured marketplaces, not from local directories. Use `./install.sh` instead.

### Hooks not running

- Check `~/.claude/settings.json` contains `"hooks"` entries with correct script paths
- Ensure scripts are executable: `chmod +x ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/*.sh`
- Restart Claude Code after modifying settings.json

## Environment Constraints

- NPU servers are typically **ARM (aarch64)** architecture
- Network often **restricted** (no HuggingFace/GitHub direct access)
- Use pip mirrors: `-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
- Use ModelScope for models: `from modelscope import snapshot_download`
- Use HF mirror: `export HF_ENDPOINT=https://hf-mirror.com`
- **Docker is the preferred environment setup method**

## Safety

The plugin **never modifies third-party library source code** and **requires user confirmation for system-level operations**. When no NPU hardware is available, it declares migrated code as untested.

## License

MIT — see the [LICENSE](LICENSE) file.

---

📖 [中文文档 (Chinese README)](README.zh-CN.md)
