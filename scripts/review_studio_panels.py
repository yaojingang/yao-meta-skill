import html
from typing import Any

from review_studio_gates import status_label


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep small Review Studio panel renderers out of the main page composer."


def render_gate_list(gates: list[dict[str, str]]) -> str:
    items = []
    for item in gates:
        link_html = f"<a href='{html.escape(item['link'])}'>证据</a>" if item.get("link") else ""
        items.append(
            "<article class='gate "
            + html.escape(item["status"])
            + "'>"
            f"<div><span>{html.escape(status_label(item['status']))}</span><h3>{html.escape(item['label'])}</h3></div>"
            f"<p>{html.escape(item['detail'])}</p>"
            f"<footer>{html.escape(item['evidence'])} {link_html}</footer>"
            "</article>"
        )
    return "".join(items)


def render_insights(cards: list[dict[str, str]]) -> str:
    return "".join(
        (
            "<article class='metric'>"
            f"<span>{html.escape(item['label'])}</span>"
            f"<strong>{html.escape(item['value'])}</strong>"
            f"<p>{html.escape(item['detail'])}</p>"
            "</article>"
        )
        for item in cards
    )


def render_issue_list(title: str, items: list[dict[str, str]]) -> str:
    if not items:
        return f"<section><h2>{html.escape(title)}</h2><p class='muted'>无。</p></section>"
    body = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['label'])}</strong>"
            f"<span>{html.escape(item['detail'])}</span>"
            "</li>"
        )
        for item in items
    )
    return f"<section><h2>{html.escape(title)}</h2><ul class='issues'>{body}</ul></section>"


def render_review_annotations_panel(annotations_report: dict[str, Any]) -> str:
    annotations = annotations_report.get("annotations", []) if isinstance(annotations_report, dict) else []
    if not annotations:
        return "<p class='muted'>当前没有 reviewer 批注。</p>"
    cards = []
    for item in annotations:
        line_suffix = f":{item['line']}" if item.get("line") else ""
        target_label = f"{item.get('target_path', '')}{line_suffix}"
        meta = " · ".join(
            part
            for part in [
                str(item.get("gate_key", "")),
                str(item.get("reviewer", "")),
                str(item.get("created_at", "")),
            ]
            if part
        )
        cards.append(
            "<article class='annotation-card "
            + html.escape(str(item.get("severity", "note")))
            + " "
            + html.escape(str(item.get("status", "open")))
            + "'>"
            f"<div><span>{html.escape(str(item.get('severity', 'note')))} · {html.escape(str(item.get('status', 'open')))}</span>"
            f"<h3>{html.escape(str(item.get('id', 'annotation')))}</h3></div>"
            f"<p>{html.escape(str(item.get('body', '')))}</p>"
            f"<dl><dt>位置</dt><dd><code>{html.escape(target_label)}</code></dd>"
            f"<dt>Gate</dt><dd>{html.escape(str(item.get('gate_key', '')))}</dd>"
            f"<dt>建议</dt><dd>{html.escape(str(item.get('suggested_action', '') or '无'))}</dd></dl>"
            f"<small>{html.escape(meta)}</small>"
            f"<footer>{html.escape(str(item.get('source_excerpt', '')))}</footer>"
            "</article>"
        )
    return "".join(cards)
