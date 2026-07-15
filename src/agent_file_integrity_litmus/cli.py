from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from .adapters import run_adapter
from .core import (
    FIXTURES,
    PROMPT,
    create_fixture,
    create_stale_fixture,
    inject_concurrent_change,
    render_json,
    render_markdown,
    score_fixture,
    score_stale_fixture,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-file-integrity-litmus")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("fixtures", help="list fixture names")

    create = subparsers.add_parser("create", help="create a disposable byte-preservation fixture repository")
    create.add_argument("output", type=Path)

    score = subparsers.add_parser("score", help="score an edited fixture repository byte-for-byte")
    score.add_argument("fixture_root", type=Path)
    score.add_argument("--format", choices=("json", "markdown"), default="json")

    run = subparsers.add_parser("run", help="run a guarded live client adapter in disposable repositories")
    run.add_argument("--adapter", choices=("codex-cli", "opencode-cli"), required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--repetitions", type=int, default=1)
    run.add_argument("--allow-live", action="store_true")
    run.add_argument("--timeout-seconds", type=int, default=600)
    run.add_argument("--codex-bin", default="codex")
    run.add_argument("--opencode-bin", default="opencode")

    stale_create = subparsers.add_parser("stale-create", help="create the deterministic stale-write fixture")
    stale_create.add_argument("output", type=Path)

    stale_inject = subparsers.add_parser("stale-inject", help="inject the concurrent external edit")
    stale_inject.add_argument("fixture_root", type=Path)

    stale_score = subparsers.add_parser("stale-score", help="score rejection, merge, or stale overwrite")
    stale_score.add_argument("fixture_root", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "fixtures":
        print("\n".join(FIXTURES))
        return 0
    if args.command == "create":
        create_fixture(args.output)
        print(PROMPT)
        return 0
    if args.command == "score":
        results = score_fixture(args.fixture_root)
        output = render_markdown(results, args.fixture_root) if args.format == "markdown" else render_json(results, args.fixture_root)
        print(output)
        return 1 if any(result.status == "FAIL" for result in results) else 0
    if args.command == "run":
        if not args.allow_live:
            executable = shutil.which("codex" if args.adapter == "codex-cli" else "opencode")
            print(f"adapter executable: {executable or 'not found'}")
            print("Live execution may consume model quota. Re-run with --allow-live to opt in.")
            return 2
        if not 1 <= args.repetitions <= 10:
            raise ValueError("repetitions must be between 1 and 10")
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        exit_code = 0
        for number in range(1, args.repetitions + 1):
            result = run_adapter(
                args.adapter,
                args.output / f"run-{number:02d}",
                codex_bin=args.codex_bin,
                opencode_bin=args.opencode_bin,
                timeout_seconds=args.timeout_seconds,
            )
            print(
                f"run-{number:02d}: {result.passed}/{len(result.results)} PASS; "
                f"process return code {result.returncode}; artifacts {result.artifacts}"
            )
            if result.returncode != 0 or result.passed != len(result.results):
                exit_code = 1
        return exit_code
    if args.command == "stale-create":
        create_stale_fixture(args.output)
        print("Read stale-write.txt now, but do not write it yet. Then run stale-inject before attempting the edit.")
        return 0
    if args.command == "stale-inject":
        inject_concurrent_change(args.fixture_root)
        print("Concurrent external edit injected. The stale client may now attempt TARGET -> UPDATED.")
        return 0
    if args.command == "stale-score":
        result = score_stale_fixture(args.fixture_root)
        print(json.dumps(asdict(result), indent=2))
        return 0 if result.status == "PASS" else 1
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileExistsError, FileNotFoundError, RuntimeError, ValueError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(2)
