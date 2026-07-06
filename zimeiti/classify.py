#!/usr/bin/env python3
"""
zimeiti 自动归类引擎 v2

数据源：~/zimeiti_tiktok_monitor/outputs/*.txt（每天 2 次的视频脚本）
按文件名的 author + topic + 内容关键词判断归入哪个话题大全 HTML，
追加到对应 HTML 的"本话题已归类的视频脚本"和"更新日志"两节。

用法：
    python3 ~/zimeiti/scripts/classify.py            # 扫描所有 outputs（自动跳过已处理）
    python3 ~/zimeiti/scripts/classify.py --dry-run  # 预览不写
    python3 ~/zimeiti/scripts/classify.py --file <path>  # 处理单文件
    python3 ~/zimeiti/scripts/classify.py --reset    # 清空去重表

设计原则：
1. 数据源固定 ~/zimeiti_tiktok_monitor/outputs/，不依赖 inbox
2. 关键词匹配决定话题；并列（差 ≤1）全收（多归属）
3. 已处理过的文件用 SHA256 去重，不会重复追加
4. 输出文件名格式 YYYY-MM-DD_author_topic-name.txt
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "zimeiti"
TOPICS_HTML = BASE / "topics_html"
LOG_FILE = BASE / "scripts" / "classify.log"
PROCESSED = BASE / "scripts" / ".processed.json"

# 视频脚本数据源
SCRIPT_DIR = Path.home() / "zimeiti_tiktok_monitor" / "outputs"
TRANSCRIPT_DIR = Path.home() / "zimeiti_tiktok_monitor" / "work"

# 7 个真实话题（基于 74 个视频脚本主题聚类）
TOPIC_RULES = [
    {
        "id": "ai-search-geo-citation",
        "title": "AI 搜索 / GEO / AI Citation",
        "html": "01-ai-search-geo-citation.html",
        "keywords": [
            "ai search", "geo", "aeo", "llms.txt", "knowledge graph", "citation",
            "cited", "freshness", "ai overviews", "ai overview", "zero click",
            "zero-click", "answer pages", "answer-first", "answer first",
            "micro moments", "eeat", "fact list", "rank math", "brand mention",
            "hubspot", "anti spam", "reddit ai", "google becomes",
            "seo was never", "ai visibility", "google rank", "google spam",
            "google business profile", "knowledge base", "chatbot",
            "ai recommendation", "google fact list", "page one",
            "search intent", "conversational", "two score system",
        ],
    },
    {
        "id": "claude-ai-models",
        "title": "Claude / AI 模型与产品",
        "html": "02-claude-ai-models.html",
        "keywords": [
            "claude", "sonnet", "fable", "chatgpt", "gpt-", "openai",
            "frontier ai model", "model cost", "model comparison", "token subsidy",
            "claude skill", "prompt injection", "ai writing",
            "ai tells", "structure detection", "second brain", "cowork", "code modes",
            "sandcastles", "channel audit", "agents", "7 types",
            "glm", "mythos", "ai subscription",
        ],
    },
    {
        "id": "conversion-funnel",
        "title": "Conversion Funnel / 转化漏斗",
        "html": "03-conversion-funnel.html",
        "keywords": [
            "funnel", "checkout", "friction", "lead form", "form pruning",
            "landing page", "cro", "conversion", "ltv", "tiktok shop",
            "creator business", "international payments", "onboarding",
            "core value", "hot leads", "conversation ai", "highlevel",
            "300 million button", "price clock", "inherited steps",
            "welcome message", "stock photos", "tesla",
        ],
    },
    {
        "id": "big-tech-business",
        "title": "大公司新闻与科技商业",
        "html": "04-big-tech-business.html",
        "keywords": [
            "a24", "big tech", "meta ai", "spacex", "ipo", "amazon",
            "trump", "government", "crypto", "stake", "openai stake",
            "brain2qwerty", "meg", "typing", "export controls", "china",
            "cyberwar", "mythos", "glm", "crash landing",
            "artificial movie", "oscar pushback",
        ],
    },
    {
        "id": "content-creation-video",
        "title": "内容创作与视频策略",
        "html": "05-content-creation-video.html",
        "keywords": [
            "bullseye", "positioning", "lego method", "video hook",
            "skip rate", "shock score", "storytelling", "story funnel",
            "blockers", "failure modes", "script rhythm", "zigzag test",
            "six levels", "story ladder", "declarative hooks",
            "embedded truths", "video failure", "education",
            "long term marketing", "gen z", "brand touches",
        ],
    },
    {
        "id": "website-local-seo",
        "title": "网站与本地 SEO",
        "html": "06-website-local-seo.html",
        "keywords": [
            "google business profile", "local seo", "website annoyances",
            "ban list", "stock photos", "five seo sins", "diy diagnostics",
            "bot traffic", "ai agent visibility", "ai infrastructure",
            "inflation", "personal finance", "offline ai", "privacy",
            "side hustle", "quality gap", "quality risk",
            "website rebuild", "web mcp", "side hustle quality",
        ],
    },
    {
        "id": "marketing-trust-other",
        "title": "营销信任与其他战略",
        "html": "07-marketing-trust-other.html",
        "keywords": [
            "distribution", "owned channels", "relationships",
            "platform ai rewriting", "digital marketing three step",
            "gamma voice dictation", "deck workflow", "heygen",
            "avatar", "speech cleanup", "seamless cuts",
            "marketing visibility", "trust", "three step",
            "business owner", "visibility trust", "creator economy",
            "five seo sins", "diy", "diagnostics",
        ],
    },
]


# 手动归类（关键词覆盖不到的）
MANUAL_MAP = {
    "creator-business-international-payments-ai": "conversion-funnel",
    "digital-marketing-three-step-business-owner": "marketing-trust-other",
    "five-seo-sins-diy-website-diagnostics": "website-local-seo",
}


def load_processed():
    if PROCESSED.exists():
        try:
            return json.loads(PROCESSED.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_processed(d):
    PROCESSED.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_transcripts():
    """从 work/*_transcript*.txt 加载所有 transcript，按 video ID 索引"""
    transcripts = {}
    for f in TRANSCRIPT_DIR.glob("*_transcript*.txt"):
        parts = f.stem.replace("_transcript_clean", "").replace("_transcript", "").rsplit("_", 1)
        if len(parts) == 2:
            vid_id = parts[1]
            if vid_id not in transcripts:  # clean 优先
                transcripts[vid_id] = f.read_text(encoding="utf-8")
    return transcripts


def extract_video_id(text: str) -> str | None:
    m = re.search(r"(?:视频 ID|video ID|video id)\s*[::]\s*(\d+)", text)
    if m:
        return m.group(1)
    m2 = re.search(r"/video/(\d+)", text)
    if m2:
        return m2.group(1)
    return None


def parse_script_filename(name: str) -> dict:
    """YYYY-MM-DD_author_topic-name.txt"""
    base = name.replace(".txt", "")
    parts = base.split("_", 2)
    return {
        "date": parts[0] if len(parts) >= 1 else "",
        "author": parts[1] if len(parts) >= 2 else "",
        "topic_part": parts[2] if len(parts) >= 3 else "",
    }


def get_title_cn(text: str) -> str:
    """从 outputs 文件提取第一行 H1 标题"""
    first = text.split("\n")[0].lstrip("# ").strip()
    if first and first != "基本信息":
        return first
    return "(无标题)"


def classify(name: str, transcript: str, topic_part: str) -> list[dict]:
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

    # 手动兜底
    for key, tid in MANUAL_MAP.items():
        if key in topic_part.lower():
            rule = next(r for r in TOPIC_RULES if r["id"] == tid)
            return [{"rule": rule, "hits": 0, "manual": True}]
    return []


def build_item_html(meta: dict, transcript: str, rule: dict) -> str:
    t = transcript.strip()
    # 清理 transcript 中的 [time] 标记
    t_clean = re.sub(r'language=\S+\s+probability=\S+\s+duration=\S+\s*', '', t)
    t_clean = re.sub(r'\[\d+\.\d+-\d+\.\d+\]\s*', '', t_clean)

    excerpt = ""
    if t_clean:
        snippet = t_clean[:400].replace("\n", " ").strip()
        if len(t_clean) > 400:
            snippet += "..."
        excerpt = f'<div class="excerpt">🎙️ EN: {snippet}</div>'

    marker = f'<!-- appended:{meta["name"]} -->'
    return f'''<div class="item" {marker}>
  <div class="head">
    <span class="date">📅 {meta["date"]}</span>
    <span class="author">@{meta["author"]}</span>
  </div>
  <div class="title-cn">📝 {meta["title_cn"]}</div>
  <div class="topic-en">topic: {meta["topic_part"]}</div>
  {excerpt}
</div>
'''


def append_to_html(html_path: Path, item_html: str, log_entry: str, name: str) -> bool:
    if not html_path.exists():
        return False
    html = html_path.read_text(encoding="utf-8")

    # 防重复：marker 检查
    marker = f'<!-- appended:{name} -->'
    if marker in html:
        return False

    # 1. 追加到"本话题已归类的视频脚本"节
    pattern_files = re.compile(
        r'(<h2>本话题已归类的视频脚本</h2>.*?)(</section>)',
        re.DOTALL,
    )
    html, n_files = pattern_files.subn(
        lambda m: m.group(1) + item_html + "\n" + m.group(2),
        html, count=1,
    )

    # 2. 追加到"更新日志"节
    pattern_log = re.compile(
        r'(<h2>更新日志</h2>\s*<ul>)(.*?)(</ul>)',
        re.DOTALL,
    )
    html, n_log = pattern_log.subn(
        lambda m: m.group(1) + m.group(2).rstrip() + "\n    " + log_entry + m.group(3),
        html, count=1,
    )

    if n_files == 0 or n_log == 0:
        return False

    html_path.write_text(html, encoding="utf-8")
    return True


def log(msg: str):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def process_script(path: Path, transcripts: dict, dry_run: bool = False) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    text = path.read_text(encoding="utf-8")
    meta = parse_script_filename(path.name)
    meta["name"] = path.name
    title_cn = get_title_cn(text)
    meta["title_cn"] = title_cn

    vid_id = extract_video_id(text)
    transcript = transcripts.get(vid_id, "") if vid_id else ""
    if not transcript:
        # 退而求其次：用 outputs 里的英文脚本段（如有）
        m = re.search(r"# 英文脚本（Audio transcript）\s*\n+(.*?)(?=\n# |\Z)", text, re.DOTALL)
        if m:
            transcript = m.group(1).strip()

    matches = classify(path.name, transcript, meta["topic_part"])
    if not matches:
        log(f"NO-MATCH  {path.name}")
        return {"file": str(path), "matched": [], "status": "no-match"}

    result = {"file": str(path), "matched": [], "status": "ok"}
    for m in matches:
        rule = m["rule"]
        html_path = TOPICS_HTML / rule["html"]
        item_html = build_item_html(meta, transcript, rule)
        log_entry = f'<li><strong>{today}</strong> · 新增：<code>{meta["name"]}</code>（@{meta["author"]}）— {title_cn}</li>'

        if dry_run:
            log(f"DRY  {path.name} → {rule['id']} (hits={m['hits']})")
            result["matched"].append({"topic": rule["id"], "hits": m["hits"], "dry": True})
        else:
            ok = append_to_html(html_path, item_html, log_entry, meta["name"])
            tag = "OK" if ok else "DUP"
            log(f"{tag}  {path.name} → {rule['id']} (hits={m['hits']})")
            result["matched"].append({"topic": rule["id"], "hits": m["hits"], "appended": ok})
    return result


def main():
    parser = argparse.ArgumentParser(description="zimeiti 自动归类引擎 v2")
    parser.add_argument("--dry-run", action="store_true", help="只看，不写 HTML")
    parser.add_argument("--file", help="处理单个文件路径")
    parser.add_argument("--reset", action="store_true", help="清空 processed 表")
    args = parser.parse_args()

    if args.reset:
        if PROCESSED.exists():
            PROCESSED.unlink()
        log("RESET  processed 表已清空")

    processed = {} if args.reset else load_processed()
    results = []
    transcripts = load_transcripts()

    if args.file:
        p = Path(args.file).expanduser().resolve()
        if not p.exists():
            log(f"NOT-FOUND  {p}")
            sys.exit(1)
        r = process_script(p, transcripts, dry_run=args.dry_run)
        results.append(r)
    else:
        if not SCRIPT_DIR.exists():
            log(f"SCRIPT-DIR-MISSING  {SCRIPT_DIR}")
            sys.exit(1)
        for p in sorted(SCRIPT_DIR.glob("2026-*.txt")):
            if not p.is_file():
                continue
            if "brief" in p.name.lower():
                continue
            h = file_hash(p)
            key = str(p)
            if key in processed and processed[key] == h:
                continue  # 已处理过
            r = process_script(p, transcripts, dry_run=args.dry_run)
            processed[key] = h
            results.append(r)
        save_processed(processed)

    matched = sum(1 for r in results if r["matched"])
    unmatched = sum(1 for r in results if not r["matched"])
    log(f"DONE  共 {len(results)} 个脚本，归类 {matched}，未匹配 {unmatched}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()