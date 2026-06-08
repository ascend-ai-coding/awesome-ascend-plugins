# awesome-ascend-plugins

Ascend NPU complete toolchain plugin for Claude Code — end-to-end workflow from hardware check to model quantization, serving, and evaluation.

## Skill

**msmodelslim** — the single entry point covering the full E2E loop:

```
HW Check → Model Download → Quantize → Serve → Evaluate → Analyze → Retry
```

### Sections

| # | Section | What it covers |
|---|---------|---------------|
| 1 | Hardware Check | NPU health, `npu-smi info`, env setup |
| 2 | Model Download | ModelScope / HuggingFace download |
| 3 | Quantization | One-click & custom YAML, W4A8/W8A8/W4A4, MoE, VLM |
| 4 | vLLM Serving | Offline inference, API server, distributed, quantization inference |
| 5 | Evaluation | AISBench accuracy & performance benchmarks |
| 6 | Sensitive Layer Analysis | Identify & exclude problematic layers |
| 7 | Model Adapters | Register new models under third-party/ |

### Reference Files

| Reference | Content |
|-----------|---------|
| `yaml-config-guide.md` | Complete YAML reference: processors, parameters, templates |
| `analysis.md` | Sensitive layer analysis workflow |
| `model-adapter.md` | Adding new model adapters |
| `model-download.md` | Model download guide |
| `vllm-install.md` | vLLM + vllm-ascend source install |
| `vllm-run.md` | vLLM running & troubleshooting |
| `aisbench-install.md` | AISBench installation |
| `aisbench-accuracy.md` | Accuracy evaluation guide |
| `aisbench-performance.md` | Performance benchmarking guide |

## Structure

```
.
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── msmodelslim/
│       ├── SKILL.md
│       └── references/
│           ├── yaml-config-guide.md
│           ├── analysis.md
│           ├── model-adapter.md
│           ├── model-download.md
│           ├── vllm-install.md
│           ├── vllm-run.md
│           ├── aisbench-install.md
│           ├── aisbench-accuracy.md
│           └── aisbench-performance.md
└── README.md
```
