#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SAFE_ENV_KEYS = (
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "PYTHONPATH",
    "PYTHONIOENCODING",
    "TEMP",
    "TERM",
    "TMP",
    "TMPDIR",
    "TZ",
)
DEFAULT_TARGETS = [
    "eval",
    "eval-suite",
    "route-scorecard",
    "route-confusion-check",
    "description-optimization",
    "description-optimization-check",
    "promotion-check",
    "python-compat-check",
    "architecture-maintainability-check",
    "yao-cli-check",
    "skill-overview-check",
    "skill-interpretation-check",
    "skill-report-metrics-check",
    "skill-report-charts-check",
    "html-rendering-check",
    "skill-ir-check",
    "compiler-check",
    "output-eval-check",
    "output-execution-check",
    "output-review-kit-check",
    "output-review-adjudication-check",
    "runtime-conformance-check",
    "runtime-permission-check",
    "trust-check",
    "skill-atlas-check",
    "registry-audit-check",
    "package-verify-check",
    "install-simulation-check",
    "upgrade-check",
    "review-viewer-check",
    "review-studio-check",
    "skill-os2-audit-check",
    "skill-os2-coverage-check",
    "world-class-evidence-check",
    "world-class-ledger-check",
    "world-class-intake-check",
    "world-class-submission-review-check",
    "world-class-runbook-check",
    "world-class-claim-guard-check",
    "benchmark-reproducibility-check",
    "evidence-consistency-check",
    "feedback-check",
    "adaptation-safety-check",
    "adoption-drift-check",
    "telemetry-import-check",
    "telemetry-emit-check",
    "telemetry-hooks-check",
    "telemetry-native-host-check",
    "review-waivers-check",
    "review-annotations-check",
    "baseline-compare-check",
    "reference-scan-check",
    "github-benchmark-scan-check",
    "reference-synthesis-check",
    "output-risk-profile-check",
    "artifact-design-profile-check",
    "prompt-quality-profile-check",
    "system-model-check",
    "iteration-directions-check",
    "description-drift-history",
    "iteration-ledger",
    "regression-history",
    "context-reports",
    "portability-report",
    "portability-check",
    "failure-regression-check",
    "package-check",
    "package-failure-check",
    "security-boundary-check",
    "local-install-sync-check",
    "snapshot-check",
    "validate",
    "lint",
    "governance-check",
    "resource-boundary-check",
    "quality-check",
]


def tail_text(path: Path, max_lines: int) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) <= max_lines:
        return "\n".join(lines)
    hidden = len(lines) - max_lines
    tail = "\n".join(lines[-max_lines:])
    return f"... truncated {hidden} earlier lines ...\n{tail}"


def run_target(target: str, index: int, total: int, tail_lines: int) -> None:
    print(f"[{index}/{total}] {target}")
    start = time.perf_counter()
    with tempfile.NamedTemporaryFile(prefix=f"ci-{target}-", suffix=".log", delete=False) as handle:
        log_path = Path(handle.name)
    child_env = {key: os.environ[key] for key in SAFE_ENV_KEYS if key in os.environ}
    child_env["CI"] = "1"
    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            proc = subprocess.run(
                ["make", "--silent", target],
                cwd=ROOT,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                env=child_env,
            )
        elapsed = time.perf_counter() - start
        if proc.returncode != 0:
            print(f"FAILED {target} ({elapsed:.1f}s)")
            print(f"--- {target} log ---")
            print(tail_text(log_path, tail_lines))
            raise SystemExit(proc.returncode)
        print(f"OK {target} ({elapsed:.1f}s)")
    finally:
        if log_path.exists():
            log_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run CI test targets with compact logging.")
    parser.add_argument("--tail-lines", type=int, default=200, help="How many log lines to show on failure.")
    parser.add_argument("targets", nargs="*", default=DEFAULT_TARGETS, help="Optional target override.")
    args = parser.parse_args()

    total = len(args.targets)
    for index, target in enumerate(args.targets, start=1):
        run_target(target, index, total, args.tail_lines)
    print(f"Completed {total} CI targets.")


if __name__ == "__main__":
    main()
