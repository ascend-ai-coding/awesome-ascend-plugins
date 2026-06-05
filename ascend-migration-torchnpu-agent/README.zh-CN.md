# Ascend Migration torch_npu Agent（昇腾 NPU 迁移代理）

一个 **Claude Code** / **OpenCode** 插件，用于将深度学习模型从 CPU/GPU 自动迁移至 **华为昇腾 NPU**，基于 `torch_npu` 适配层。

迁移流程：**代码分析 → CPU 基线 → NPU 迁移 → 结果验证 → 迁移报告**

## 快速开始

```bash
git clone https://github.com/Gongdayao/awesome-ascend-plugins
cd awesome-ascend-plugins/ascend-migration-torchnpu-agent
./install.sh
```

重启 Claude Code（或 OpenCode），然后触发代理：

- **Claude Code：** `/ascend-migration-torchnpu-agent`
- **自然语言：** *"把这个模型迁移到昇腾 NPU 上运行"*

## 安装

### 环境要求

- **Claude Code**（>= 2.0.0）或 **OpenCode**
- `git`、`bash`、`python3`（macOS 和大多数 Linux 发行版自带）
- 如果要实际运行迁移后的模型，需要华为昇腾 NPU 环境（无 NPU 时插件仍可进行代码转换，但会标注结果未经验证）

### 自动安装（推荐）

```bash
git clone https://github.com/Gongdayao/awesome-ascend-plugins
cd awesome-ascend-plugins/ascend-migration-torchnpu-agent
./install.sh
```

安装器会自动检测 Claude Code 和/或 OpenCode 是否可用，并为所有已找到的工具安装。选项：

```bash
./install.sh --claude     # 仅安装到 Claude Code
./install.sh --opencode   # 仅安装到 OpenCode
./install.sh --uninstall  # 卸载插件
```

### 手动安装

如果 `install.sh` 无法使用，请按以下步骤手动安装：

<details>
<summary><b>Claude Code — 手动安装步骤</b></summary>

```bash
# 1. 复制代理定义
mkdir -p ~/.claude/agents
cp agents/ascend-migration-torchnpu-agent.md ~/.claude/agents/

# 2. 复制技能
mkdir -p ~/.claude/skills
cp -r skills/* ~/.claude/skills/

# 3. 安装脚本
mkdir -p ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts
cp scripts/*.sh ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/
chmod +x ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/*.sh
```

然后将 `hooks/hooks.json` 中 `manual_setup.settings_snippet` 部分的内容添加到 `~/.claude/settings.json`，将 `{PLUGIN_ROOT}` 替换为 `~/.claude/plugins-installed/ascend-migration-torchnpu-agent` 的绝对路径。
</details>

<details>
<summary><b>OpenCode — 手动安装步骤</b></summary>

```bash
cp -r skills/* ~/.config/opencode/skills/
cp agents/ascend-migration-torchnpu-agent.md ~/.config/opencode/agents/
```
</details>

## 安装内容

| 路径 | 用途 |
|------|------|
| `.claude-plugin/plugin.json` | 插件元数据 |
| `agents/ascend-migration-torchnpu-agent.md` | 子代理定义 |
| `skills/`（5 个子目录） | 流程编排、代码迁移、环境搭建、API 参考、故障排查 |
| `templates/migration-report-template.md` | 迁移报告模板 |
| `hooks/hooks.json` | Hook 配置参考 |
| `scripts/session-start.sh` | 会话启动钩子 — 显示 NPU 迁移规则 |
| `scripts/post-edit.sh` | 编辑后钩子 — 扫描残留的 CUDA 引用 |

## 核心能力

| 领域 | 处理内容 |
|------|---------|
| **设备映射** | cuda→npu、nccl→hccl、DataParallel→DDP、cudnn→删除 |
| **混合精度** | `torch.cuda.amp` → `torch.npu.amp` |
| **优化器** | NpuFusedSGD、NpuFusedAdamW、NpuFusedAdam |
| **环境搭建** | Docker + CANN 镜像，或手动安装驱动/CANN/torch_npu |
| **版本支持** | CANN 7.0–9.0 × PyTorch 2.0–2.10 × torch_npu |
| **第三方库** | transformers、accelerate、peft、trl（昇腾原生支持） |
| **验证** | 精度对比工具和逐层验证 |

## 设备映射速查表

| CUDA（原始） | NPU（目标） | 说明 |
|-------------|------------|------|
| `.cuda()` / `.to('cuda')` | `.npu()` / `.to('npu')` | Tensor/模型迁移 |
| `torch.cuda.is_available()` | `torch.npu.is_available()` | 设备检查 |
| `torch.cuda.amp.autocast()` | `torch.npu.amp.autocast()` | 混合精度 |
| `torch.cuda.amp.GradScaler()` | `torch.npu.amp.GradScaler()` | 梯度缩放 |
| `backend="nccl"` | `backend="hccl"` | 分布式通信 |
| `DataParallel` | `DistributedDataParallel` | DP 在 NPU 上不支持 |
| `torch.backends.cudnn.*` | 删除/条件跳过 | 不可用 |

## 常见问题

### `./install.sh` 执行失败

- 确保 `python3` 可用：`python3 --version`
- 确保 `bash` >= 4.0：`bash --version`
- 显式指定工具安装：`./install.sh --claude`

### 安装后代理未出现

- 重启 Claude Code / OpenCode
- 检查代理文件是否存在：`ls ~/.claude/agents/ascend-migration-torchnpu-agent.md`
- 检查技能是否存在：`ls ~/.claude/skills/migration-ascend-torchnpu-skills/SKILL.md`

### `claude plugins install .` 不起作用

这是预期行为。Claude Code 2.x 目前仅支持从已配置的插件市场安装插件，不支持从本地目录安装。请改用 `./install.sh`。

### Hooks 不执行

- 检查 `~/.claude/settings.json` 中是否包含 `"hooks"` 配置且脚本路径正确
- 确保脚本有执行权限：`chmod +x ~/.claude/plugins-installed/ascend-migration-torchnpu-agent/scripts/*.sh`
- 修改 settings.json 后需重启 Claude Code

## 环境限制

- NPU 服务器通常为 **ARM（aarch64）** 架构
- 网络通常**受限**（无法直接访问 HuggingFace/GitHub）
- 使用 pip 镜像源：`-i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com`
- 使用 ModelScope 下载模型：`from modelscope import snapshot_download`
- 使用 HF 镜像站：`export HF_ENDPOINT=https://hf-mirror.com`
- **优先使用 Docker 方式搭建环境**

## 安全声明

插件**绝不修改第三方库源码**，对系统级操作**需要用户确认**。当无 NPU 硬件时，会明确声明代码修改后未在 NPU 上验证。

## 许可证

MIT — 详见 [LICENSE](LICENSE) 文件。

---

📖 [English README](README.md)
