# Awesome Ascend Plugins

面向华为昇腾 NPU 开发的 Claude Code 插件合集，以分布式 Agent Plugin 形式组织，覆盖算子开发、模型迁移、量化压缩、性能分析与 AI for Science 等场景。

仓库地址：[https://github.com/ascend-ai-coding/awesome-ascend-plugins](https://github.com/ascend-ai-coding/awesome-ascend-plugins)

## 前置要求

- [Claude Code](https://code.claude.com/)（建议 >= 2.0.0）
- 部分插件需要可用的昇腾 NPU 环境（CANN、torch_npu 等），具体见各插件说明

## 安装方式

本仓库通过 **Marketplace（插件市场）** 分发。安装分两步：先添加 marketplace，再按需安装单个 plugin。

### 第一步：添加 Marketplace

在 Claude Code 交互会话中执行：

```shell
/plugin marketplace add ascend-ai-coding/awesome-ascend-plugins
```

也可使用完整 GitHub 地址：

```shell
/plugin marketplace add https://github.com/ascend-ai-coding/awesome-ascend-plugins
```

或在终端直接使用 CLI：

```shell
claude plugin marketplace add ascend-ai-coding/awesome-ascend-plugins
```

添加成功后，可通过 `/plugin` 进入插件管理界面，在 **Discover** 标签页浏览本 marketplace 下的全部插件。

> 说明：添加 marketplace 只是注册插件目录，**不会自动安装任何 plugin**。需要单独安装你需要的模块。

### 第二步：安装 Plugin

安装指定插件（`plugin-name` 见下方模块列表）：

```shell
/plugin install <plugin-name>@awesome-ascend-plugins
```

示例——安装 AscendC 算子开发插件：

```shell
/plugin install ascendc-operator-studio@awesome-ascend-plugins
```

CLI 等效命令：

```shell
claude plugin install ascendc-operator-studio@awesome-ascend-plugins
```

安装完成后，建议执行 `/reload-plugins` 重新加载插件。

### 团队共享（可选）

若希望团队成员打开项目时自动识别本 marketplace，可在项目 `.claude/settings.json` 中加入：

```json
{
  "extraKnownMarketplaces": {
    "awesome-ascend-plugins": {
      "source": {
        "source": "github",
        "repo": "ascend-ai-coding/awesome-ascend-plugins"
      }
    }
  }
}
```

更多 marketplace 用法见 [Claude Code 官方文档](https://code.claude.com/docs/en/discover-plugins)。

## 插件模块

| Plugin 名称 | 目录 | 分类 | 简介 |
|---|---|---|---|
| `ascendc-operator-studio` | [ascend_AscendC_plugins](./ascend_AscendC_plugins) | 算子开发 | AscendC 自定义算子端到端闭环开发 |
| `profiling-analysis` | [profiling-analysis-plugin](./profiling-analysis-plugin) | 性能分析 | 昇腾 NPU Profiling 采集、分析与显存分析 |
| `msmodelslim` | [msmodelslim](./msmodelslim) | 模型量化 | 基于 msmodelslim 的模型量化与评估 |
| `ai-for-science-ai4s-basic` | [AI4S-basic](./AI4S-basic) | 模型迁移 | AI for Science 通用 NPU 迁移 Skill |
| `ascend-torchnpu-migration-plugin` | [ascend-torchnpu-migration-plugin](./ascend-torchnpu-migration-plugin) | 模型迁移 | 基于 torch_npu 的 PyTorch 模型迁移 |
| `ascend-migration-torchnpu-agent` | [ascend-migration-torchnpu-agent](./ascend-migration-torchnpu-agent) | 模型迁移 | CPU/GPU → 昇腾 NPU 迁移 Agent |
| `example-plugin` | [example-plugin](./example-plugin) | 示例 | Claude Code 插件能力参考示例 |

---

### ascendc-operator-studio — AscendC 算子开发

自包含的闭环 Agent 插件，从算子名称与数学规格出发，驱动 AscendC 自定义算子在昇腾 NPU 上的完整开发流程：环境准备 → 工程初始化 → Tiling 设计 → op_host/op_kernel 代码生成 → 编译安装调试 → 接口文档 → 精度评估 → 性能分析与优化 → 代码审查。

- 入口命令：`/ascendc-operator`
- 编排 Agent：`ascendc-operator-studio`
- 详细说明：[ascend_AscendC_plugins/README.md](./ascend_AscendC_plugins/README.md)

### profiling-analysis — 性能 Profiling 分析

面向 vLLM 推理等场景的昇腾 NPU 性能分析插件，支持 Profiling 数据采集、批量分析、HBM 显存 Profiling 及本地/远程两种工作模式，输出 Markdown、Excel、HTML 等可追溯报告。

- 核心能力：Profiling 分析、远程采集、批量 Sweep、显存采集与分析
- 详细说明：[profiling-analysis-plugin/README.md](./profiling-analysis-plugin/README.md)

### msmodelslim — 模型量化

基于 msmodelslim 的昇腾 NPU 模型量化插件，覆盖 W4A8 / W8A8 / W4A4 等量化方案，支持 YAML 配置、MoE/VLM 混合精度、敏感层分析，以及 vLLM Ascend 推理部署与 AISBench 评估的完整 E2E 工作流。

- 调用示例：`/msmodelslim:msmodelslim`
- 详细说明：[msmodelslim/README.md](./msmodelslim/README.md)

### ai-for-science-ai4s-basic — AI for Science 迁移

通用 AI for Science 昇腾 NPU 模型迁移 Skill，适用于将 PyTorch、TensorFlow、vLLM 等框架的 CUDA 项目迁移到华为 Ascend NPU，覆盖环境检查、代码分析、自动/手动迁移、分布式改造、第三方库替换与验证全流程。

- 帮助命令：`/ai-for-science-ai4s-basic:help`
- 详细说明：[AI4S-basic/README.md](./AI4S-basic/README.md)

### ascend-torchnpu-migration-plugin — torch_npu 迁移

将传统 PyTorch 深度学习模型通过 `torch_npu` 适配层迁移至昇腾 NPU 的插件，覆盖环境搭建、代码迁移、精度验证与报告输出。仅支持 torch_npu 路径，不包含 ATC 编译、ACL 原生开发或 MindSpore 迁移。

- 调用示例：`/ascend-torchnpu-migration-plugin:migration-ascend-torchnpu`
- 详细说明：[ascend-torchnpu-migration-plugin/README.md](./ascend-torchnpu-migration-plugin/README.md)

### ascend-migration-torchnpu-agent — 迁移 Agent

Claude Code / OpenCode 迁移 Agent 插件，将 CPU/GPU 上的深度学习模型自动迁移至昇腾 NPU。流程为：代码分析 → CPU 基线 → NPU 迁移 → 结果验证 → 迁移报告。

- 入口命令：`/ascend-migration-torchnpu-agent`
- 详细说明：[ascend-migration-torchnpu-agent/README.zh-CN.md](./ascend-migration-torchnpu-agent/README.zh-CN.md)

### example-plugin — 插件开发示例

展示 Claude Code 插件全部扩展能力的参考实现，包含 Skills、Agents、Commands、Hooks 与 MCP Server 配置，适合作为自定义插件的开发模板。

- 详细说明：[example-plugin/README.md](./example-plugin/README.md)

## 仓库结构

```
awesome-ascend-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace 清单（插件注册入口）
├── ascend_AscendC_plugins/       # AscendC 算子开发
├── profiling-analysis-plugin/    # Profiling 分析
├── msmodelslim/                  # 模型量化
├── AI4S-basic/                   # AI for Science 迁移
├── ascend-torchnpu-migration-plugin/
├── ascend-migration-torchnpu-agent/
└── example-plugin/               # 示例插件
```

## 许可证

各插件目录下可能有独立的 LICENSE 文件，使用前请查阅对应插件说明。
