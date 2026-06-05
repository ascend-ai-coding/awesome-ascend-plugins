# session-management

Manage isolated VAWS agent sessions for parallel remote work.

## Entry points

| Script | Purpose |
|--------|---------|
| `scripts/session_remove.py` | Remove a session's service, container, worktree, and leases |

## Usage

```bash
python3 scripts/session_remove.py --session-id <ID> --remove-container --release-leases
```
