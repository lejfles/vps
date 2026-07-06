#!/usr/bin/env python3
"""
zimeiti 编辑器 v3 · 把队列中的任务实际写入 HTML

任务类型：
1. new_topic：创建新话题大全 HTML（基于 transcript + 标题生成内容草稿）
2. update_topic：把新观点/数据点追加到现有话题 HTML 的对应段落

用法：
    python3 edit_apply.py                    # 处理一个 pending 任务（自动选优先级最高的）
    python3 edit_apply.py --task-id <id>     # 指定任务
    python3 edit_apply.py --list             # 列出队列
    python3 edit_apply.py --preview <id>     # 预览待写入内容，不写 HTML
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path.home() / "zimeiti"
QUEUE_FILE = BASE / "scripts" / "queue.json"
LOG_FILE = BASE / "scripts" / "edit.log"
TOPICS_HTML = BASE / "topics_html"

VANCOUVER_TZ = timezone(timedelta(hours=-7))

# 与 queue_engine.py 保持一致
TOPIC_RULES = [
    {"id": "ai-search-geo-citation", "html": "01-ai-search-geo-citation.html",
     "title": "AI 搜索 / GEO / AI Citation", "subtitle": "AI 搜索时代的引用与可见性"},
    {"id": "claude-ai-models", "html": "02-claude-ai-models.html",
     "title": "Claude / AI 模型与产品", "subtitle": "AI 模型演进、能力边界与商业化"},
    {"id": "conversion-funnel", "html": "03-conversion-funnel.html",
     "title": "Conversion Funnel / 转化漏斗", "subtitle": "从流量到收入的最后一公里"},
    {"id": "big-tech-business", "html": "04-big-tech-business.html",
     "title": "大公司新闻与科技商业", "subtitle": "Big Tech 战略、资本动作与地缘政治"},
    {"id": "content-creation-video", "html": "05-content-creation-video.html",
     "title": "内容创作与视频策略", "subtitle": "短视频时代的创作者方法论"},
    {"id": "website-local-seo", "html": "06-website-local-seo.html",
     "title": "网站与本地 SEO", "subtitle": "网站健康度、本地搜索与个人 AI 隐私"},
    {"id": "marketing-trust-other", "html": "07-marketing-trust-other.html",
     "title": "营销信任与其他战略", "subtitle": "数字营销、信任构建与新兴趋势"},
]

# 下一个新话题编号：08, 09, ...
def next_topic_number():
    existing = sorted(TOPICS_HTML.glob("*.html"))
    nums = []
    for f in existing:
        m = re.match(r"(\d+)-", f.name)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1 if nums else 8


# HTML 模板（简化版：用于新建话题骨架）
NEW_TOPIC_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 话题大全</title>
<style>
:root {{ --bg:#0f1115; --panel:#161a22; --ink:#e7ecf3; --muted:#9aa4b2; --accent:#5b8def; --accent2:#10b981; --line:#222a36; }}
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--ink);line-height:1.8;font-size:16px}}
header{{padding:56px 24px 28px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,#10141c,#0f1115)}}
header h1{{margin:0 0 10px;font-size:34px;line-height:1.3}}
header .subtitle{{color:var(--muted);font-size:16px;margin-bottom:8px}}
header .meta{{color:var(--muted);font-size:13px}}
main{{max-width:900px;margin:0 auto;padding:32px 24px 60px}}
article section, article .lead{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:24px 28px;margin-bottom:20px}}
article h2{{margin-top:32px;margin-bottom:16px;font-size:24px;border-left:3px solid var(--accent);padding-left:12px}}
article h3{{font-size:19px;color:var(--accent);margin-top:24px;margin-bottom:10px}}
article p{{margin:0 0 14px 0;color:#dde3ec}}
article ul, article ol{{padding-left:24px}}
article li{{margin-bottom:8px}}
article blockquote{{border-left:3px solid var(--accent);background:#0c1018;margin:16px 0;padding:14px 20px;color:var(--muted);border-radius:0 6px 6px 0}}
article strong{{color:var(--ink);font-weight:600}}
article code{{background:#0a0d12;color:#cfd6e4;padding:2px 8px;border-radius:4px;font-size:14px}}
section.lead p{{font-size:17px;line-height:1.9}}
.update-log{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:20px 24px}}
.update-log h2{{margin-top:0;font-size:20px;border-left:3px solid var(--accent);padding-left:10px}}
.update-log ul{{padding-left:20px}}
.update-log li{{margin-bottom:6px;color:var(--muted);font-size:14px}}
.update-log li strong{{color:var(--ink)}}
.footer{{color:var(--muted);font-size:13px;text-align:center;padding:32px 16px;border-top:1px solid var(--line);margin-top:40px}}
.new-point{{background:#1a1f2b;border-left:3px solid var(--accent2);padding:10px 14px;border-radius:0 4px 4px 0;margin:8px 0;font-size:14px;color:#cfd6e4}}
</style>
</head>
<body>
<header>
  <h1>{title}</h1>
  <div class="subtitle">{subtitle}</div>
  <div class="meta">持续更新 · 最后更新：{today} · 新建话题（由 queue_engine 自动检测）</div>
</header>
<main>
<article>

<section class="lead">
<p>{intro}</p>
</section>

<section>
<h2>话题定义</h2>
<p>{definition}</p>
</section>

<section>
<h2>初步观察（来自首个触发脚本）</h2>
{initial_observations}
</section>

<section>
<h2>新观点与数据点（持续补充）</h2>
{new_points_section}
</section>

</article>

<div class="update-log">
<h2>更新日志</h2>
<ul>
<li><strong>{today}</strong> · 新建话题 · 首个触发脚本：<code>{trigger_script}</code></li>
</ul>
</div>
</main>
<div class="footer">
  话题大全 · 自媒体自动归类引擎 · v3 · 由 queue_engine 自动检测到的新话题<br>
  <a href="../index.html" style="color:var(--accent)">返回索引</a>
</div>
</body>
</html>"""


def load_queue():
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"pending": [], "in_progress": None, "completed_today": 0, "last_processed": None}


def save_queue(q):
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def log(msg):
    line = f"[{datetime.now(VANCOUVER_TZ).isoformat(timespec='seconds')}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def gen_topic_id_from_topic_part(topic_part):
    """从文件名 topic_part 生成候选话题 ID"""
    slug = re.sub(r'[^a-z0-9-]', '-', topic_part.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    # 截短到合理长度
    words = slug.split('-')[:5]
    return '-'.join(words)[:60]


def gen_title_from_topic_part(topic_part, title_cn):
    """从 topic_part + 中文标题生成话题标题"""
    if title_cn and title_cn != "(无标题)":
        # 取标题核心
        return title_cn[:30]
    # 从 topic_part 转中文风格
    return topic_part.replace("-", " ").title()[:30]


def build_new_topic_html(task):
    """为新话题构建 HTML 骨架"""
    today = datetime.now(VANCOUVER_TZ).strftime("%Y-%m-%d")
    n = next_topic_number()
    topic_id = gen_topic_id_from_topic_part(task["topic_part"])
    title = gen_title_from_topic_part(task["topic_part"], task.get("title_cn", ""))
    subtitle = f"由 queue_engine 在 {today} 自动检测到的新话题"

    # 用 transcript preview 生成初步观察
    preview = task.get("transcript_preview", "")
    initial_obs = ""
    if preview:
        # 提取 2-3 句作为初步观察
        sentences = re.split(r'(?<=[.!?])\s+', preview)
        bullets = ""
        for s in sentences[:5]:
            s = s.strip()
            if len(s) > 30 and len(s) < 300:
                bullets += f"<li>{s}</li>\n"
        initial_obs = f"<ul>\n{bullets}</ul>\n<p><em>以上为首次触发脚本的核心观点摘要，将随新数据持续补充。</em></p>"

    # 新观点段
    new_points_html = ""
    if task.get("new_points"):
        for p in task["new_points"]:
            new_points_html += f'<div class="new-point">📌 {p}</div>\n'
    else:
        new_points_html = "<p style='color:var(--muted)'>暂无新增观点，等待下一轮扫描补充。</p>"

    intro = f"本话题由 {today} 的扫描自动识别。当某条视频脚本的内容无法匹配任何现有话题时，queue_engine 会将其标记为新话题候选，并在编辑时段（温哥华时间 20:00–09:00）创建本页面。"

    definition = f"基于首个触发脚本的内容，本话题涉及以下核心议题：{task.get('topic_part', '').replace('-', ' ')}。详细定义将在积累更多脚本后逐步完善。"

    html = NEW_TOPIC_TEMPLATE.format(
        title=title,
        subtitle=subtitle,
        today=today,
        intro=intro,
        definition=definition,
        initial_observations=initial_obs,
        new_points_section=new_points_html,
        trigger_script=task["script_name"],
    )

    fname = f"{n:02d}-{topic_id}.html"
    return fname, html


def append_update_to_existing_topic(task):
    """把新观点追加到现有话题 HTML"""
    rule = next(r for r in TOPIC_RULES if r["id"] == task["topic_id"])
    html_path = TOPICS_HTML / rule["html"]

    if not html_path.exists():
        return False, f"HTML 不存在: {html_path}"

    html = html_path.read_text(encoding="utf-8")
    today = datetime.now(VANCOUVER_TZ).strftime("%Y-%m-%d %H:%M PT")

    # 检查 marker（用 data-updated 属性）
    data_marker = f'data-updated="{task["script_name"]}"'
    if data_marker in html:
        return False, "已处理过此脚本"

    # 在"新观点补充"section 或文章主体末尾插入新观点块
    new_points_html = ""
    for p in task.get("new_points", []):
        new_points_html += f'<div class="new-point">📌 {p}</div>\n'

    if not new_points_html:
        return False, "无新观点可写"

    # marker 放在第一个 new-point div 内部作 data 属性，便于编辑幂等检查
    first_point_with_marker = new_points_html.replace(
        '<div class="new-point">',
        f'<div class="new-point" data-updated="{task["script_name"]}">',
        1,
    )

    # 尝试找到文章主体末尾（</article> 之前），插入"新观点补充"段
    # 如果文章已有这个段，追加到末尾；否则新建
    section_marker = "<h2>新观点补充（持续更新）</h2>"
    if section_marker in html:
        # 已存在该 section，追加到其末尾（</section> 前）
        pattern = re.compile(
            rf'({re.escape(section_marker)}.*?)(</section>)',
            re.DOTALL,
        )
        html, n = pattern.subn(
            lambda m: m.group(1) + "\n" + first_point_with_marker + m.group(2),
            html, count=1,
        )
        if n == 0:
            return False, "新观点补充 section 存在但无法定位"
    else:
        # 新建该 section，放在最后一段 </section> 之后、</article> 之前
        new_section = f'\n<section>\n{section_marker}\n{new_points_html}\n</section>\n'
        html = html.replace("</article>", new_section + "</article>", 1)

    # 更新日志追加
    log_entry = f'<li><strong>{today}</strong> · 新增 {len(task["new_points"])} 条观点：<code>{task["script_name"]}</code></li>\n'
    pattern_log = re.compile(r'(<div class="update-log">.*?</h2>\s*<ul>)(.*?)(</ul>)', re.DOTALL)
    html, n = pattern_log.subn(
        lambda m: m.group(1) + m.group(2) + "\n" + log_entry + m.group(3),
        html, count=1,
    )
    if n == 0:
        return False, "找不到更新日志 section"

    html_path.write_text(html, encoding="utf-8")
    return True, f"已追加 {len(task['new_points'])} 条新观点到 {rule['title']}"


def cmd_list(args):
    queue = load_queue()
    print(f"队列状态：")
    print(f"  pending: {len(queue['pending'])}")
    print(f"  in_progress: {queue.get('in_progress', 'None')}")
    print(f"  completed_today: {queue.get('completed_today', 0)}")
    print(f"  last_processed: {queue.get('last_processed', 'Never')}")
    print()
    for i, t in enumerate(queue["pending"], 1):
        print(f"[{i}] {t['task_id']}")
        print(f"    type: {t['type']}")
        print(f"    topic: {t.get('topic_id') or 'NEW'}")
        print(f"    reason: {t['reason']}")
        print(f"    points: {len(t.get('new_points', []))}")
        print()


def cmd_preview(args):
    queue = load_queue()
    task = next((t for t in queue["pending"] if t["task_id"] == args.preview), None)
    if not task:
        print(f"Task not found: {args.preview}")
        return
    print(json.dumps(task, ensure_ascii=False, indent=2))


def cmd_apply(args):
    queue = load_queue()
    if not queue["pending"]:
        log("APPLY  NO-TASK")
        return

    # 选任务
    if args.task_id:
        task = next((t for t in queue["pending"] if t["task_id"] == args.task_id), None)
        if not task:
            log(f"APPLY  ERR  task not found: {args.task_id}")
            return
    else:
        # 优先级 high 优先（新话题），再按时间
        pending = sorted(queue["pending"], key=lambda x: (x.get("priority") != "high", x["created_at"]))
        task = pending[0]

    queue["in_progress"] = task["task_id"]
    save_queue(queue)
    log(f"APPLY  START  {task['task_id']}  type={task['type']}")

    if task["type"] == "new_topic":
        fname, html = build_new_topic_html(task)
        out_path = TOPICS_HTML / fname
        out_path.write_text(html, encoding="utf-8")
        log(f"APPLY  NEW-TOPIC  created: {fname}")
        result = "created"
    elif task["type"] == "update_topic":
        ok, msg = append_update_to_existing_topic(task)
        log(f"APPLY  UPDATE  {task['topic_id']}: {msg}")
        result = "updated" if ok else "skipped"
    else:
        log(f"APPLY  ERR  unknown type: {task['type']}")
        result = "error"

    # 移出 pending
    queue["pending"] = [t for t in queue["pending"] if t["task_id"] != task["task_id"]]
    queue["in_progress"] = None
    queue["completed_today"] = queue.get("completed_today", 0) + 1
    queue["last_processed"] = datetime.now(VANCOUVER_TZ).isoformat()
    save_queue(queue)

    log(f"APPLY  DONE  result={result}")
    print(json.dumps({"result": result, "task_id": task["task_id"]}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="列出队列")
    p_list.set_defaults(func=cmd_list)

    p_prev = sub.add_parser("preview", help="预览任务详情")
    p_prev.add_argument("preview", help="task_id")
    p_prev.set_defaults(func=cmd_preview)

    p_apply = sub.add_parser("apply", help="处理一个任务（实际写入 HTML）")
    p_apply.add_argument("--task-id", help="指定任务")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()