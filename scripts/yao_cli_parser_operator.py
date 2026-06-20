#!/usr/bin/env python3
"""Operator UX command declarations for the Yao CLI parser."""

import argparse
from collections.abc import Callable


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao_cli_parser.py to keep operator UX command declarations out of the main parser module."


def _handler(command_handlers: dict[str, Callable[[argparse.Namespace], int]], name: str) -> Callable[[argparse.Namespace], int]:
    if name not in command_handlers:
        raise KeyError(f"Missing CLI command handler: {name}")
    return command_handlers[name]


def add_operator_commands(
    subparsers: argparse._SubParsersAction,
    command_handlers: dict[str, Callable[[argparse.Namespace], int]],
) -> None:
    install_status_cmd = subparsers.add_parser(
        "install-status",
        help="Diagnose whether yao-meta-skill is active in Codex/Cortex, .agents, or a disabled mirror.",
    )
    install_status_cmd.add_argument("--skill-name", default="yao-meta-skill")
    install_status_cmd.add_argument("--expected-source", default=".")
    install_status_cmd.add_argument("--codex-root", default="~/.codex/skills")
    install_status_cmd.add_argument("--agents-root", default="~/.agents/skills")
    install_status_cmd.add_argument("--disabled-root", default="~/.agents/skills.disabled")
    install_status_cmd.set_defaults(func=_handler(command_handlers, "command_install_status"))

    localized_docs_cmd = subparsers.add_parser(
        "localized-doc-sync-check",
        help="Check that localized README docs contain the public homepage sections introduced in README.md.",
    )
    localized_docs_cmd.add_argument("--source", default="README.md")
    localized_docs_cmd.add_argument("--localized", default="docs/README.zh-CN.md")
    localized_docs_cmd.add_argument(
        "--pair",
        action="append",
        default=[],
        help="Custom sync marker in key::source-marker::localized-marker form. Replaces defaults when present.",
    )
    localized_docs_cmd.add_argument("--output-json")
    localized_docs_cmd.add_argument("--output-md")
    localized_docs_cmd.set_defaults(func=_handler(command_handlers, "command_localized_doc_sync_check"))

    pr_review_cmd = subparsers.add_parser(
        "pr-review-report",
        help="Build a read-only GitHub PR review report with mergeability, checks, files, and suggested commands.",
    )
    pr_review_cmd.add_argument("pr")
    pr_review_cmd.add_argument("--repo")
    pr_review_cmd.add_argument("--require-checks", action="store_true")
    pr_review_cmd.add_argument("--output-json")
    pr_review_cmd.add_argument("--output-md")
    pr_review_cmd.set_defaults(func=_handler(command_handlers, "command_pr_review_report"))
