#!/usr/bin/env python3
import argparse
import ast
import hashlib
import json
import subprocess
import sys
import re
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["agents", "docs", "evals", "references", "runtime", "scripts", "security", "skill-ir", "templates"]
ROOT_FILES = ["SKILL.md", "README.md", "manifest.json", "requirements-ci.txt", "Makefile"]
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".py", ".sh", ".txt", ".toml"}
PACKAGE_HASH_SCOPE = "source-contract-without-generated-reports"
INTERNAL_SCRIPT_INTERFACE = "internal-module"
NETWORK_POLICY_REL_PATH = "security/network_policy.json"
PERMISSION_POLICY_REL_PATH = "security/permission_policy.json"
HELP_SMOKE_TIMEOUT_SECONDS = 5.0
PERMISSION_CAPABILITIES = ("network", "file_write", "subprocess", "interactive")
PERMISSION_TARGETS = ("openai", "claude", "generic", "vscode")
SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
]


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def iter_scan_files(skill_dir: Path) -> list[Path]:
    files = []
    for rel in ROOT_FILES:
        path = skill_dir / rel
        if path.exists() and path.is_file():
            files.append(path)
    for rel in SCAN_DIRS:
        folder = skill_dir / rel
        if not folder.exists():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if path.suffix in TEXT_SUFFIXES and path.stat().st_size <= 1_000_000:
                files.append(path)
    return sorted(set(files))


def relpath(skill_dir: Path, path: Path) -> str:
    return str(path.relative_to(skill_dir))


def scan_secrets(skill_dir: Path, files: list[Path]) -> list[dict[str, Any]]:
    findings = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for name, pattern in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append({"type": name, "path": relpath(skill_dir, path), "line": line})
    return findings


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


def dependency_status(skill_dir: Path) -> dict[str, Any]:
    candidates = ["requirements-ci.txt", "requirements.txt", "pyproject.toml", "package-lock.json", "uv.lock", "poetry.lock"]
    present = [name for name in candidates if (skill_dir / name).exists()]
    pinned = []
    unpinned = []
    requirements = skill_dir / "requirements-ci.txt"
    if requirements.exists():
        for line in requirements.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "==" in stripped or " @ " in stripped:
                pinned.append(stripped)
            else:
                unpinned.append(stripped)
    return {"present": present, "pinned": pinned, "unpinned": unpinned}


def script_capability_paths(scripts: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {
        "network": [item["path"] for item in scripts if item["uses_network"]],
        "file_write": [item["path"] for item in scripts if item.get("uses_file_write", False)],
        "subprocess": [item["path"] for item in scripts if item["uses_subprocess"]],
        "interactive": [item["path"] for item in scripts if item["uses_input"]],
    }


def load_network_policy(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / NETWORK_POLICY_REL_PATH
    if not path.exists():
        return {"present": False, "path": NETWORK_POLICY_REL_PATH, "scripts": {}}
    payload = load_json(path)
    scripts = payload.get("scripts", {})
    return {
        "present": True,
        "path": NETWORK_POLICY_REL_PATH,
        "schema_version": payload.get("schema_version", ""),
        "default_policy": payload.get("default_policy", {}),
        "scripts": scripts if isinstance(scripts, dict) else {},
    }


def load_permission_policy(skill_dir: Path) -> dict[str, Any]:
    path = skill_dir / PERMISSION_POLICY_REL_PATH
    if not path.exists():
        return {"present": False, "path": PERMISSION_POLICY_REL_PATH, "capabilities": {}}
    payload = load_json(path)
    capabilities = payload.get("capabilities", {})
    return {
        "present": True,
        "path": PERMISSION_POLICY_REL_PATH,
        "schema_version": payload.get("schema_version", ""),
        "reviewed_at": payload.get("reviewed_at", ""),
        "capabilities": capabilities if isinstance(capabilities, dict) else {},
    }


def parse_iso_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def permission_governance_status(skill_dir: Path, scripts: list[dict[str, Any]], today: date | None = None) -> dict[str, Any]:
    policy = load_permission_policy(skill_dir)
    today = today or date.today()
    capability_paths = script_capability_paths(scripts)
    required = {name: paths for name, paths in capability_paths.items() if paths}
    approvals = []
    missing = []
    invalid = []
    expired = []
    approved = []

    for name, paths in required.items():
        entry = policy["capabilities"].get(name, {}) if policy["present"] else {}
        if not isinstance(entry, dict) or not entry:
            missing.append(name)
            approvals.append({"capability": name, "status": "missing", "scripts": paths, "validation": ["approval entry is missing"]})
            continue
        validation = []
        if entry.get("decision") != "approved":
            validation.append("decision must be approved")
        if not entry.get("reviewer"):
            validation.append("reviewer is required")
        if len(str(entry.get("reason", ""))) < 30:
            validation.append("reason must be at least 30 characters")
        if not entry.get("scope"):
            validation.append("scope is required")
        expires_at = parse_iso_date(entry.get("expires_at"))
        if expires_at is None:
            validation.append("expires_at must be ISO date")
        target_enforcement = entry.get("target_enforcement", {})
        if not isinstance(target_enforcement, dict):
            validation.append("target_enforcement must be an object")
            target_enforcement = {}
        missing_targets = [target for target in PERMISSION_TARGETS if not target_enforcement.get(target)]
        if missing_targets:
            validation.append(f"target_enforcement missing: {', '.join(missing_targets)}")
        if validation:
            invalid.append(name)
            status = "invalid"
        elif expires_at is not None and expires_at < today:
            expired.append(name)
            status = "expired"
        else:
            approved.append(name)
            status = "approved"
        approvals.append(
            {
                "capability": name,
                "status": status,
                "scripts": paths,
                "reviewer": str(entry.get("reviewer", "")),
                "scope": str(entry.get("scope", "")),
                "reason": str(entry.get("reason", "")),
                "expires_at": str(entry.get("expires_at", "")),
                "evidence": entry.get("evidence", []) if isinstance(entry.get("evidence", []), list) else [],
                "target_enforcement": target_enforcement,
                "validation": validation,
            }
        )

    return {
        "present": policy["present"],
        "path": policy["path"],
        "schema_version": policy.get("schema_version", ""),
        "reviewed_at": policy.get("reviewed_at", ""),
        "required_capabilities": sorted(required),
        "approved_capabilities": sorted(approved),
        "missing_capabilities": sorted(missing),
        "invalid_capabilities": sorted(invalid),
        "expired_capabilities": sorted(expired),
        "approval_count": len(approved),
        "required_count": len(required),
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "expired_count": len(expired),
        "approvals": approvals,
    }


def network_policy_status(skill_dir: Path, scripts: list[dict[str, Any]]) -> dict[str, Any]:
    policy = load_network_policy(skill_dir)
    network_scripts = [item for item in scripts if item["uses_network"]]
    covered = []
    missing = []
    mismatches = []
    for item in network_scripts:
        entry = policy["scripts"].get(item["path"], {}) if policy["present"] else {}
        if not isinstance(entry, dict) or not entry:
            missing.append(item["path"])
            continue
        allowed_hosts = set(entry.get("allowed_hosts") or [])
        if not allowed_hosts:
            mismatches.append(
                {
                    "path": item["path"],
                    "reason": "allowed_hosts is empty",
                    "observed_hosts": item["network_hosts"],
                    "allowed_hosts": [],
                }
            )
            continue
        observed_hosts = set(item.get("network_hosts") or [])
        unexpected_hosts = sorted(observed_hosts - allowed_hosts)
        if unexpected_hosts:
            mismatches.append(
                {
                    "path": item["path"],
                    "reason": "observed HTTPS hosts are not declared in policy",
                    "observed_hosts": sorted(observed_hosts),
                    "allowed_hosts": sorted(allowed_hosts),
                    "unexpected_hosts": unexpected_hosts,
                }
            )
            continue
        covered.append(item["path"])
    return {
        "present": policy["present"],
        "path": policy["path"],
        "schema_version": policy.get("schema_version", ""),
        "network_script_count": len(network_scripts),
        "covered_scripts": covered,
        "missing_scripts": missing,
        "mismatches": mismatches,
        "default_policy": policy.get("default_policy", {}),
    }


def interface_trust(skill_dir: Path) -> dict[str, Any]:
    interface = load_yaml(skill_dir / "agents" / "interface.yaml")
    trust = interface.get("compatibility", {}).get("trust", {})
    return {
        "source_tier": trust.get("source_tier", ""),
        "remote_inline_execution": trust.get("remote_inline_execution", ""),
        "remote_metadata_policy": trust.get("remote_metadata_policy", ""),
    }


def package_digest(files: list[Path], skill_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in files:
        rel = relpath(skill_dir, path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def help_smoke_candidates(scripts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in scripts
        if item["interface"] != INTERNAL_SCRIPT_INTERFACE and item["has_argparse"]
    ]


def run_help_smoke_checks(skill_dir: Path, scripts: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidates = help_smoke_candidates(scripts)
    skipped = [
        {
            "path": item["path"],
            "reason": "internal module" if item["interface"] == INTERNAL_SCRIPT_INTERFACE else "missing argparse/help surface",
        }
        for item in scripts
        if item not in candidates
    ]
    results = []
    for item in candidates:
        command = [sys.executable, item["path"], "--help"]
        try:
            proc = subprocess.run(
                command,
                cwd=skill_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            output = f"{proc.stdout}\n{proc.stderr}".lower()
            has_help_text = "usage:" in output or "--help" in output
            results.append(
                {
                    "path": item["path"],
                    "command": f"python3 {item['path']} --help",
                    "returncode": proc.returncode,
                    "timed_out": False,
                    "passed": proc.returncode == 0 and has_help_text,
                    "has_help_text": has_help_text,
                    "stdout_excerpt": proc.stdout.strip()[:240],
                    "stderr_excerpt": proc.stderr.strip()[:240],
                }
            )
        except subprocess.TimeoutExpired as exc:
            results.append(
                {
                    "path": item["path"],
                    "command": f"python3 {item['path']} --help",
                    "returncode": None,
                    "timed_out": True,
                    "passed": False,
                    "has_help_text": False,
                    "stdout_excerpt": (exc.stdout or "").strip()[:240] if isinstance(exc.stdout, str) else "",
                    "stderr_excerpt": (exc.stderr or "").strip()[:240] if isinstance(exc.stderr, str) else "",
                }
            )
    failed = [item for item in results if not item["passed"]]
    return {
        "enabled": True,
        "timeout_seconds": timeout,
        "candidate_count": len(candidates),
        "checked_count": len(results),
        "passed_count": len(results) - len(failed),
        "failed_count": len(failed),
        "skipped_count": len(skipped),
        "failed_scripts": [item["path"] for item in failed],
        "results": results,
        "skipped": skipped,
    }


def disabled_help_smoke_status(scripts: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    candidates = help_smoke_candidates(scripts)
    return {
        "enabled": False,
        "timeout_seconds": timeout,
        "candidate_count": len(candidates),
        "checked_count": 0,
        "passed_count": 0,
        "failed_count": 0,
        "skipped_count": len(scripts),
        "failed_scripts": [],
        "results": [],
        "skipped": [{"path": item["path"], "reason": "help smoke disabled"} for item in scripts],
    }


def build_trust_report(skill_dir: Path, run_help_smoke: bool = True, help_smoke_timeout: float = HELP_SMOKE_TIMEOUT_SECONDS) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    files = iter_scan_files(skill_dir)
    secrets = scan_secrets(skill_dir, files)
    scripts = script_inventory(skill_dir)
    deps = dependency_status(skill_dir)
    network_policy = network_policy_status(skill_dir, scripts)
    help_smoke = (
        run_help_smoke_checks(skill_dir, scripts, help_smoke_timeout)
        if run_help_smoke
        else disabled_help_smoke_status(scripts, help_smoke_timeout)
    )
    permission_governance = permission_governance_status(skill_dir, scripts)
    trust = interface_trust(skill_dir)
    failures = []
    warnings = []

    if secrets:
        failures.append(f"High-risk secret patterns found: {len(secrets)}")
    if trust.get("remote_inline_execution") not in {"forbid", "deny", "false"}:
        failures.append("remote_inline_execution must be forbid for governed release")
    if deps["unpinned"]:
        warnings.append(f"Unpinned dependency entries: {', '.join(deps['unpinned'])}")
    if not deps["present"]:
        warnings.append("No dependency or lock file detected")
    internal_modules = [item for item in scripts if item["interface"] == INTERNAL_SCRIPT_INTERFACE]
    missing_help = [
        item["path"] for item in scripts if item["interface"] != INTERNAL_SCRIPT_INTERFACE and not item["has_argparse"]
    ]
    if missing_help:
        warnings.append(f"CLI scripts without argparse/help surface: {', '.join(missing_help[:8])}")
    interactive = [item["path"] for item in scripts if item["uses_input"]]
    if interactive:
        warnings.append(f"Interactive scripts require reviewer awareness: {', '.join(interactive[:8])}")
    network = [item["path"] for item in scripts if item["uses_network"]]
    file_write = [item["path"] for item in scripts if item["uses_file_write"]]
    if network_policy["missing_scripts"]:
        warnings.append(f"Network-capable scripts require bounded host policy: {', '.join(network_policy['missing_scripts'][:8])}")
    if network_policy["mismatches"]:
        warning_paths = [item["path"] for item in network_policy["mismatches"]]
        warnings.append(f"Network host policy mismatch: {', '.join(warning_paths[:8])}")
    if help_smoke["failed_scripts"]:
        warnings.append(f"CLI help smoke failed: {', '.join(help_smoke['failed_scripts'][:8])}")
    if permission_governance["missing_capabilities"]:
        warnings.append(f"Permission approvals missing: {', '.join(permission_governance['missing_capabilities'][:8])}")
    if permission_governance["invalid_capabilities"]:
        warnings.append(f"Permission approvals invalid: {', '.join(permission_governance['invalid_capabilities'][:8])}")
    if permission_governance["expired_capabilities"]:
        warnings.append(f"Permission approvals expired: {', '.join(permission_governance['expired_capabilities'][:8])}")

    summary = {
        "scanned_files": len(files),
        "script_count": len(scripts),
        "internal_module_count": len(internal_modules),
        "secret_findings": len(secrets),
        "dependency_files": deps["present"],
        "network_script_count": len(network),
        "network_policy_covered_count": len(network_policy["covered_scripts"]),
        "network_policy_missing_count": len(network_policy["missing_scripts"]),
        "file_write_script_count": len(file_write),
        "permission_required_count": permission_governance["required_count"],
        "permission_approved_count": permission_governance["approval_count"],
        "permission_missing_count": permission_governance["missing_count"],
        "permission_invalid_count": permission_governance["invalid_count"],
        "permission_expired_count": permission_governance["expired_count"],
        "help_smoke_checked_count": help_smoke["checked_count"],
        "help_smoke_failed_count": help_smoke["failed_count"],
        "interactive_script_count": len(interactive),
        "package_hash_scope": PACKAGE_HASH_SCOPE,
        "package_hash_file_count": len(files),
        "package_sha256": package_digest(files, skill_dir),
    }
    return {
        "ok": not failures,
        "skill_dir": display_path(skill_dir),
        "summary": summary,
        "failures": failures,
        "warnings": warnings,
        "secrets": secrets,
        "scripts": scripts,
        "dependencies": deps,
        "network_policy": network_policy,
        "help_smoke": help_smoke,
        "permission_governance": permission_governance,
        "trust_metadata": trust,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Security Trust Report",
        "",
        f"- OK: `{payload['ok']}`",
        f"- Scanned files: `{summary['scanned_files']}`",
        f"- Scripts: `{summary['script_count']}`",
        f"- Internal script modules: `{summary.get('internal_module_count', 0)}`",
        f"- Secret findings: `{summary['secret_findings']}`",
        f"- Network-capable scripts: `{summary['network_script_count']}`",
        f"- Network policy covered scripts: `{summary.get('network_policy_covered_count', 0)}`",
        f"- Network policy missing scripts: `{summary.get('network_policy_missing_count', 0)}`",
        f"- File-write scripts: `{summary.get('file_write_script_count', 0)}`",
        f"- Permission approvals: `{summary.get('permission_approved_count', 0)} / {summary.get('permission_required_count', 0)}`",
        f"- Permission approval gaps: `{summary.get('permission_missing_count', 0) + summary.get('permission_invalid_count', 0) + summary.get('permission_expired_count', 0)}`",
        f"- CLI help smoke checked: `{summary.get('help_smoke_checked_count', 0)}`",
        f"- CLI help smoke failures: `{summary.get('help_smoke_failed_count', 0)}`",
        f"- Interactive scripts: `{summary['interactive_script_count']}`",
        f"- Package hash scope: `{summary['package_hash_scope']}`",
        f"- Package hash files: `{summary['package_hash_file_count']}`",
        f"- Package SHA256: `{summary['package_sha256']}`",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {item}" for item in payload["failures"]] or ["- None"])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in payload["warnings"]] or ["- None"])
    lines.extend(["", "## Dependency Evidence", ""])
    lines.append(f"- Files: `{', '.join(payload['dependencies']['present']) or 'none'}`")
    lines.append(f"- Pinned entries: `{len(payload['dependencies']['pinned'])}`")
    lines.append(f"- Unpinned entries: `{len(payload['dependencies']['unpinned'])}`")
    network_policy = payload.get("network_policy", {})
    lines.extend(["", "## Network Policy", ""])
    lines.append(f"- Policy file: `{network_policy.get('path', NETWORK_POLICY_REL_PATH)}`")
    lines.append(f"- Present: `{network_policy.get('present', False)}`")
    lines.append(f"- Covered scripts: `{len(network_policy.get('covered_scripts', []))}`")
    lines.append(f"- Missing scripts: `{', '.join(network_policy.get('missing_scripts', [])) or 'none'}`")
    lines.append(f"- Mismatches: `{len(network_policy.get('mismatches', []))}`")
    permission_governance = payload.get("permission_governance", {})
    lines.extend(["", "## Permission Governance", ""])
    lines.append(f"- Policy file: `{permission_governance.get('path', PERMISSION_POLICY_REL_PATH)}`")
    lines.append(f"- Present: `{permission_governance.get('present', False)}`")
    lines.append(f"- Required capabilities: `{', '.join(permission_governance.get('required_capabilities', [])) or 'none'}`")
    lines.append(f"- Approved capabilities: `{', '.join(permission_governance.get('approved_capabilities', [])) or 'none'}`")
    lines.append(f"- Missing approvals: `{', '.join(permission_governance.get('missing_capabilities', [])) or 'none'}`")
    lines.append(f"- Invalid approvals: `{', '.join(permission_governance.get('invalid_capabilities', [])) or 'none'}`")
    lines.append(f"- Expired approvals: `{', '.join(permission_governance.get('expired_capabilities', [])) or 'none'}`")
    help_smoke = payload.get("help_smoke", {})
    lines.extend(["", "## CLI Help Smoke", ""])
    lines.append(f"- Enabled: `{help_smoke.get('enabled', False)}`")
    lines.append(f"- Timeout seconds: `{help_smoke.get('timeout_seconds', HELP_SMOKE_TIMEOUT_SECONDS)}`")
    lines.append(f"- Checked scripts: `{help_smoke.get('checked_count', 0)}`")
    lines.append(f"- Passed scripts: `{help_smoke.get('passed_count', 0)}`")
    lines.append(f"- Failed scripts: `{', '.join(help_smoke.get('failed_scripts', [])) or 'none'}`")
    lines.extend(
        [
            "",
            "## Script Surface",
            "",
            "| Script | Interface | Declared | Argparse | Main Guard | Input | Network | File Write | Subprocess | Reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in payload["scripts"]:
        lines.append(
            f"| {item['path']} | {item['interface']} | {item['interface_declared']} | {item['has_argparse']} | {item['has_main_guard']} | {item['uses_input']} | {item['uses_network']} | {item.get('uses_file_write', False)} | {item['uses_subprocess']} | {item['interface_reason']} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Skill OS trust and security checks.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--skip-help-smoke", action="store_true")
    parser.add_argument("--help-smoke-timeout", type=float, default=HELP_SMOKE_TIMEOUT_SECONDS)
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_json = Path(args.output_json).resolve() if args.output_json else skill_dir / "reports" / "security_trust_report.json"
    output_md = Path(args.output_md).resolve() if args.output_md else skill_dir / "reports" / "security_trust_report.md"
    payload = build_trust_report(
        skill_dir,
        run_help_smoke=not args.skip_help_smoke,
        help_smoke_timeout=args.help_smoke_timeout,
    )
    payload["artifacts"] = {"json": display_path(output_json), "markdown": display_path(output_md)}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
