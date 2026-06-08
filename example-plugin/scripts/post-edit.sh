#!/usr/bin/env bash
# PostToolUse hook: runs after Write or Edit tool calls (matched in hooks.json).
# Receives JSON on stdin; returns additional context for Claude.

cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "A file was just modified. Consider whether formatting, tests, or documentation need updating."
  }
}
EOF
