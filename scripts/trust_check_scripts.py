#!/usr/bin/env python3
import ast
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Static script inventory helpers imported by trust_check.py."
INTERNAL_SCRIPT_INTERFACE = "internal-module"


def relpath(skill_dir: Path, path: Path) -> str:
    return str(path.relative_to(skill_dir))


def script_inventory(skill_dir: Path) -> list[dict[str, Any]]:
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.exists():
        return []
    inventory = []
    for path in sorted(scripts_dir.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        flags = script_flags(text)
        interface = script_interface(text)
        urls = extract_url_literals(text)
        inventory.append(
            {
                "path": relpath(skill_dir, path),
                "interface": interface["name"],
                "interface_declared": interface["declared"],
                "interface_reason": interface["reason"],
                "has_argparse": "argparse" in text,
                "has_main_guard": 'if __name__ == "__main__"' in text,
                "uses_input": flags["uses_input"],
                "uses_network": flags["uses_network"],
                "uses_file_write": flags["uses_file_write"],
                "uses_subprocess": flags["uses_subprocess"],
                "network_urls": urls,
                "network_hosts": sorted({urlparse(url).hostname or "" for url in urls if urlparse(url).hostname}),
            }
        )
    return inventory


def string_assignment(tree: ast.Module, variable_name: str) -> str:
    for node in tree.body:
        value_node = None
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == variable_name for target in node.targets):
                value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == variable_name:
                value_node = node.value
        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            return value_node.value
    return ""


def script_interface(text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        match = re.search(r"SCRIPT_INTERFACE\s*=\s*['\"]([^'\"]+)['\"]", text)
        reason_match = re.search(r"SCRIPT_INTERFACE_REASON\s*=\s*['\"]([^'\"]+)['\"]", text)
        name = match.group(1) if match else "cli"
        reason = reason_match.group(1) if reason_match else ""
        return {"name": name, "declared": bool(match), "reason": reason}

    name = string_assignment(tree, "SCRIPT_INTERFACE")
    reason = string_assignment(tree, "SCRIPT_INTERFACE_REASON")
    if name:
        return {"name": name, "declared": True, "reason": reason}
    return {"name": "cli", "declared": False, "reason": "Default CLI classification; add SCRIPT_INTERFACE for internal modules."}


def extract_url_literals(text: str) -> list[str]:
    values: list[str] = []
    try:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                values.append(node.value)
    except SyntaxError:
        values = re.findall(r"['\"]([^'\"]+)['\"]", text)

    urls = []
    seen = set()
    for value in values:
        for match in re.finditer(r"https?://[^\s'\"<>]+", value):
            url = match.group(0).rstrip(").,]")
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def script_flags(text: str) -> dict[str, bool]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {
            "uses_input": bool(re.search(r"\b(?:input|getpass)\s*\(", text)),
            "uses_network": bool(re.search(r"\b(?:urlopen|Request)\s*\(|\brequests\.", text)),
            "uses_file_write": bool(
                re.search(r"\.(?:write_text|write_bytes|mkdir|unlink)\s*\(", text)
                or re.search(r"\b(?:open)\s*\([^)]*['\"][wa+x]", text)
                or "shutil.rmtree" in text
            ),
            "uses_subprocess": "subprocess." in text,
        }
    call_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    calls = [call_name(node.func) for node in call_nodes]
    return {
        "uses_input": any(name in {"input", "getpass.getpass"} or name.endswith(".getpass") for name in calls),
        "uses_network": any(name in {"urlopen", "Request"} or name.startswith("requests.") for name in calls),
        "uses_file_write": any(is_file_write_call(node, call_name(node.func)) for node in call_nodes),
        "uses_subprocess": any(name.startswith("subprocess.") for name in calls),
    }


def is_file_write_call(node: ast.Call, name: str) -> bool:
    if name.endswith((".write_text", ".write_bytes", ".mkdir", ".unlink", ".rmdir")):
        return True
    if name in {"shutil.copy", "shutil.copy2", "shutil.copytree", "shutil.move", "shutil.rmtree"}:
        return True
    if name == "zipfile.ZipFile":
        return True
    if name in {"open", "Path.open"} or name.endswith(".open"):
        args = list(node.args)
        keywords = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        mode_node = args[1] if len(args) > 1 else keywords.get("mode")
        if isinstance(mode_node, ast.Constant) and isinstance(mode_node.value, str):
            return any(flag in mode_node.value for flag in ("w", "a", "x", "+"))
    return False
