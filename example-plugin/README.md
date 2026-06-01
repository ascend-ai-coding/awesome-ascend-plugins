# Example Plugin

A comprehensive example plugin demonstrating Claude Code extension options.

## Structure

```
example-plugin/
├── .claude-plugin/
│   └── plugin.json            # Plugin metadata
├── .mcp.json                  # MCP server configuration
├── agents/
│   └── example-agent.md       # Subagent definition
├── hooks/
│   └── hooks.json             # Event handler configuration
├── scripts/
│   ├── session-start.sh       # SessionStart hook script
│   └── post-edit.sh           # PostToolUse hook script
├── skills/
│   ├── example-skill/
│   │   └── SKILL.md           # Model-invoked skill (contextual guidance)
│   └── example-command/
│       └── SKILL.md           # User-invoked skill (slash command)
└── commands/
    └── example-command.md     # Legacy slash command format (see note below)
```

## Extension Options

### Skills (`skills/`)

Skills are the preferred format for both model-invoked capabilities and user-invoked slash commands. Create a `SKILL.md` in a subdirectory:

**Model-invoked skill** (activated by task context):

```yaml
---
name: skill-name
description: Trigger conditions for this skill
version: 1.0.0
---
```

**User-invoked skill** (slash command — `/skill-name`):

```yaml
---
name: skill-name
description: Short description for /help
argument-hint: <arg1> [optional-arg]
allowed-tools: [Read, Glob, Grep]
---
```

### Commands (`commands/`) — legacy

> **Note:** The `commands/*.md` layout is a legacy format. It is loaded identically to `skills/<name>/SKILL.md` — the only difference is file layout. For new plugins, prefer the `skills/` directory format. This plugin keeps `commands/example-command.md` as a reference for the legacy layout.

### Agents (`agents/`)

Agents are specialized subagents that Claude can spawn for focused, multi-step tasks:

```markdown
---
name: agent-name
description: When Claude should invoke this agent (include <example> blocks)
model: inherit
color: blue
tools: ["Read", "Glob", "Grep"]
---

System prompt describing the agent's role, process, and output format.
```

Required frontmatter: `name`, `description`, `model`. All `.md` files in `agents/` are auto-discovered.

### Hooks (`hooks/hooks.json`)

Hooks respond to Claude Code lifecycle events. Use `${CLAUDE_PLUGIN_ROOT}` to reference scripts bundled with the plugin:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/session-start.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/post-edit.sh"
          }
        ]
      }
    ]
  }
}
```

Supported hook types: `command`, `http`, `mcp_tool`, `prompt`, and `agent`. After changing hooks, run `/reload-plugins` or restart Claude Code.

### MCP Servers (`.mcp.json`)

Configure external tool integration via Model Context Protocol:

```json
{
  "server-name": {
    "type": "http",
    "url": "https://mcp.example.com/api"
  }
}
```

## Usage

- `/example-command [args]` - Run the example slash command
- `/example-plugin:example-agent` - Invoke the example subagent (or let Claude spawn it automatically)
- The example skill activates based on task context
- SessionStart and PostToolUse hooks run automatically when the plugin is enabled
- The example MCP activates based on task context
