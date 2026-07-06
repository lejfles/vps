#!/usr/bin/env python3
"""
给 v3 话题文章补上 update_topic 流程需要的两个 anchor：
1. <section><h2>新观点补充（持续更新）</h2></section> （在 </article> 前）
2. <div class="update-log"><h2>更新日志</h2><ul></ul></div> （在 </main> 内，</article> 后）
"""

import re
from pathlib import Path

TOPICS_HTML = Path("/home/ubuntu/zimeiti/topics_html")

files = [
    "01-ai-search-geo-citation.html",
    "02-claude-ai-models.html",
    "03-conversion-funnel.html",
    "04-big-tech-business.html",
    "05-content-creation-video.html",
    "06-website-local-seo.html",
    "07-marketing-trust-other.html",
]

# CSS 追加：update-log 和 new-point
EXTRA_CSS = """
.update-log{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px 24px;margin-bottom:20px;margin-top:24px}
.update-log h2{margin-top:0;font-size:20px;border-left:3px solid var(--accent);padding-left:10px}
.update-log ul{padding-left:20px}
.update-log li{margin-bottom:6px;color:var(--muted);font-size:14px}
.update-log li strong{color:var(--ink)}
.new-point{background:#1a1f2b;border-left:3px solid #10b981;padding:10px 14px;border-radius:0 4px 4px 0;margin:8px 0;font-size:14px;color:#cfd6e4;line-height:1.7}
"""

for fname in files:
    path = TOPICS_HTML / fname
    html = path.read_text(encoding="utf-8")

    # 1. 在 </style> 前追加 CSS
    if ".new-point{" not in html:
        html = html.replace("</style>", EXTRA_CSS + "\n</style>", 1)

    # 2. 在 </article> 前插入"新观点补充"section
    section_marker = '<h2>新观点补充（持续更新）</h2>'
    if section_marker not in html:
        new_section = f'\n<section>\n{section_marker}\n<p style="color:var(--muted);font-style:italic">本节由 edit_apply.py 自动维护，每次有新视频脚本带来新观点时补充。</p>\n</section>\n'
        html = html.replace("</article>", new_section + "</article>", 1)

    # 3. 在 </article> 后、</main> 前插入"更新日志"div
    log_marker = '<div class="update-log">'
    if log_marker not in html:
        log_div = '\n<div class="update-log">\n<h2>更新日志</h2>\n<ul>\n<li><strong>2026-07-06</strong> · v3 文章发布（重写为可读深度文章）</li>\n</ul>\n</div>\n'
        html = html.replace("</main>", log_div + "</main>", 1)

    path.write_text(html, encoding="utf-8")
    print(f"✓ {fname}: 已补 anchor")

print(f"\n完成 {len(files)} 个文件")