# msmodelslim Plugin

Model weight quantization on Ascend NPUs using msmodelslim — from quick one-click runs to custom YAML configs, mixed precision for MoE/VLM, and accuracy recovery via sensitive layer analysis.

## 描述

昇腾 NPU 模型量化插件，覆盖 W4A8 / W8A8 / W4A4 / W4A16 等量化方案，支持一键量化、自定义 YAML 配置、混合精度（MoE / VLM）、敏感层分析、vLLM Ascend 推理服务部署、AISBench 精度与性能评估的完整 E2E 工具链。

## 版本

1.0.0

## 作者

starmountain1997

## 安装和使用

### 安装方法

```bash
git clone https://github.com/ascend-ai-coding/awesome-ascend-plugins.git
cd awesome-ascend-plugins
claude --plugin-dir ./msmodelslim
```

启动后运行 `/reload-plugins` 加载 skill。

### 使用方式

调用本插件的 skill 时，使用带命名空间前缀的 skill 名称发起量化任务：

```
使用 /msmodelslim:msmodelslim 技能，将 <模型路径> 量化为 W4A8
```

### E2E 工作流

完整的量化→推理→评估→分析闭环：

1. **Quantize** — 执行模型量化，生成量化 checkpoint
2. **Serve** — 使用 vLLM + `quantization="ascend"` 部署推理服务
3. **Evaluate** — 运行 AISBench 精度基准测试（默认 GSM8K）
4. **If accuracy fails** — 运行敏感层分析，排除问题层后重试

### Prompt 关键要素

| 要素 | 必填 | 说明 |
|------|------|------|
| Skill 名称 | ✅ | `/msmodelslim:msmodelslim` |
| 本地模型路径 | ✅ | 模型权重所在目录（非 HuggingFace ID） |
| 目标量化类型 | ✅ | `w4a8`, `w8a8`, `w4a16`, `w4a4` 等 |
| 自定义 YAML | 可选 | 混合精度 / MoE / VLM 场景提供 config 路径 |
| 多 NPU 卡 | 可选 | `ASCEND_RT_VISIBLE_DEVICES=0,1,2,3` |

## 包含的 Skills

- **msmodelslim** — 核心量化 skill，涵盖量化配置、执行、服务部署、评估和敏感层分析

## 量化方案速查

| 方案 | 权重 scope | 激活 scope | 典型场景 |
|------|-----------|-----------|---------|
| W8A8 | per_channel / minmax | per_token / symmetric | 通用 LLM，精度损失最小 |
| W4A8 | per_channel / ssz | per_token / symmetric | 标准低比特量化 |
| W4A16 | per_channel / ssz | — | 权重-only 量化，适合带宽瓶颈 |
| W4A4 | per_group / autoround | pd_mix | 极致压缩，需敏感层保护 |

## 许可证

MIT

## 相关链接

- 昇腾官方文档：https://www.hiascend.com/document/
- msmodelslim 官方仓库：https://gitee.com/ascend/msmodelslim
- 原始 Skill 代码：https://github.com/ascend-ai-coding/awesome-ascend-skills
