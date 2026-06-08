# ascend_AscendC_plugins — AscendC Operator Studio

A **self-contained, closed-loop agent plugin** for end-to-end AscendC custom operator
development on Ascend NPU. It packages the full `ascendc` skill (methodology, project
template, code-gen templates, scripts, examples) together with an orchestrator agent and a
kickoff command, so it can drive a new operator from a spec to a built, tested,
documented, and benchmarked operator — without any external dependency.

## What's inside

```
ascend_AscendC_plugins/
├── .claude-plugin/
│   └── plugin.json                     # plugin manifest
├── agents/
│   └── ascendc-operator-studio.md      # closed-loop orchestrator agent
├── commands/
│   └── ascendc-operator.md             # /ascendc-operator kickoff command
└── skills/
    └── ascendc/                        # the full self-contained skill
        ├── SKILL.md                    # lifecycle orchestrator (phase gates)
        ├── references/                 # 00..11 phase methodology (English)
        ├── templates/                  # ascend-kernel project + code-gen + design/test/precision templates
        ├── examples/                   # layer_norm profiler reference, precision-debug cases
        └── scripts/                    # detect / precision-debug / mssanitizer scripts
```

## Lifecycle (closed loop)

```
0 Environment + requirements
1 Project init        2 Design (design.md)     3 Test cases
4 Code generation     5 Compile / install / debug
6 Interface docs      7 Precision eval (fail -> precision-debug)
8 Performance eval    9 Performance optimization
10 Code review        (optional) Memory check (mssanitizer)
```

Each phase reads its `skills/ascendc/references/NN-*.md`, reuses the bundled
templates/scripts, and must pass a Definition-of-Done gate before advancing.

## Usage

This plugin targets the Claude Code plugin format. Install it from the marketplace defined
at the repo root (`.claude-plugin/marketplace.json`), then:

- **Slash command**: `/ascendc-operator <op_name> "<math/functional spec>"`
  - Single phase: append a phase, e.g. `/ascendc-operator rms_norm "..." precision`.
- **Agent**: invoke `ascendc-operator-studio` (auto-selected for "develop a new AscendC
  operator" requests, or run it manually via `/agents`).
- **Skill**: the `ascendc` skill also activates autonomously when you describe AscendC
  operator development.

## Prerequisites

- A working CANN toolkit (`source ${CANN_PATH}/*/set_env.sh`).
- A PyTorch + `torch_npu` conda environment.
- A host with Ascend NPUs to compile and run the operator.

The plugin resolves CANN/conda from the environment and asks you only when they cannot be
determined.

## Scope note

This plugin targets the **ascend-kernel / `csrc/ops` PyTorch custom-op** workflow (vector /
row / index / sort / pool operators, FP16/BF16 up-cast, two-level tiling). It is not for
the `ops-transformer` aclnn/genop flow.
