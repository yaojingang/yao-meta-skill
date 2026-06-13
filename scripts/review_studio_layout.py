#!/usr/bin/env python3
"""Static layout contract for Review Studio HTML."""

import html


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep Review Studio layout and CSS out of gate logic."


REVIEW_STUDIO_NAV = [
    ("#overview", "审查总览"),
    ("#intent", "意图画布"),
    ("#trigger", "触发实验"),
    ("#output", "输出实验"),
    ("#actions", "修复动作"),
    ("#annotations", "审查批注"),
    ("#runtime", "运行矩阵"),
    ("#trust", "信任报告"),
    ("#permissions", "权限批准"),
    ("#permission-probes", "权限探针"),
    ("#atlas", "组合治理"),
    ("#telemetry", "运营回路"),
    ("#waivers", "人工批准"),
    ("#world-class", "世界证据"),
    ("#registry", "注册审计"),
    ("#release", "发布路线"),
]


def render_review_nav(nav_items: list[tuple[str, str]] | None = None) -> str:
    items = REVIEW_STUDIO_NAV if nav_items is None else nav_items
    return "".join(
        f"<a href='{html.escape(href)}'>{html.escape(label)}</a>"
        for href, label in items
    )


def review_studio_css() -> str:
    return """
    :root {
      --ink: #1B365D;
      --text: #24201d;
      --muted: #746d66;
      --line: #e7ded2;
      --soft: #faf8f5;
      --pass: #1e6b52;
      --warn: #9a6718;
      --block: #9b2c2c;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      background: #ffffff;
      color: var(--text);
      font-family: Georgia, "Times New Roman", "Songti SC", serif;
      line-height: 1.58;
    }
    nav {
      position: sticky;
      top: 0;
      z-index: 10;
      display: flex;
      gap: 4px;
      justify-content: center;
      flex-wrap: wrap;
      padding: 10px 16px;
      background: rgba(255,255,255,0.94);
      border-bottom: 1px solid var(--line);
      backdrop-filter: blur(10px);
    }
    nav a {
      color: var(--ink);
      text-decoration: none;
      font-size: 14px;
      padding: 7px 10px;
      border-radius: 6px;
    }
    nav a:hover { background: var(--soft); }
    main { max-width: 1180px; margin: 0 auto; padding: 44px 28px 76px; }
    header { border-bottom: 1px solid var(--line); padding-bottom: 28px; margin-bottom: 28px; }
    .eyebrow { color: var(--ink); font-size: 14px; letter-spacing: .08em; text-transform: uppercase; }
    h1, h2, h3 { color: var(--text); font-weight: 500; margin: 0; letter-spacing: 0; }
    h1 { font-size: clamp(34px, 5vw, 64px); line-height: 1.03; max-width: 920px; margin-top: 12px; }
    h2 { font-size: 30px; margin-bottom: 14px; }
    h3 { font-size: 19px; }
    p { margin: 0; }
    .lede { max-width: 820px; color: var(--muted); font-size: 20px; margin-top: 18px; }
    .decision {
      display: inline-flex;
      align-items: baseline;
      gap: 12px;
      margin-top: 24px;
      padding: 12px 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      background: var(--soft);
    }
    .decision strong { font-size: 28px; }
    section { padding: 30px 0; border-bottom: 1px solid var(--line); scroll-margin-top: 76px; }
    .metrics, .gates {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
    }
    .gates { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .metric, .gate {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      background: #fff;
      min-width: 0;
    }
    .metric span, .gate span { display: block; color: var(--muted); font-size: 13px; }
    .metric strong { display: block; color: var(--ink); font-size: 34px; line-height: 1.1; margin: 8px 0; }
    .metric p, .gate p, .gate footer, .issues span, .evidence span { color: var(--muted); font-size: 14px; overflow-wrap: anywhere; }
    .gate { display: flex; flex-direction: column; gap: 10px; }
    .gate.pass { border-top: 4px solid var(--pass); }
    .gate.warn { border-top: 4px solid var(--warn); }
    .gate.block { border-top: 4px solid var(--block); }
    .gate footer { border-top: 1px solid var(--line); padding-top: 10px; }
    a { color: var(--ink); }
    .twocol {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 22px;
      align-items: start;
    }
    .panel {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: #fff;
    }
    .panel p { color: var(--muted); }
    .kv-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 12px;
      margin: 2px 0 0;
    }
    .kv-grid div {
      min-width: 0;
      padding: 9px 0 0;
      border-top: 1px solid var(--line);
    }
    .kv-grid dt {
      color: var(--muted);
      font-size: 13px;
    }
    .kv-grid dd {
      margin: 2px 0 0;
      color: var(--ink);
      font-size: 15px;
      overflow-wrap: anywhere;
    }
    .issues, .evidence {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 12px;
    }
    .issues li, .evidence li {
      border-left: 3px solid var(--line);
      padding-left: 12px;
      display: grid;
      gap: 3px;
    }
    .muted { color: var(--muted); }
    .actions-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .annotations-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }
    .action-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: #fff;
      display: grid;
      gap: 10px;
      min-width: 0;
    }
    .action-card.warn { border-left: 4px solid var(--warn); }
    .action-card.block { border-left: 4px solid var(--block); }
    .annotation-card {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: #fff;
      display: grid;
      gap: 10px;
      min-width: 0;
    }
    .annotation-card.warning { border-left: 4px solid var(--warn); }
    .annotation-card.blocker { border-left: 4px solid var(--block); }
    .annotation-card.resolved { opacity: .72; }
    .action-card span,
    .annotation-card span,
    .action-card small,
    .annotation-card small,
    .action-card footer,
    .annotation-card footer,
    .action-card dd {
      color: var(--muted);
      font-size: 14px;
      overflow-wrap: anywhere;
    }
    .annotation-card dd { color: var(--muted); font-size: 14px; overflow-wrap: anywhere; }
    .action-card dl, .annotation-card dl {
      display: grid;
      grid-template-columns: 80px minmax(0, 1fr);
      gap: 6px 10px;
      margin: 0;
    }
    .action-card dt, .annotation-card dt { color: var(--ink); font-size: 14px; }
    .action-card dd, .annotation-card dd { margin: 0; }
    .source-ref-list {
      list-style: none;
      padding: 0;
      margin: 0;
      display: grid;
      gap: 6px;
    }
    .source-ref-list li {
      display: grid;
      gap: 2px;
      min-width: 0;
      padding: 8px 0 0;
      border-top: 1px solid var(--line);
    }
    .source-ref-list a,
    .source-ref-list span {
      overflow-wrap: anywhere;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }
    .source-ref-list small {
      font-size: 12px;
      color: var(--muted);
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 13px;
    }
    @media (max-width: 980px) {
      .metrics, .gates, .twocol, .actions-grid, .annotations-grid, .kv-grid { grid-template-columns: 1fr; }
      main { padding: 32px 18px 60px; }
      nav { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; }
      nav a { flex: 0 0 auto; }
    }
    """.strip()
