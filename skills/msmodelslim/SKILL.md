---
name: msmodelslim
description: Model quantization on Ascend NPUs using msmodelslim. Use whenever the user wants to quantize an LLM or VLM (W4A8, W8A8, W4A16, W4A4, or other dtypes), write a quantization YAML config, run sensitive layer analysis, compress model weights for NPU serving, or debug quantization accuracy. Covers one-click quantization, custom YAML authoring, mixed precision for MoE models, VLM calibration, and adding new model adapters.
argument-hint: quantize / config / analyze / adapter
license: MIT
---

# msmodelslim

Model weight quantization on Ascend NPUs — from quick one-click runs to custom YAML configs, mixed precision, and accuracy recovery.

## Prerequisites

Before quantizing:

1. **NPU hardware** — verify NPUs are available with `npu-smi info`
2. **Model on disk** — the model must be downloaded locally. See [references/model-download.md](references/model-download.md). `--model_path` always points to a local directory, never an online model ID
3. **Dependencies** — verify with `pip show msmodelslim torch_npu transformers`

## Decision Flow

When a user asks to quantize a model, follow this decision tree:

```
User states: model + target dtype (e.g., "quantize Qwen3-32B to W4A8")
        │
        ▼
Is there a lab_practice YAML for this model + dtype?
        │
   ┌────┴────┐
   │ YES     │ NO
   ▼         ▼
Use        Build a custom YAML using the config guide.
one-click  See [references/yaml-config-guide.md](references/yaml-config-guide.md)
command    for templates and parameter selection.
   │         │
   ▼         ▼
Quantize → Serve → Evaluate
        │
   ┌────┴────┐
   │ PASS     │ FAIL
   ▼          ▼
Done     Run sensitive layer analysis → exclude problematic layers → retry
         See [references/analysis.md](references/analysis.md)
```

## Quantization Execution

### One-Click (lab_practice config exists)

When a pre-configured YAML exists in `msmodelslim/lab_practice` for the model + dtype:

```bash
msmodelslim quant \
    --model_path ${MODEL_PATH} \
    --save_path ${SAVE_PATH} \
    --device npu \
    --model_type <ModelName> \
    --quant_type <TARGET_DTYPE> \
    --trust_remote_code True
```

- `--quant_type` auto-matches the best YAML from `lab_practice`. Values: `w4a8`, `w4a8c8`, `w8a8`, `w8a8s`, `w8a8c8`, `w8a16`, `w16a16s`
- `--config_path` can be used instead to point to a specific YAML file (takes priority over `--quant_type`)
- Always pass `--trust_remote_code True` for models with custom architectures (Qwen3, DeepSeek, GLM, etc.)

### Custom YAML (no lab_practice config, or mixed precision needed)

When no pre-built config matches, or when the model needs mixed precision (MoE, VLM), write a YAML config and use `--config_path`.

**Use [references/yaml-config-guide.md](references/yaml-config-guide.md) as the authoritative reference** for all YAML structure, processor types, parameters, and templates. It covers:

- YAML顶层结构 (top-level structure)
- 离群值抑制处理器选择 (outlier suppression: iter_smooth, flex_smooth_quant, AWQ, QuaRot)
- 量化处理器配置 (quantization: linear_quant, autoround_quant)
- group 元处理器 (mixed precision via layer grouping)
- 完整模板 (W8A8, W4A8, W4A16, MoE, VLM)
- 参数决策 (scope, method, symmetric 选取逻辑)

## Quick Parameter Reference

These are the most common decisions. The full rationale and edge cases are in the config guide.

**Activation scope + symmetric** (hardware-constrained on Ascend NPU):

| scope | symmetric | type | use case |
|-------|-----------|------|----------|
| `per_token` | `true` | dynamic | Default for LLMs — one scale per token at runtime |
| `per_tensor` | `false` | static | Throughput-optimized attention layers |
| `pd_mix` | `false` | hybrid | Only with KV cache quantization (w8a8c8) |

**Weight scope**:

| scope | when |
|-------|------|
| `per_channel` | Standard for W8A8 and all W4A8 |
| `per_group` + `group_size` | W4A4 only, when absolute minimum memory is needed |

**Weight method** (determined by dtype + scope):

| dtype | scope | method |
|-------|-------|--------|
| int8 | per_channel | `minmax` |
| int4 | per_channel | `ssz` |
| int4 | per_group | `autoround` |

**Outlier suppression** (runs before quantization):

| dtype | preprocessor | subgraph types |
|-------|-------------|----------------|
| W8A8 (dense) | `iter_smooth` (alpha=0.5) | norm-linear, linear-linear, ov, up-down |
| W4A8 (standard) | `flex_smooth_quant` | norm-linear (+ ov if cross-attention exists) |
| W4A4 / aggressive | `quarot` → `flex_smooth_quant` | quarot has no subgraph config |
| W4A16 (weight-only) | `awq` | norm-linear, linear-linear, ov, up-down |

## E2E Workflow

The full loop is: **quantize → serve → evaluate → (if fail) analyze → retry**.

1. **Quantize** — produce a quantized checkpoint
2. **Serve** — launch vLLM with `quantization="ascend"`. See [references/vllm-run.md](references/vllm-run.md) for offline validation, optimization, and online serving. See [references/vllm-install.md](references/vllm-install.md) if vLLM is not yet installed.
3. **Evaluate** — run AISBench accuracy benchmark (GSM8K; threshold: ≤1 pp drop vs FP16 baseline). See [references/aisbench-accuracy.md](references/aisbench-accuracy.md). See [references/aisbench-install.md](references/aisbench-install.md) if AISBench is not yet installed.
4. **If accuracy fails** — run sensitive layer analysis ([references/analysis.md](references/analysis.md)) to identify problematic layers, add them to `exclude`, and retry quantization
5. **If still failing** — inform the user and discuss fallback options (higher bit width for sensitive layers, different preprocessor)

## Calibration Datasets

| dataset | use for |
|---------|---------|
| `mix_calib.jsonl` (default) | General-purpose text models |
| `qwen3_cot.json` | Reasoning/CoT models at W8A8 |
| `qwen3_cot_w4a4.json` | Reasoning models at W4A4 or aggressive W4A8 |
| `autocodebench.jsonl` | Code models |

**For Vision-Language Models**: built-in datasets are text-only and cannot calibrate vision components. Always supply a custom multimodal calibration dataset (64–256 samples, base64 image URIs in chat format). See the config guide for format details and vision component exclusion patterns.

## Layer Protection

Some layers are inherently sensitive to quantization:

- **`*gate` routers** — never quantize (universal across all lab_practice configs)
- **`*lm_head*`** — exclude or use higher bit width
- **`*embed_tokens*`** — exclude for INT4
- **First/last N transformer layers** — exclude or bump to W8A8 if accuracy drops

Start without layer protection. Add exclusions only after evaluation shows accuracy degradation.

## Adding a New Model Adapter

When quantizing a model with no existing lab_practice config, register it under `third-party/msmodelslim/<model_family>/`. See [references/model-adapter.md](references/model-adapter.md) for the directory layout, YAML template, and validation steps.

## Running Commands

Save quantization commands to a shell script and execute it so output is captured in a timestamped log file. This makes debugging easier when quantization fails.

## Core Tips

- `msmodelslim` is installed in editable mode. Run `pip show msmodelslim` to find the source directory
- For OOM on a single NPU, distribute across multiple devices: `export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3` and pass `--device npu:0,1,2,3`
- `--quant_type` and `--config_path` are mutually exclusive — use one or the other
- SSZ does not support `per_group` scope — switch to `autoround` for per_group INT4
- GPTQ is not recommended for MoE expert layers — use `ssz` (per_channel) or `autoround` (per_group)
