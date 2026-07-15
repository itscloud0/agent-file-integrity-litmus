# Guarded adapter summary — 2026-07-15

Environment: macOS; Codex CLI 0.144.4; opencode 1.16.2.

| Adapter | Run 1 | Run 2 | Exact repeated finding |
| --- | --- | --- | --- |
| Codex CLI native tools | 2/6 | 3/6 | CRLF, final-newline, and Windows-1252 failed twice; executable handling varied. |
| opencode native tools | 5/6 | 5/6 | Windows-1252 failed twice; one safe skip and one replacement-character corruption. |

All client processes returned zero. The exact-byte scorer found failures that client final messages sometimes described as successful.

Raw stdout, stderr, exact JSON/Markdown reports, post-edit byte snapshots, and disposable Git workspaces were retained locally but are intentionally ignored by Git because provider output can contain machine-specific paths or context. Reproduce them with:

```bash
agent-file-integrity-litmus run --adapter codex-cli --allow-live --repetitions 2 --output /tmp/codex-results
agent-file-integrity-litmus run --adapter opencode-cli --allow-live --repetitions 2 --output /tmp/opencode-results
```
