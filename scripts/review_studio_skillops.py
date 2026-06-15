from typing import Any

from review_studio_formatting import render_kv_grid


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep SkillOps summary panels out of the main HTML renderer."


def render_skillops_section(data: dict[str, Any]) -> str:
    daily_summary = data["daily_skillops"].get("summary", {})
    weekly_summary = data["weekly_curator"].get("summary", {})
    daily_panel = render_kv_grid(
        daily_summary,
        [
            "decision",
            "proposal_count",
            "approval_count",
            "pending_review_count",
            "release_lock_ready",
            "public_world_class_ready",
            "writes_source_files",
            "auto_patch_enabled",
        ],
        "no daily SkillOps summary",
    )
    weekly_panel = render_kv_grid(
        weekly_summary,
        [
            "decision",
            "week_id",
            "daily_report_count",
            "unique_opportunity_count",
            "ready_for_approval_review_count",
            "proposal_review_count",
            "top_score",
            "release_lock_ready",
            "writes_source_files",
            "auto_patch_enabled",
        ],
        "no weekly curator summary",
    )
    return f"""
    <section class="twocol">
      <div class="panel"><h2>日常运维</h2>{daily_panel}</div>
      <div class="panel"><h2>周度队列</h2>{weekly_panel}</div>
    </section>
"""
