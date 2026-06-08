#!/usr/bin/env bash
# SessionStart hook: injects context when the example-plugin session begins.
# Receives JSON on stdin; returns JSON on stdout for Claude to read.

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "The example-plugin is active. Available extensions: /example-command (slash command), example-agent (subagent), example-skill (contextual guidance), and hooks that run on session start and after file edits."
  }
}
EOF
