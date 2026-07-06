#!/usr/bin/env python3
"""
zimeiti 自动归类引擎 v3 · 分层时序版

工作流：
1. 04:00 / 16:00 PT（数据采集） → 扫 outputs → 判定新话题 / 旧话题新观点
   → 把"待编辑任务"写入队列 queue.json，**不修改任何 HTML**
2. 20:00–09:00 PT（编辑时段） → 每 30 分钟处理一个任务 → 实际写入 HTML

队列结构（queue.json）：
{
  "pending": [
    {
      "task_id": "2026-07-06T16:00:01_xxx",
      "created_at": "2026-07-06T16:00:01-07:00",
      "type": "new_topic" | "update_topic",
      "topic_id": "...",
      "script_name": "2026-07-06_xxx_yyy.txt",
      "reason": "首次出现新话题 X / 旧话题 X 有新数据点",
      "new_points": ["...新观点...", "...新数据..."]
    }
  ],
  "in_progress": null,
  "completed_today": 0,
  "last_processed": null
}

用法：
    python3 scan.py              # 04/16 点跑，扫 + 判定 + 入队
    python3 scan.py --dry-run    # 预览，不写队列
    python3 edit_one.py          # 20-09 点跑一次，处理一个任务
    python3 edit_one.py --task-id <id>   # 指定处理哪个任务
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path.home() / "zimeiti"
QUEUE_FILE = BASE / "scripts" / "queue.json"
LOG_FILE = BASE / "scripts" / "scan.log"
PROCESSED = BASE / "scripts" / ".processed.json"

SCRIPT_DIR = Path.home() / "zimeiti_tiktok_monitor" / "outputs"
TRANSCRIPT_DIR = Path.home() / "zimeiti_tiktok_monitor" / "work"
TOPICS_HTML = BASE / "topics_html"

# 温哥华时间（PDT = UTC-7，PST = UTC-8，简化为 UTC-7）
VANCOUVER_TZ = timezone(timedelta(hours=-7))

# 7 个现有话题的关键词（同 classify.py）
TOPIC_RULES = [
    {"id": "ai-search-geo-citation", "html": "01-ai-search-geo-citation.html",
     "keywords": ["ai search", "geo", "aeo", "llms.txt", "knowledge graph", "citation", "cited", "freshness", "ai overviews", "ai overview", "zero click", "zero-click", "answer pages", "answer-first", "answer first", "micro moments", "eeat", "fact list", "rank math", "brand mention", "hubspot", "anti spam", "reddit ai", "google becomes", "seo was never", "ai visibility", "google rank", "google spam", "google business profile", "knowledge base", "chatbot", "ai recommendation", "google fact list", "page one", "search intent", "conversational", "two score system"]},
    {"id": "claude-ai-models", "html": "02-claude-ai-models.html",
     "keywords": ["claude", "sonnet", "fable", "chatgpt", "gpt-", "openai", "frontier ai model", "model cost", "model comparison", "token subsidy", "claude skill", "prompt injection", "ai writing", "ai tells", "structure detection", "second brain", "cowork", "code modes", "sandcastles", "channel audit", "agents", "7 types", "glm", "mythos", "ai subscription"]},
    {"id": "conversion-funnel", "html": "03-conversion-funnel.html",
     "keywords": ["funnel", "checkout", "friction", "lead form", "form pruning", "landing page", "cro", "conversion", "ltv", "tiktok shop", "creator business", "international payments", "onboarding", "core value", "hot leads", "conversation ai", "highlevel", "300 million button", "price clock", "inherited steps", "welcome message", "stock photos", "tesla"]},
    {"id": "big-tech-business", "html": "04-big-tech-business.html",
     "keywords": ["a24", "big tech", "meta ai", "spacex", "ipo", "amazon", "trump", "government", "crypto", "stake", "openai stake", "brain2qwerty", "meg", "typing", "export controls", "china", "cyberwar", "mythos", "glm", "crash landing", "artificial movie", "oscar pushback"]},
    {"id": "content-creation-video", "html": "05-content-creation-video.html",
     "keywords": ["bullseye", "positioning", "lego method", "video hook", "skip rate", "shock score", "storytelling", "story funnel", "blockers", "failure modes", "script rhythm", "zigzag test", "six levels", "story ladder", "declarative hooks", "embedded truths", "video failure", "education", "long term marketing", "gen z", "brand touches"]},
    {"id": "website-local-seo", "html": "06-website-local-seo.html",
     "keywords": ["google business profile", "local seo", "website annoyances", "ban list", "stock photos", "five seo sins", "diy diagnostics", "bot traffic", "ai agent visibility", "ai infrastructure", "inflation", "personal finance", "offline ai", "privacy", "side hustle", "quality gap", "quality risk", "website rebuild", "web mcp", "side hustle quality", "google business", "ai chatbot"]},
    {"id": "marketing-trust-other", "html": "07-marketing-trust-other.html",
     "keywords": ["distribution", "owned channels", "relationships", "platform ai rewriting", "digital marketing three step", "gamma voice dictation", "deck workflow", "heygen", "avatar", "speech cleanup", "seamless cuts", "marketing visibility", "trust", "three step", "business owner", "visibility trust", "creator economy"]},
]

MANUAL_MAP = {
    "creator-business-international-payments-ai": "conversion-funnel",
    "digital-marketing-three-step-business-owner": "marketing-trust-other",
    "five-seo-sins-diy-website-diagnostics": "website-local-seo",
}


def load_queue():
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"pending": [], "in_progress": None, "completed_today": 0, "last_processed": None}


def save_queue(q):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_processed():
    if PROCESSED.exists():
        try:
            return json.loads(PROCESSED.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_processed(d):
    PROCESSED.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def load_transcripts():
    transcripts = {}
    for f in TRANSCRIPT_DIR.glob("*_transcript*.txt"):
        parts = f.stem.replace("_transcript_clean", "").replace("_transcript", "").rsplit("_", 1)
        if len(parts) == 2:
            vid_id = parts[1]
            if vid_id not in transcripts:
                transcripts[vid_id] = f.read_text(encoding="utf-8")
    return transcripts


def parse_filename(name):
    base = name.replace(".txt", "")
    parts = base.split("_", 2)
    return {
        "date": parts[0] if len(parts) >= 1 else "",
        "author": parts[1] if len(parts) >= 2 else "",
        "topic_part": parts[2] if len(parts) >= 3 else "",
    }


def extract_video_id(text):
    m = re.search(r"(?:视频 ID|video ID|video id)\s*[::]\s*(\d+)", text)
    if m:
        return m.group(1)
    m2 = re.search(r"/video/(\d+)", text)
    if m2:
        return m2.group(1)
    return None


def get_transcript_and_title(path, transcripts):
    text = path.read_text(encoding="utf-8")
    meta = parse_filename(path.name)
    vid_id = extract_video_id(text)
    transcript = transcripts.get(vid_id, "") if vid_id else ""
    if not transcript:
        m = re.search(r"# 英文脚本（Audio transcript）\s*\n+(.*?)(?=\n# |\Z)", text, re.DOTALL)
        if m:
            transcript = m.group(1).strip()
    first = text.split("\n")[0].lstrip("# ").strip()
    title = first if first and first != "基本信息" else "(无标题)"
    return meta, transcript, title, vid_id


def clean_transcript(t):
    t = re.sub(r'language=\S+\s+probability=\S+\s+duration=\S+\s*', '', t)
    t = re.sub(r'\[\d+\.\d+-\d+\.\d+\]\s*', '', t)
    t = re.sub(r'\[\d+\.\d+\s*->\s*\d+\.\d+\]\s*', '', t)
    return t.strip()


def classify_topic(name, transcript, topic_part):
    haystack = (topic_part + " " + transcript[:1500]).lower()
    scored = []
    for rule in TOPIC_RULES:
        hits = sum(1 for kw in rule["keywords"] if kw.lower() in haystack)
        if hits > 0:
            scored.append({"rule": rule, "hits": hits})
    scored.sort(key=lambda x: -x["hits"])

    if scored:
        top_hits = scored[0]["hits"]
        return [s for s in scored if s["hits"] >= max(1, top_hits - 1)]

    for key, tid in MANUAL_MAP.items():
        if key in topic_part.lower():
            rule = next(r for r in TOPIC_RULES if r["id"] == tid)
            return [{"rule": rule, "hits": 0, "manual": True}]
    return []


def extract_new_points(transcript, existing_topic_id):
    """从 transcript 提取可能的新观点/数据点"""
    t = clean_transcript(transcript)
    if not t:
        return []
    # 找含数字、百分号、新趋势词的句子
    sentences = re.split(r'(?<=[.!?])\s+', t)
    points = []
    keywords_new = ["new", "launch", "release", "update", "announced", "just", "yesterday",
                    "this week", "breaking", "first time", "new study", "research shows",
                    "新", "刚", "最近", "本周", "首次", "最新", "研究显示"]
    for s in sentences:
        s_clean = s.strip()
        if not s_clean or len(s_clean) < 30 or len(s_clean) > 400:
            continue
        has_data = bool(re.search(r'\d+%|\d+\.\d+%|\$\d+|\d+ percent|\d+ 倍|\d+x', s_clean, re.IGNORECASE))
        has_new = any(kw in s_clean.lower() for kw in keywords_new)
        if has_data or has_new:
            points.append(s_clean)
    return points[:5]  # 最多 5 条


def log(msg):
    line = f"[{datetime.now(VANCOUVER_TZ).isoformat(timespec='seconds')}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def cmd_scan(args):
    """04:00 / 16:00 PT 数据采集：扫脚本，判定，入队，不写 HTML"""
    if not SCRIPT_DIR.exists():
        log(f"SCAN  ERR  SCRIPT_DIR missing: {SCRIPT_DIR}")
        sys.exit(1)

    processed = load_processed()
    queue = load_queue()
    transcripts = load_transcripts()
    new_tasks = []

    for p in sorted(SCRIPT_DIR.glob("2026-*.txt")):
        if not p.is_file() or "brief" in p.stem.lower():
            continue
        h = file_hash(p)
        key = str(p)
        if key in processed and processed[key] == h:
            continue  # 已扫描过

        meta, transcript, title, vid_id = get_transcript_and_title(p, transcripts)
        matches = classify_topic(p.name, transcript, meta["topic_part"])

        if not matches:
            # 新话题候选
            new_task = {
                "task_id": f"{meta['date']}_NEW_{p.stem}",
                "created_at": datetime.now(VANCOUVER_TZ).isoformat(),
                "type": "new_topic",
                "topic_id": None,  # 待 editor 命名
                "script_path": str(p),
                "script_name": p.name,
                "topic_part": meta["topic_part"],
                "author": meta["author"],
                "title_cn": title,
                "transcript_preview": clean_transcript(transcript)[:600],
                "reason": "未匹配任何现有话题 → 疑似新话题",
                "new_points": extract_new_points(transcript, None),
                "priority": "high",  # 新话题优先级高
            }
            new_tasks.append(new_task)
            log(f"SCAN  NEW-TOPIC  {p.name}")
        else:
            # 旧话题：检查是否有新观点
            top_match = matches[0]["rule"]
            points = extract_new_points(transcript, top_match["id"])
            if points:
                new_task = {
                    "task_id": f"{meta['date']}_UPD_{top_match['id']}_{p.stem}",
                    "created_at": datetime.now(VANCOUVER_TZ).isoformat(),
                    "type": "update_topic",
                    "topic_id": top_match["id"],
                    "html": top_match["html"],
                    "script_path": str(p),
                    "script_name": p.name,
                    "topic_part": meta["topic_part"],
                    "author": meta["author"],
                    "title_cn": title,
                    "transcript_preview": clean_transcript(transcript)[:600],
                    "reason": f"旧话题 '{top_match['id']}' 有新观点/数据点（{len(points)} 条）",
                    "new_points": points,
                    "priority": "medium",
                }
                new_tasks.append(new_task)
                log(f"SCAN  UPD-TOPIC  {p.name} → {top_match['id']} ({len(points)} new points)")
            else:
                log(f"SCAN  NO-NEW  {p.name} → {top_match['id']}（已有，无新观点）")

        processed[key] = h

    # 入队
    queue["pending"].extend(new_tasks)
    save_queue(queue)
    save_processed(processed)

    log(f"SCAN  DONE  新任务 {len(new_tasks)}，队列总数 {len(queue['pending'])}")

    if args.dry_run:
        print(json.dumps({"new_tasks": new_tasks, "queue_total": len(queue["pending"])},
                         ensure_ascii=False, indent=2))


def cmd_edit_one(args):
    """20:00–09:00 PT 编辑时段：处理一个任务"""
    queue = load_queue()

    if not queue["pending"]:
        log("EDIT  NO-TASK  队列为空")
        return

    # 选任务：优先级 high（新话题）优先，再按时间
    pending = sorted(queue["pending"], key=lambda x: (x.get("priority") != "high", x["created_at"]))

    if args.task_id:
        task = next((t for t in pending if t["task_id"] == args.task_id), None)
        if not task:
            log(f"EDIT  ERR  task_id not found: {args.task_id}")
            return
    else:
        task = pending[0]

    queue["in_progress"] = task["task_id"]
    save_queue(queue)

    log(f"EDIT  START  {task['task_id']}  type={task['type']}  topic={task.get('topic_id', 'NEW')}")

    # 这里留接口给 editor；当前版本先打印任务详情，等手动/agent 处理
    print(json.dumps(task, ensure_ascii=False, indent=2))

    # 标记完成（实际写入由 edit_apply.py 或人工完成）
    # 这里把任务移出 pending（写入 HTML 的逻辑在 edit_apply.py 中实现）
    # 当前 scan.py + edit_one.py 只负责队列调度


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_scan = sub.add_parser("scan", help="扫描 outputs，判定新话题/旧话题新观点，入队")
    p_scan.add_argument("--dry-run", action="store_true")
    p_scan.set_defaults(func=cmd_scan)

    p_edit = sub.add_parser("edit-one", help="处理一个待编辑任务")
    p_edit.add_argument("--task-id", help="指定任务 ID")
    p_edit.set_defaults(func=cmd_edit_one)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()