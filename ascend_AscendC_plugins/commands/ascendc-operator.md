---
description: Develop a new AscendC custom operator end-to-end (ascend-kernel), or run a single phase on an existing one.
argument-hint: <operator_name> "<math/functional spec>" [phase: design|code-gen|compile|docs|precision|performance|optimize|review]
---

Use the **ascendc-operator-studio** agent to develop an AscendC custom operator in an
ascend-kernel project, driving the full closed loop autonomously.

Request: $ARGUMENTS

Instructions for the agent:

1. Read the bundled skill entry `${CLAUDE_PLUGIN_ROOT}/skills/ascendc/SKILL.md` first,
   then the reference for each phase you enter.
2. Phase 0: resolve the CANN path (`$ASCEND_HOME_PATH`) and the conda env; if either is
   unresolved, or the operator name / functional spec is missing, ask the user before
   proceeding.
3. If `$ARGUMENTS` names a single phase, run just that phase end-to-end. Otherwise run the
   whole lifecycle: env → init → design → test cases → code-gen → compile/debug → docs →
   precision (debug on failure) → performance → (optional) optimize → (optional) review.
4. Honor every stage gate, the unified anti-patterns, and the in-chat display rules
   (show precision/performance/optimization tables and conclusions in chat, path last).
5. Stop and report if the compile/precision debug loop fails after 3 attempts.

If invoked with no arguments, ask the user for the operator name and its math/functional
spec, then begin.
