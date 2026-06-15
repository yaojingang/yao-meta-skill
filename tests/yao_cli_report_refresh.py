from pathlib import Path
from typing import Callable


def refresh_root_report_consistency_inputs(run: Callable[..., dict], root: Path) -> None:
    """Refresh root reports that evidence-consistency compares by value."""

    for refresh_args in [
        ("benchmark-reproducibility", str(root), "--generated-at", "2026-06-15"),
        ("skill-report", str(root)),
        ("skill-interpretation", str(root)),
        ("world-class-preflight", str(root), "--generated-at", "2026-06-15"),
        ("review-studio", str(root)),
    ]:
        refresh_result = run(*refresh_args)
        assert refresh_result["ok"], refresh_result
