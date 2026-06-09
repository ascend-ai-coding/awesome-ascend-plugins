# Ascend Migration torch_npu Agent

将深度学习模型从 CPU/GPU 迁移至华为昇腾 NPU 的 Claude Code 插件，
基于 `torch_npu` 适配层。

## 概述

本插件自动化端到端 NPU 迁移流程：

```
代码分析 → CPU基线 → NPU迁移 → 结果验证 → 迁移报告
```

涵盖设备映射（cuda→npu）、接口替换、混合精度适配、
分布式训练转换（nccl→hccl, DP→DDP）、
环境搭建（Docker + CANN + torch_npu）及验证报告。

**平台：仅 Claude Code。** 本插件专为 Claude Code 代理生态构建，
使用其原生 hooks、skills 和 agent 功能。

---

## 安装

本插件发布在 [awesome-ascend-plugins](https://github.com/ascend-ai-coding/awesome-ascend-plugins) 市场中。

### 一键安装

```bash
# 添加 awesome-ascend-plugins 市场（一次性配置）
claude plugins marketplace add https://github.com/ascend-ai-coding/awesome-ascend-plugins

# 安装本插件
claude plugins install ascend-migration-torchnpu-agent@awesome-ascend-plugins
```

### 本地开发安装

```bash
git clone https://github.com/ascend-ai-coding/awesome-ascend-plugins.git
cd awesome-ascend-plugins

# 添加为本地市场
claude plugins marketplace add .

# 安装本插件
claude plugins install ascend-migration-torchnpu-agent@awesome-ascend-plugins
```

### 验证安装

```bash
claude plugins list | grep ascend-migration
```

期望输出：
```
  ❯ ascend-migration-torchnpu-agent@ascend-migration-tools
    Version: 2.0.0
    Status: ✔ enabled
```

### 卸载

```bash
claude plugins uninstall ascend-migration-torchnpu-agent
```

---

## 插件结构

```
ascend-migration-torchnpu-agent/
├── .claude-plugin/
│   ├── plugin.json                           # 插件元数据 (v2.0.0)
│   └── marketplace.json                      # 市场描述
├── agents/
│   └── ascend-migration-torchnpu-agent.md    # Agent 定义
├── skills/
│   ├── migration-ascend-torchnpu-skills/                     # 总控：迁移流程编排
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-migration-execution/ # 代码迁移执行
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-environment-setup/   # 环境搭建
│   │   └── SKILL.md
│   ├── migration-ascend-torchnpu-skills-torch-npu-reference/ # API 兼容查询
│   │   └── SKILL.md
│   └── migration-ascend-torchnpu-skills-troubleshooting/    # 故障排查
│       └── SKILL.md
├── templates/
│   └── migration-report-template.md          # 报告模板
├── hooks/
│   └── hooks.json                            # SessionStart 内联 hook
├── LICENSE                                   # MIT
├── README.md                                 # 英文说明
└── README_zh.md                              # 本文件
```

---

## 使用方式

### 触发 Agent

在对话中使用以下任一关键词或短语即可自动激活 Agent：

| 触发方式 | 示例 |
|---|---|
| **自然语言** | "把这个模型迁移到昇腾NPU上" |
| | "将训练脚本从CUDA适配到torch_npu" |
| | "帮我搭建昇腾NPU开发环境" |
| | "检查我的PyTorch模型接口是否支持NPU" |
| | "把这个CUDA模型转成NPU版本" |
| | "安装CANN工具包" |
| **斜杠命令** | `/ascend-migration-torchnpu-agent` |

### 可用技能

Agent 激活后可加载以下专项技能：

| 技能 | 使用场景 |
|---|---|
| `migration-ascend-torchnpu-skills` | 整体迁移策略，五步流程指导 |
| `migration-ascend-torchnpu-skills-migration-execution` | 代码修改：设备映射、接口替换 |
| `migration-ascend-torchnpu-skills-environment-setup` | Docker/CANN/torch_npu 安装，版本对应 |
| `migration-ascend-torchnpu-skills-torch-npu-reference` | API 兼容性查询，torch_npu 等价接口 |
| `migration-ascend-torchnpu-skills-troubleshooting` | 错误诊断、OOM、精度问题 |

### 典型会话流程

```
1. 用户: "把这个 YOLO 模型迁移到 NPU"
2. Claude 加载 ascend-migration-torchnpu-agent
3. Agent 执行步骤1: 代码分析 → 识别所有接口
4. Agent 加载环境搭建技能 → 配置 Docker + CANN
5. Agent 加载迁移执行技能 → 替换 cuda 为 npu
6. Agent 执行步骤4: 验证 → 精度对比
7. Agent 执行步骤5: 报告 → 生成完整迁移报告
```

---

## 能力覆盖

| 领域 | 覆盖内容 |
|---|---|
| **设备映射** | cuda→npu, nccl→hccl, DataParallel→DDP, cudnn→删除 |
| **混合精度** | torch.cuda.amp → torch.npu.amp |
| **Autocast 适配** | NPU autocast float32 → 显式 .float() 转换 |
| **分布式训练** | HCCL 后端, context parallelism |
| **优化器** | NpuFusedSGD, NpuFusedAdamW, NpuFusedAdam |
| **环境搭建** | Docker (vllm-ascend 镜像), 手动 CANN/torch_npu 安装 |
| **版本矩阵** | CANN 7.0~9.0 × PyTorch 2.0~2.10 × torch_npu |
| **第三方库** | transformers, accelerate, peft, trl（昇腾原生支持） |
| **模型获取** | ModelScope, HF-mirror, HuggingFace |
| **验证** | 精度对比工具, 逐层验证 |
| **自定义算子** | Triton-Ascend 兼容, BSA/FA 算子适配 |
| **显存优化** | CPU offload, 多卡 context parallelism |
| **调试** | 接口支持查询, 错误模式识别 |

---

## Hooks

本插件使用 `SessionStart` hook，在每个会话启动时自动注入 NPU 迁移上下文，
确保行为一致性。

---

## 安全原则

- 绝不修改第三方库源码
- 系统级操作需要用户确认
- 无 NPU 硬件时声明"代码已修改但未经验证"
- 优先使用镜像源（pip 阿里源、ModelScope）应对受限网络
- 所有迁移报告使用实际执行数据，绝不编造

---

## 环境要求

- Claude Code CLI v1.0.0+
- 无需额外系统依赖（运行时由 skills 处理）

---

## 许可证

MIT — 详见 [LICENSE](./LICENSE)
