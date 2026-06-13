#!/usr/bin/env python3
import argparse
import io
import json
import token
import tokenize
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Checks repository Python source for syntax that can pass locally but fail on the supported CI interpreter."

EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".previews",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "dist",
    "node_modules",
    "venv",
}
MAX_FILE_BYTES = 1_000_000


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def resolve_path(raw_path: str, root: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def is_ignored(path: Path, root: Path) -> bool:
    try:
        parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == "tests" and parts[1].startswith("tmp"):
        return True
    return False


def expand_scan_paths(root: Path, raw_paths: list[str]) -> list[Path]:
    candidates: list[Path] = []
    explicit_paths = bool(raw_paths)
    if raw_paths:
        for raw_path in raw_paths:
            path = resolve_path(raw_path, root)
            if path.is_dir():
                candidates.extend(path.rglob("*.py"))
            elif path.exists():
                candidates.append(path)
    else:
        candidates.extend(root.rglob("*.py"))
    files = []
    for path in candidates:
        if not path.is_file() or path.is_symlink() or path.suffix != ".py":
            continue
        if not explicit_paths and is_ignored(path, root):
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        files.append(path)
    return sorted(set(files), key=lambda item: rel_path(item, root))


def issue(path: Path, root: Path, line: int, column: int, rule: str, message: str, excerpt: str = "") -> dict[str, Any]:
    return {
        "path": rel_path(path, root),
        "line": line,
        "column": column,
        "rule": rule,
        "message": message,
        "excerpt": excerpt.strip()[:220],
    }


def compile_issues(path: Path, root: Path, source: str) -> list[dict[str, Any]]:
    try:
        compile(source, str(path), "exec")
    except SyntaxError as exc:
        return [
            issue(
                path,
                root,
                exc.lineno or 0,
                exc.offset or 0,
                "current-python-syntax",
                str(exc.msg),
                exc.text or "",
            )
        ]
    return []


def token_name(token_type: int) -> str:
    return token.tok_name.get(token_type, "")


def scan_modern_fstring_tokens(path: Path, root: Path, source: str) -> tuple[bool, list[dict[str, Any]]]:
    findings: list[dict[str, Any]] = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return False, findings
    has_modern_fstring_tokens = any(token_name(item.type) == "FSTRING_START" for item in tokens)
    if not has_modern_fstring_tokens:
        return False, findings
    fstring_depth = 0
    expression_depth = 0
    for item in tokens:
        name = token_name(item.type)
        if name == "FSTRING_START":
            fstring_depth += 1
            expression_depth = 0
            continue
        if name == "FSTRING_END":
            fstring_depth = max(0, fstring_depth - 1)
            expression_depth = 0
            continue
        if not fstring_depth:
            continue
        if item.type == token.OP and item.string == "{":
            expression_depth += 1
            continue
        if item.type == token.OP and item.string == "}":
            expression_depth = max(0, expression_depth - 1)
            continue
        if expression_depth > 0 and "\\" in item.string:
            findings.append(
                issue(
                    path,
                    root,
                    item.start[0],
                    item.start[1] + 1,
                    "fstring-expression-backslash",
                    "Python 3.11 rejects backslashes inside f-string expressions.",
                    item.line,
                )
            )
    return True, findings


def split_string_token(token_text: str) -> tuple[str, str] | None:
    index = 0
    while index < len(token_text) and token_text[index].isalpha():
        index += 1
    prefix = token_text[:index].lower()
    if "f" not in prefix:
        return None
    quote = ""
    for candidate in ('"""', "'''", '"', "'"):
        if token_text[index:].startswith(candidate):
            quote = candidate
            break
    if not quote or not token_text.endswith(quote):
        return None
    return prefix, token_text[index + len(quote) : -len(quote)]


def scan_legacy_fstring_body(path: Path, root: Path, token_text: str, start_line: int, start_column: int) -> list[dict[str, Any]]:
    parsed = split_string_token(token_text)
    if not parsed:
        return []
    _, body = parsed
    findings: list[dict[str, Any]] = []
    expression_depth = 0
    line = start_line
    column = start_column
    index = 0
    while index < len(body):
        char = body[index]
        next_char = body[index + 1] if index + 1 < len(body) else ""
        if expression_depth == 0:
            if char == "{" and next_char == "{":
                index += 2
                column += 2
                continue
            if char == "{" and next_char != "{":
                expression_depth = 1
        else:
            if char == "\\":
                findings.append(
                    issue(
                        path,
                        root,
                        line,
                        column + 1,
                        "fstring-expression-backslash",
                        "Python 3.11 rejects backslashes inside f-string expressions.",
                        token_text,
                    )
                )
            elif char == "{":
                expression_depth += 1
            elif char == "}":
                expression_depth = max(0, expression_depth - 1)
        if char == "\n":
            line += 1
            column = 0
        else:
            column += 1
        index += 1
    return findings


def fstring_compat_issues(path: Path, root: Path, source: str) -> list[dict[str, Any]]:
    handled, findings = scan_modern_fstring_tokens(path, root, source)
    if handled:
        return findings
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for item in tokens:
            if item.type == token.STRING:
                findings.extend(scan_legacy_fstring_body(path, root, item.string, item.start[0], item.start[1]))
    except tokenize.TokenError:
        return findings
    return findings


def check_file(path: Path, root: Path) -> dict[str, Any]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues = [issue(path, root, 0, 0, "read-error", str(exc))]
    else:
        issues = compile_issues(path, root, source)
        issues.extend(fstring_compat_issues(path, root, source))
    return {
        "path": rel_path(path, root),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def build_report(root: Path, raw_paths: list[str], target_python: str, generated_at: str) -> dict[str, Any]:
    files = expand_scan_paths(root, raw_paths)
    checked = [check_file(path, root) for path in files]
    issues = [item for file_report in checked for item in file_report["issues"]]
    syntax_error_count = sum(1 for item in issues if item["rule"] == "current-python-syntax")
    fstring_count = sum(1 for item in issues if item["rule"] == "fstring-expression-backslash")
    return {
        "schema_version": "1.0",
        "ok": not issues,
        "generated_at": generated_at,
        "root": rel_path(root, ROOT),
        "summary": {
            "target_python": target_python,
            "file_count": len(checked),
            "issue_count": len(issues),
            "syntax_error_count": syntax_error_count,
            "fstring_311_violation_count": fstring_count,
            "decision": "pass" if not issues else "block-python-compat",
        },
        "rules": [
            {
                "key": "current-python-syntax",
                "reason": "Every scanned Python source file must compile under the running interpreter.",
            },
            {
                "key": "fstring-expression-backslash",
                "reason": "Python 3.11 rejects backslashes inside f-string expressions; keep escaping outside the expression.",
            },
        ],
        "files": checked,
        "issues": issues,
        "artifacts": {
            "json": "reports/python_compatibility.json",
            "markdown": "reports/python_compatibility.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Python Compatibility",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- target python: `{summary['target_python']}`",
        f"- files scanned: `{summary['file_count']}`",
        f"- issues: `{summary['issue_count']}`",
        f"- syntax errors: `{summary['syntax_error_count']}`",
        f"- f-string 3.11 violations: `{summary['fstring_311_violation_count']}`",
        "",
        "This report catches Python syntax and compatibility hazards that can pass on a newer local interpreter but fail in the supported CI/runtime interpreter.",
        "",
        "## Issues",
        "",
        "| Path | Line | Rule | Message |",
        "| --- | ---: | --- | --- |",
    ]
    if report["issues"]:
        for item in report["issues"]:
            message = str(item["message"]).replace("|", "\\|")
            lines.append(f"| `{item['path']}` | {item['line']} | `{item['rule']}` | {message} |")
    else:
        lines.append("| `none` | 0 | `none` | none |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Python source compatibility for supported CI/runtime versions.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--path", action="append", default=[], help="Optional file or directory to scan relative to skill_dir.")
    parser.add_argument("--target-python", default="3.11")
    parser.add_argument("--output-json", default="reports/python_compatibility.json")
    parser.add_argument("--output-md", default="reports/python_compatibility.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    root = Path(args.skill_dir).resolve()
    report = build_report(root, args.path, args.target_python, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = root / output_json
    if not output_md.is_absolute():
        output_md = root / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
