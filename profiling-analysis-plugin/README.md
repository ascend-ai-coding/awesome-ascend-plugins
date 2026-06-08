# profiling-analysis-plugin

Ascend NPU profiling collection, analysis, and memory profiling for vLLM serving.

## Overview

This is a Claude Code / Codex plugin that provides five core capabilities for Ascend NPU profiling workflows:

| Capability | Description | Remote Required |
|---|---|---|
| **Profiling Analysis** | Analyze collected torch-profiler output, produce traceable reports (md/xlsx/html) | Optional (supports local mode) |
| **Profiling Collection** | Collect one torch-profiler case end-to-end on a remote NPU | Yes |
| **Profiling Sweep** | Batch analyze multiple profiling roots on a remote machine | Yes |
| **Memory Profile** | Collect HBM memory usage data on Ascend NPU | Yes |
| **Memory Analyze** | Analyze collected memory profiling data locally | No |

## Installation

Add this plugin to your Claude Code or Codex workspace:

```bash
# Claude Code
claude plugin add /path/to/profiling-analysis-plugin

# Or copy into your project's .claude/plugins/ directory
```

## Commands

### `/ascend-analyze` — Analyze Profiling Data

**Local mode** (no remote server needed):
```bash
/ascend-analyze --local-profile-root /path/to/local/profiling_data
```

**Remote mode** (profiling data on a remote NPU machine):
```bash
/ascend-analyze --machine <alias> --manifest <manifest-path>
/ascend-analyze --machine <alias> --remote-profile-root /remote/path
```

Key options:
- `--local-profile-root <path>` — Local profiling directory (skips SSH)
- `--manifest <path>` — Collection manifest JSON from a prior `ascend-collect` run
- `--remote-profile-root <path>` — Remote profiling root path
- `--local-output-dir <path>` — Output directory
- `--skip-html` — Skip HTML rendering (faster)
- `--report-mode summary|full-raw` — HTML depth (default: full-raw)
- `--from-stage / --to-stage / --only-stage` — Partial pipeline re-runs

### `/ascend-collect` — Collect Profiling Data

```bash
/ascend-collect --machine <alias> --model /path/to/model --tp 4 --tag my_run
```

Key options:
- `--machine <alias>` — Remote machine alias
- `--model <path>` — Model path on the remote container
- `--tp <N>` — Tensor parallelism degree
- `--tag <name>` — Run tag
- `--mode enforce_eager` — vLLM mode
- `--benchmark-output-tokens <N>` — Output token count

### `/ascend-sweep` — Batch Analyze Multiple Roots

```bash
/ascend-sweep --machine <alias> --search-root /remote/profiling_dir
```

Key options:
- `--search-root <path>` — Remote directory to scan (repeatable)
- `--limit <N>` — Cap number of roots
- `--jobs <N>` — Parallel analysis threads
- `--reuse-existing` — Skip roots with existing manifests
- `--render-html` — Render HTML for each root (off by default)

### `/ascend-mem-profile` — Collect Memory Profiling Data

**Standalone mode**:
```bash
/ascend-mem-profile --machine <alias> --model /path/to/model --tp 4 --tag my_mem
```

**Attach mode** (attach to a running service):
```bash
/ascend-mem-profile --machine <alias> --attach --tag my_mem
```

### `/ascend-mem-analyze` — Analyze Memory Profiling Data

```bash
/ascend-mem-analyze <run-dir>
```

Where `<run-dir>` is the local directory created by `/ascend-mem-profile`.

## Natural Language Usage

You can also use natural language with the agent:

- "分析一下 `/path/to/profiling_data` 这份 profiling 数据" → triggers local analysis
- "采集一个 profiling case" → triggers collection
- "显存用了多少" → triggers memory profiling
- "批量分析远端的 profiling 目录" → triggers sweep

## Local Profiling Data Requirements

When using `--local-profile-root`, the directory must contain Ascend profiler output:

```
<local-profile-root>/
  kernel_details.csv          # Required
  trace_view.json             # Optional
  op_summary/                 # Optional
  communication.json          # Optional
```

## Output

Analysis results are written to `.vaws-local/profiling-analysis/runs/<timestamp>_<tag>/` by default:

```
report/
  report.md        # Markdown report
  report.xlsx      # Excel report
  report.html      # Interactive HTML report
*_manifest.json     # Pipeline manifests
diagnosis_findings.json
*.csv              # Summary CSVs
```

## Prerequisites

- **Remote mode**: A managed remote Ascend NPU machine (added via machine-management skill), with SSH access and `torch`/`torch_npu` available
- **Local mode**: Profiling data already downloaded to the local machine; only Python stdlib + `pandas` needed
- **Collection**: Model weights must exist on the remote container

## Plugin Structure

```
profiling-analysis-plugin/
  .claude-plugin/plugin.json     # Plugin metadata
  .mcp.json                      # MCP server config (remote-dev)
  agents/ascend-profiler.md      # Agent routing rules
  commands/                      # Slash command definitions
  hooks/                         # Pre-tool-use guards
  skills/                        # Skill packages
    ascend-profiling-analysis/   # Profiling analysis
    ascend-profiling-collection/ # Profiling collection
    ascend-memory-profiling/     # Memory profiling
  scripts/                       # MCP server & remote tools
  agents_shared/                 # Shared libraries
```
