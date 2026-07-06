# zimeiti 自动归类工作流 · v3.2

## 整体流程图（文本版）

```
┌──────────────────────────────────────────────────────────────────┐
│                    数据源（生产环境，每天 2 次）                    │
│                                                                  │
│   ~/zimeiti_tiktok_monitor/outputs/2026-*.txt                    │
│   ├── 79 个视频脚本（中文改写 + 英文 transcript）                  │
│   └── 由其他 pipeline 每天 04:00 / 16:00 PT 写入                  │
│                                                                  │
│   ~/zimeiti_tiktok_monitor/work/                                  │
│   ├── *_transcript_clean.txt （英文清洁稿，71 个）                │
│   └── *_transcript.txt （早期英文原稿，80 个）                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 每天 04:00 / 16:00 PT（CST 19:00 / 07:00）
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│           [CRON 1 + 2] queue_engine.py scan                       │
│                                                                  │
│   1. glob outputs/*.txt                                          │
│   2. SHA256 hash 去重（vs .processed.json）                      │
│   3. 对每个新脚本：                                                │
│      a. 读文件 → 提取 video ID                                    │
│      b. 用 video ID 关联 work/ 下的 transcript                     │
│      c. 关键词匹配 → 7 个话题分类（可能多归属）                    │
│      d. 判定：                                                     │
│         • 命中现有话题 + 有新观点  → 入队 update_topic            │
│         • 命中现有话题 + 无新观点  → 跳过                         │
│         • 不命中任何话题           → 入队 new_topic (priority=high)│
│   4. 任务写入 queue.json                                         │
│   5. 更新 .processed.json                                         │
│                                                                  │
│   ❌ 此阶段不修改任何 HTML                                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              queue.json（待编辑任务队列）                           │
│                                                                  │
│   {                                                              │
│     "pending": [                                                 │
│       {                                                          │
│         "task_id": "...",                                        │
│         "type": "new_topic" | "update_topic",                    │
│         "topic_id": "...",                                       │
│         "script_name": "...",                                    │
│         "new_points": ["...", "..."],                            │
│         "priority": "high" | "medium"                            │
│       },                                                         │
│       ...                                                        │
│     ],                                                           │
│     "completed_today": N                                         │
│   }                                                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 每天 20:00–09:00 PT（CST 11:00–23:30 每 30 分钟 + 00:00）
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│           [CRON 3 + 4] edit_apply.py apply                        │
│                                                                  │
│   1. 从 queue.json 取一个 pending 任务                            │
│      （优先级 high 优先 = 新话题优先）                             │
│   2. 检查 HTML marker（data-updated="..."）防重复                  │
│   3. 按 type 处理：                                                │
│                                                                  │
│      ┌─────────────────────────────────────────┐                │
│      │ type = new_topic                         │                │
│      │ → 创建新 HTML 文件                       │                │
│      │   topics_html/08-xxx.html                │                │
│      │ → 包含骨架 + transcript 摘要 + 触发日志   │                │
│      └─────────────────────────────────────────┘                │
│                                                                  │
│      ┌─────────────────────────────────────────┐                │
│      │ type = update_topic                      │                │
│      │ → 找到现有话题 HTML                      │                │
│      │ → 在"新观点补充"section 追加              │                │
│      │ → 写入更新日志（时间 + 脚本名）           │                │
│      └─────────────────────────────────────────┘                │
│                                                                  │
│   4. 任务标记完成，移出 pending                                    │
│   5. 写入 in_progress / last_processed                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   本地产物（~/zimeiti/）                          │
│                                                                  │
│   topics_html/                                                   │
│   ├── 01-ai-search-geo-citation.html  (GEO 主题深度文章)           │
│   ├── 02-claude-ai-models.html        (AI 模型与产品)            │
│   ├── 03-conversion-funnel.html       (转化漏斗)                 │
│   ├── 04-big-tech-business.html       (大公司新闻)               │
│   ├── 05-content-creation-video.html  (内容创作)                 │
│   ├── 06-website-local-seo.html       (网站本地 SEO)             │
│   ├── 07-marketing-trust-other.html   (营销信任)                 │
│   └── 08-big-tech-waters-down-water.html (自动新建)              │
│                                                                  │
│   index.html (v3.2 索引页，8 话题卡片 + 时序机制说明)             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ 每天 18:00 PT（CST 09:00）
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│           [CRON 5] sync_to_pages.sh                               │
│                                                                  │
│   cd ~/lejfles-vps                                               │
│   git add zimeiti/topics_html/ zimeiti/index.html                 │
│   git commit -m "zimeiti auto-sync: ..."                         │
│   git push                                                       │
│   → GitHub Pages 1-2 分钟内自动部署                               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                  GitHub Pages 公开发布                            │
│                                                                  │
│   https://lejfles.github.io/vps/zimeiti/                          │
│   ├── / (索引页)                                                  │
│   ├── /topics_html/01-08.html                                     │
│   ├── /queue_engine.py /edit_apply.py /patch_v3_anchors.py        │
│   └── /README.md                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 时序图（24 小时循环）

```
CST:    07  08  09  10  11  12  13  14  15  16  17  18  19  20  21  22  23  00  01  02  03  04  05  06
        ├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤

PT:     16  17  18  19  20  21  22  23  00  01  02  03  04  05  06  07  08  09  10  11  12  13  14  15

EVENTS: [S1]                                            [S2]                                                  [S1]
       scan                                            scan                                                  scan
       07:00                                           19:00                                                 07:00
       CST                                             CST                                                   CST
       PT 16:00                                         PT 04:00                                              PT 16:00

                       [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*] [E*]
                       每30分钟                          PT 20:00–09:00                                              每30分钟
                       edit_apply                         编辑窗口                                                  edit_apply
                       11:00–23:30                                                                       00:00       11:00–23:30
                                                                                                            额外一次

[Sync]                    [Y]
git push                                                  ↕
09:00 CST
PT 18:00

Legend:
  S1 / S2 = queue_engine scan
  E* = edit_apply apply
  Y = sync_to_pages.sh (git push)
```

## 三层时间线映射

| 温哥华时间 (PDT, UTC-7) | 系统时区 CST (UTC+8) | 动作 | Cron |
|---|---|---|---|
| 04:00 早晨 | 19:00 当晚 | 数据采集 | `0 19 * * *` |
| 16:00 下午 | 07:00 次日早晨 | 数据采集 | `0 7 * * *` |
| 20:00 晚上 | 11:00 次日中午 | 编辑开始 | `*/30 11-23 * * *` |
| 23:30 深夜 | 14:30 次日下午 | 编辑继续 | 同上 |
| 09:00 早晨（次日） | 00:00 午夜 | 编辑收尾 | `0 0 * * *` |
| 18:00 傍晚 | 09:00 早晨 | 同步 Pages | `0 9 * * *` |

## 数据流保护（防重复）

```
Script 文件
   │
   ▼
SHA256 hash ────→ .processed.json
   │
   ▼ (新文件才进)
关键词分类
   │
   ▼
写入 queue.json 任务
   │
   ▼
HTML data-updated marker ────→ HTML 文件
   │
   ▼ (新 marker 才写)
实际追加
```

三层去重保证：
1. **hash 层**：同一文件不被 scan 两次
2. **task_id 层**：同一任务不被入队两次
3. **marker 层**：同一脚本的新观点不被 HTML 重复追加

## 当前实际状态（2026-07-06 23:02 CST）

- ✅ 8 话题 HTML 全部生成并部署
- ✅ 82 个 outputs 全部扫描（79 历史 + 3 测试）
- ✅ 60 个 update 任务已 apply，1 个 new_topic 任务已 apply
- ✅ queue.json: pending=0, completed_today=62
- ✅ GitHub Pages: 13/13 HTTP 200
- ⏳ 等 cron 下一次触发（明早 07:00 CST 扫描）