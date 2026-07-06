# zimeiti · 自媒体话题大全 v3.2（分层时序版）

按用户 #自媒体 任务搭建：每天从历史视频脚本中归纳持续话题，每篇话题文章持续更新（不再停留）。

**核心**：分层时序 — 数据采集（PT 04:00 / 16:00）只判定不入库；编辑写入（PT 20:00–09:00）每 30 分钟处理一个任务。

## 在线浏览

- **索引**：<https://lejfles.github.io/vps/zimeiti/>
- **8 个话题文章**：索引页可点击进入
- **脚本源码**：<https://lejfles.github.io/vps/zimeiti/queue_engine.py> 等

## 当前状态（截至 2026-07-06）

| 项目 | 数值 |
|---|---|
| 话题文章数 | 8 篇 |
| 视频脚本支撑 | 81 个 |
| 总字数 | 77,553 字 |
| 已自动补充新观点 | 60 个 |

8 个话题：AI 搜索/GEO、Claude/AI 模型、转化漏斗、大公司新闻、内容创作、网站/本地 SEO、营销信任其他、Big Tech 水消耗（最新新建）。

## 分层时序架构

### 三层时间线（系统时区 CST）

| Cron 表达式 | 动作 | 对应温哥华时间 |
|---|---|---|
| `0 19 * * *` | `queue_engine.py scan` | ≈ PT 04:00 |
| `0 7 * * *` | `queue_engine.py scan` | ≈ PT 16:00 |
| `*/30 11-23 * * *` | `edit_apply.py apply` | PT 20:00–14:30 |
| `0 0 * * *` | `edit_apply.py apply` | ≈ PT 09:00 |
| `0 9 * * *` | `sync_to_pages.sh` | ≈ PT 18:00 |

### 工作流

```
[PT 04:00] queue_engine scan ──┐
[PT 16:00] queue_engine scan ──┤
                               ▼
                    queue.json (待编辑任务)
                               │
[PT 20:00–09:00 每30分钟]       │
   edit_apply apply ←──────────┘
                               ▼
                  topics_html/*.html (实际写入)
                               │
[PT 18:00] sync_to_pages ──────┘
                               ▼
                  git push → GitHub Pages
```

### 队列系统

`~/zimeiti/scripts/queue.json`：
```json
{
  "pending": [...],
  "in_progress": "task_id 或 null",
  "completed_today": 60,
  "last_processed": "ISO 时间"
}
```

每条任务：
```json
{
  "task_id": "2026-07-05_UPD_ai-search-geo-citation_2026-07-05_neilpatel_answer-first",
  "type": "new_topic | update_topic",
  "topic_id": "ai-search-geo-citation",
  "script_name": "2026-07-05_..._answer-first-content-three-fixes-ai-citation.txt",
  "new_points": ["...", "..."],
  "priority": "high | medium"
}
```

## 三层去重机制

1. **SHA256 hash** (`~/zimeiti/scripts/.processed.json`)：防 scan 重复扫描同一脚本
2. **HTML marker** (`data-updated="..."`)：防 edit_apply 重复追加同一脚本的新观点
3. **task_id 唯一性**：防同一任务被多次入队

## 手动操作

```bash
# 扫描（04/16 点用，cron 自动；手动调试也行）
python3 ~/zimeiti/scripts/queue_engine.py scan

# 看队列
python3 ~/zimeiti/scripts/edit_apply.py list

# 处理一个任务（按优先级选）
python3 ~/zimeiti/scripts/edit_apply.py apply

# 处理指定任务
python3 ~/zimeiti/scripts/edit_apply.py apply --task-id <task_id>

# 重置 hash 表（强制重新扫描所有脚本）
rm ~/zimeiti/scripts/.processed.json
python3 ~/zimeiti/scripts/queue_engine.py scan
```

## 目录结构

```
~/zimeiti/
├── index.html                  # 索引页 v3.2
├── README.md                   # 本文件
├── topics_html/                # 8 篇话题文章
│   ├── 01-ai-search-geo-citation.html
│   ├── 02-claude-ai-models.html
│   ├── 03-conversion-funnel.html
│   ├── 04-big-tech-business.html
│   ├── 05-content-creation-video.html
│   ├── 06-website-local-seo.html
│   ├── 07-marketing-trust-other.html
│   └── 08-big-tech-waters-down-water.html  (NEW)
└── scripts/
    ├── queue_engine.py         # 04/16 点扫描
    ├── edit_apply.py           # 20-09 点编辑
    ├── patch_v3_anchors.py     # 给 v3 文章补 anchor（一次性）
    ├── classify.py             # 老版 v2 分类器（已废弃但保留）
    ├── sync_to_pages.sh        # 同步 GitHub Pages
    ├── crontab.txt             # cron 配置
    ├── queue.json              # 任务队列
    ├── .processed.json         # SHA256 去重表
    └── cron-*.log              # cron 运行日志
```

## 同步 lejfles-vps 仓库

```bash
cd ~/lejfles-vps
git add zimeiti/
git commit -m "zimeiti: 描述"
git push
```

## 注意事项

- **不在 HTML 中展示原作者信息**（TikTok handle、时间戳）
- **权威资料仅作为论据支撑**，不是堆砌列表
- **新观点持续追加**，不替换已有内容
- **新话题自动创建**（按 08、09、10... 编号）
- **新话题优先级高**（在队列中先处理）