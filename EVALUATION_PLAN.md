# Evaluation Plan

## Oracle

Each fixture contains one ASCII `TARGET` marker. The expected result replaces only those six bytes with `UPDATED`. A fixture passes only when all resulting bytes and the expected POSIX mode match exactly.

## Cases

1. CRLF text.
2. UTF-8 text with BOM.
3. Windows-1252 text with CRLF.
4. UTF-8 Cyrillic and emoji.
5. Text without a final newline.
6. Executable shell script.
7. Concurrent external edit between client read and write, with deterministic `REJECTED`, `MERGED`, and `STALE_OVERWRITE` outcomes.

## Baselines and clients

- Baseline: direct byte replacement preserving mode.
- Client adapters: guarded Codex CLI and opencode CLI using equivalent prompts and isolated disposable repositories.
- Second platform: Windows preferred because most encoding pain is Windows-specific; Linux is useful for package/CI coverage but does not replace Windows encoding validation.

## Required evidence before publication

- three unrelated real-world file cases;
- two client ecosystems;
- at least two repeated runs per adapter;
- exact raw result artifacts and client versions;
- a concurrent-change case with an unambiguous pass/fail oracle; live-client race automation is not claimed without a stable client hook;
- documented native-tool failures and agent recovery paths;
- package build/install, CI, security, limitations, and discoverability gates.

## Stop condition for next run

Run the guarded Codex/opencode matrix at least twice, save exact post-edit bytes, and score the deterministic stale-write fixture. Keep live-client race behavior out of scope unless a client exposes a stable read/write hook. Then validate the package and byte oracles on Windows before public release.
