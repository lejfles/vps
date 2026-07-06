# zimeiti · 自媒体话题大全自动归类引擎 v2

按用户 #自媒体 任务搭建：从历史 TikTok 视频脚本中归纳持续话题，每个话题一个持续更新的 HTML 大全（中文展示 + 权威资料补齐），每天收新脚本后自动追加。

## 数据源

- **视频脚本**：`~/zimeiti_tiktok_monitor/outputs/*.txt`（每天 2 次）
- **英文 transcript**：`~/zimeiti_tiktok_monitor/work/*_transcript_clean.txt`（按 video ID 关联）

## 在线浏览

**GitHub Pages**：<https://lejfles.github.io/vps/zimeiti/>

包含：
- `index.html` — 索引页（7 个话题入口 + 统计）
- `topics_html/01-07-*.html` — 7 个话题大全
- `README.md` — 本文件
- `classify.py` — 自动归类引擎源码

## 当前收录

| # | 话题 | 脚本数 | 创作者数 |
|---|---|---|---|
| 01 | AI 搜索 / GEO / AI Citation | 26 | 多 |
| 02 | Claude / AI 模型与产品 | 17 | 多 |
| 03 | Conversion Funnel / 转化漏斗 | 21 | 多 |
| 04 | 大公司新闻与科技商业 | 14 | 多 |
| 05 | 内容创作与视频策略 | 10 | 多 |
| 06 | 网站与本地 SEO | 4 | 多 |
| 07 | 营销信任与其他战略 | 16 | 多 |

合计 **78 个独立视频脚本**，跨 8 位独立创作者（@neilpatel、@tjrobertson52、@kallaway.marketing、@elenanisonoff、@rakos.media、@rankmathpro、@willfrancis24、@nocode.joshua），时间跨度 2026-05-24 → 2026-07-05。

## 本地目录结构

```
~/zimeiti/
├── inbox/                       (空目录保留 · 脚本引擎不再使用)
├── topics_html/                 7 个话题大全 HTML（本地源）
│   ├── 01-ai-search-geo-citation.html
│   ├── 02-claude-ai-models.html
│   ├── 03-conversion-funnel.html
│   ├── 04-big-tech-business.html
│   ├── 05-content-creation-video.html
│   ├── 06-website-local-seo.html
│   └── 07-marketing-trust-other.html
└── scripts/
    ├── classify.py              自动归类引擎 v2
    ├── classify.log             运行日志
    └── .processed.json          SHA256 hash 去重表
```

## 每天用法

### 收完当天 2 条脚本后

```bash
python3 ~/zimeiti/scripts/classify.py
```

**自动行为：**
1. 扫描 `~/zimeiti_tiktok_monitor/outputs/` 下所有 2026-*.txt（跳过 brief 简报）
2. 跳过 SHA256 hash 已记录的文件（处理过的不会重跑）
3. 对每个新文件：
   - 提取 video ID → 加载对应 transcript
   - 文件名 + transcript + 中文标题 → 关键词匹配
   - 命中最多的话题归属（并列差 ≤1 多归属）
   - 追加到对应 HTML 的"已归类脚本"和"更新日志"两节
   - HTML marker `<!-- appended:文件名 -->` 防止重复追加
4. 输出 JSON 报告到 stdout + 追加日志到 `classify.log`

### 预览（不写 HTML）

```bash
python3 ~/zimeiti/scripts/classify.py --dry-run
```

### 处理单文件

```bash
python3 ~/zimeiti/scripts/classify.py --file /path/to/script.txt
```

### 清空 hash 表（强制重新处理所有文件）

```bash
python3 ~/zimeiti/scripts/classify.py --reset
```

## 话题分类规则

7 个话题，每个由 `classify.py` 顶部的 `TOPIC_RULES` 决定。每个规则含：

- `id` — 唯一标识
- `title` — 显示标题
- `html` — 对应 HTML 文件名
- `keywords` — 关键词列表（英文小写匹配）

**调整关键词**：直接编辑 `classify.py` 的 `TOPIC_RULES`，加词即可。

**手动归类兜底**：`MANUAL_MAP` 字典，覆盖关键词够不到的文件（基于文件名子串匹配）。

## 新话题怎么办

1. **新建 HTML** 在 `topics_html/` 下，复制现有 HTML 作模板
2. HTML 必须含两个固定锚点（脚本依赖）：
   - `<h2>本话题已归类的视频脚本</h2>` — 后面跟空 `<div class="empty-state">` 或 `<div class="item">` 列表
   - `<h2>更新日志</h2>` — 后面跟 `<ul>...</ul>`
3. **编辑 `classify.py`**：
   - 在 `TOPIC_RULES` 加新规则
   - 必要时在 `MANUAL_MAP` 加兜底
4. 重跑 `classify.py`

## 自动定时（可选）

```bash
crontab -e
# 每天 9:00、21:00 各跑一次（对应每天 2 次脚本更新）
0 9,21 * * * /usr/bin/python3 /home/ubuntu/zimeiti/scripts/classify.py >> /home/ubuntu/zimeiti/scripts/cron.log 2>&1
```

## GitHub Pages 部署

7 个 HTML + 索引页已部署到 `lejfles/vps` 仓库：

```bash
cd ~/lejfles-vps
git add zimeiti/
git commit -m "v2: 7 topic wikis from 78 TikTok scripts"
git push
```

Pages 部署需 15–30 秒，验证：

```bash
curl -sI https://lejfles.github.io/vps/zimeiti/ | head -3
curl -sI https://lejfles.github.io/vps/zimeiti/topics_html/01-ai-search-geo-citation.html | head -3
```

## 话题大全 HTML 结构

每个 HTML 含：

1. **Header** — 话题标题、副标题、统计
2. **话题定义** — 话题范围与核心议题
3. **权威资料 · 关键概念解释** — 行业权威资料链接 + 简要解释
   - 例如：Princeton GEO 论文、Google Search Central、E-E-A-T、Baymard、Nielsen Norman 等
4. **本话题已归类的视频脚本** — 按日期排序，每篇含：
   - 📅 日期
   - 👤 作者（TikTok handle）
   - 📝 中文标题
   - 英文 topic key
   - 🎙️ 英文 transcript 节选（前 400 字符）
5. **更新日志** — 初版建档 + 每日新增条目

## 设计原则

1. **数据源固定**：每天 2 次脚本源在 `~/zimeiti_tiktok_monitor/outputs/`，不依赖人工放置
2. **三层去重**：SHA256 hash + HTML marker + manual map，避免重复追加
3. **多归属支持**：一个脚本可同时归入多个话题（关键词并列时差 ≤1 全收）
4. **持续追加语义**：只追加不删除，体现"持续更新的话题大全"语义
5. **公开展示**：所有内容推到 GitHub Pages，全球可访问