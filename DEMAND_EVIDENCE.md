# Demand Evidence

## Repeated public pain

- Claude Code issue #7332 reports corrupted Chinese output and links related failures across Windows-1252, Turkish, Nordic, Cyrillic, and box-drawing text: https://github.com/anthropics/claude-code/issues/7332
- Codex issue #4013 reports UTF-8 emoji becoming CP1252/Latin-1 mojibake in the VS Code extension: https://github.com/openai/codex/issues/4013
- Codex issue #4574 reports Chinese and Portuguese UTF-8 corruption on Windows: https://github.com/openai/codex/issues/4574
- Codex issue #23044 reports a PowerShell 5.1 path that mojibakes UTF-8 files on non-English Windows locales: https://github.com/openai/codex/issues/23044
- Codex issue #5807 reports stale-read overwrites that discard newer manual edits: https://github.com/openai/codex/issues/5807
- Cursor report 150828 documents CRLF state being overwritten after restart: https://forum.cursor.com/t/ai-edited-files-get-corrupted-crlf-lf-conversion-on-ide-restart-causing-data-loss-risk/150828/3
- Cursor report 150566 reports an update changing line endings across hundreds of files and affecting UTF-8-with-signature content: https://forum.cursor.com/t/cursor-update-changed-line-endings-in-entire-codebase-without-consent/150566
- Cline issue #1251 reports failures reading files containing emoji: https://github.com/cline/cline/issues/1251
- JetBrains LLM-29314 reports Codex changing line endings or encoding so every line appears replaced: https://youtrack.jetbrains.com/projects/LLM/issues/LLM-29314/AI-Assistant-with-Codex-sometimes-changes-line-endings-or-file-encoding-leading-to-it-showing-all-lines-as-removed-and-added-in

## Alternatives and insufficiency

- Git attributes and EditorConfig declare conversion policy, but do not run behavioral checks against a coding-agent edit path.
- `pi-mono` and Cline contain client-specific BOM, EOL, encoding, and manual-edit safeguards. They do not compare installed clients through a shared fixture contract.
- Encoding-safe edit servers can preserve bytes and reject stale writes with base hashes. They replace the edit mechanism; they do not show whether an existing client path is safe.
- `edit-guard` checks sequential edits, line-count loss, and formatter mismatch through Claude Code hooks. It does not cover encoding, BOM, CRLF, file mode, or cross-client comparison: https://github.com/ceaksan/edit-guard
- SWE-Edit and general coding benchmarks measure task success, edit success, or efficiency rather than exact byte/file-metadata preservation: https://github.com/microsoft/SWE-Edit

## Targeted validation on 2026-07-14

The same six-fixture request was run against Codex CLI 0.144.1 and opencode 1.16.2 on macOS.

- Byte-safe baseline: 6/6.
- opencode native Read/Edit path: 5/6. The Windows-1252 `é` byte (`e9`) became the UTF-8 replacement character (`ef bf bd`).
- Codex native `apply_patch`: could not read the Windows-1252 file and initially changed the edited CRLF line to LF and added a final newline. The agent detected both violations and used Vim binary-mode workarounds; final outcome was 6/6.

This proves a client-neutral fixture can distinguish native edit paths and recovery behavior. It does not yet prove concurrent stale-write rejection or Windows-host behavior.

## Value gate

`PASS` for spec/build. The target user, job, repeated pain, alternative insufficiency, and first 5–30 minute outcome are concrete. Publication remains gated on guarded adapters, repeated runs, concurrent-write validation, and Windows or equivalent second-platform evidence.
