#!/usr/bin/env python3
import json
import os
import shutil
import stat
import textwrap
from pathlib import Path

from yao_cli_helpers import ROOT, run, run_with_env


def write_skill(path: Path, description: str = "Operator UX test skill.") -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(
        f"---\nname: yao-meta-skill\ndescription: {description}\n---\n\n# Test Skill\n",
        encoding="utf-8",
    )


def write_fake_gh(bin_dir: Path) -> None:
    bin_dir.mkdir(parents=True, exist_ok=True)
    script = bin_dir / "gh"
    script.write_text(
        textwrap.dedent(
            """\
            #!/usr/bin/env python3
            import json
            import os
            import sys

            args = sys.argv[1:]
            if args[:2] == ["pr", "view"]:
                checks = [] if os.environ.get("YAO_FAKE_GH_EMPTY_CHECKS") else [
                    {
                        "__typename": "CheckRun",
                        "name": "test",
                        "status": "COMPLETED",
                        "conclusion": "SUCCESS",
                        "workflowName": "test",
                    }
                ]
                print(json.dumps({
                    "number": 4,
                    "title": "docs: clarify Python 3.11 local development",
                    "state": "OPEN",
                    "isDraft": False,
                    "mergeable": "MERGEABLE",
                    "author": {"login": "contributor"},
                    "baseRefName": "main",
                    "headRefName": "docs-python-311",
                    "url": "https://github.com/example/repo/pull/4",
                    "additions": 23,
                    "deletions": 3,
                    "changedFiles": 2,
                    "commits": [{"oid": "abc123", "messageHeadline": "docs: clarify Python 3.11 local development"}],
                    "statusCheckRollup": checks,
                    "reviewDecision": "",
                    "maintainerCanModify": True,
                }))
                raise SystemExit(0)
            if args[:2] == ["pr", "diff"]:
                print("Makefile")
                print("README.md")
                raise SystemExit(0)
            print("unexpected gh invocation", args, file=sys.stderr)
            raise SystemExit(2)
            """
        ),
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_operator_ux"
    shutil.rmtree(tmp_root, ignore_errors=True)
    tmp_root.mkdir(parents=True, exist_ok=True)

    source = tmp_root / "source" / "yao-meta-skill"
    codex_root = tmp_root / "codex-skills"
    agents_root = tmp_root / "agents-skills"
    disabled_root = tmp_root / "disabled-skills"
    codex_root.mkdir()
    agents_root.mkdir()
    disabled_root.mkdir()
    write_skill(source)
    (codex_root / "yao-meta-skill").symlink_to(source, target_is_directory=True)
    write_skill(disabled_root / "yao-meta-skill", "Disabled mirror.")

    install_status = run(
        "install-status",
        "--expected-source",
        str(source),
        "--codex-root",
        str(codex_root),
        "--agents-root",
        str(agents_root),
        "--disabled-root",
        str(disabled_root),
    )
    assert install_status["ok"], install_status
    assert install_status["payload"]["summary"]["codex_active"] is True, install_status
    assert install_status["payload"]["summary"]["agents_active"] is False, install_status
    assert install_status["payload"]["summary"]["disabled_mirror"] is True, install_status
    assert install_status["payload"]["locations"]["codex"]["is_symlink"] is True, install_status
    assert install_status["payload"]["locations"]["codex"]["points_to_expected_source"] is True, install_status
    assert any("restart" in item.lower() for item in install_status["payload"]["recommendations"]), install_status

    sync_ok = run("localized-doc-sync-check")
    assert sync_ok["ok"], sync_ok
    assert sync_ok["payload"]["summary"]["missing_count"] == 0, sync_ok
    assert any(item["key"] == "operator-ux" for item in sync_ok["payload"]["pairs"]), sync_ok

    source_readme = tmp_root / "README.md"
    localized_readme = tmp_root / "README.zh-CN.md"
    source_readme.write_text("## Skill OS 2.0 Upgrade\n## 2.0 Use Cases\n", encoding="utf-8")
    localized_readme.write_text("## Skill OS 2.0 升级\n", encoding="utf-8")
    sync_fail = run(
        "localized-doc-sync-check",
        "--source",
        str(source_readme),
        "--localized",
        str(localized_readme),
        "--pair",
        "upgrade::## Skill OS 2.0 Upgrade::## Skill OS 2.0 升级",
        "--pair",
        "use-cases::## 2.0 Use Cases::## 2.0 使用场景",
        "--output-json",
        str(tmp_root / "sync.json"),
        "--output-md",
        str(tmp_root / "sync.md"),
    )
    assert not sync_fail["ok"], sync_fail
    assert sync_fail["returncode"] == 2, sync_fail
    assert sync_fail["payload"]["summary"]["missing_count"] == 1, sync_fail
    assert (tmp_root / "sync.json").exists(), sync_fail
    assert "use-cases" in (tmp_root / "sync.md").read_text(encoding="utf-8"), sync_fail

    sync_missing_file = run(
        "localized-doc-sync-check",
        "--source",
        str(tmp_root / "missing-README.md"),
        "--localized",
        str(localized_readme),
    )
    assert not sync_missing_file["ok"], sync_missing_file
    assert sync_missing_file["payload"]["failures"], sync_missing_file
    assert "Missing docs file" in sync_missing_file["payload"]["failures"][0], sync_missing_file

    fake_bin = tmp_root / "bin"
    write_fake_gh(fake_bin)
    fake_env = {"PATH": f"{fake_bin}{os.pathsep}{os.environ.get('PATH', '')}"}
    pr_report = run_with_env(
        fake_env,
        "pr-review-report",
        "4",
        "--repo",
        "example/repo",
        "--output-json",
        str(tmp_root / "pr.json"),
        "--output-md",
        str(tmp_root / "pr.md"),
    )
    assert pr_report["ok"], pr_report
    assert pr_report["payload"]["decision"] == "mergeable-after-review", pr_report
    assert pr_report["payload"]["review_depth"] == "quick", pr_report
    assert pr_report["payload"]["checks"]["passed_count"] == 1, pr_report
    assert pr_report["payload"]["files"] == ["Makefile", "README.md"], pr_report
    assert (tmp_root / "pr.json").exists(), pr_report
    assert "Suggested Commands" in (tmp_root / "pr.md").read_text(encoding="utf-8"), pr_report

    empty_check_env = dict(fake_env)
    empty_check_env["YAO_FAKE_GH_EMPTY_CHECKS"] = "1"
    pr_without_checks = run_with_env(
        empty_check_env,
        "pr-review-report",
        "4",
        "--repo",
        "example/repo",
    )
    assert pr_without_checks["ok"], pr_without_checks
    assert pr_without_checks["payload"]["decision"] == "local-verification-required", pr_without_checks
    pr_require_checks = run_with_env(
        empty_check_env,
        "pr-review-report",
        "4",
        "--repo",
        "example/repo",
        "--require-checks",
    )
    assert not pr_require_checks["ok"], pr_require_checks
    assert pr_require_checks["payload"]["decision"] == "checks-required", pr_require_checks

    print("operator ux checks passed")


if __name__ == "__main__":
    main()
