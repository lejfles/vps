# What We Have vs. ChatGPT Share Content (6a491641)

**Source conversation**: https://chatgpt.com/share/6a491641-4d88-83e8-b019-c6d774216090
**Title**: 结构化数据资源与文档
**Local extraction**: `资料导入/chatgpt_share_6a491641_extracted.md`
**Date**: 2026-07-05

This document compares our existing 8-agent AI SEO system with the 4-turn
conversation extracted from the ChatGPT share link, identifies gaps, and
tracks which content has been merged into the codebase.

---

## 1. Existing AI SEO Agent System (v0.5)

### Folder skeleton
- `00_system/` — global config, MVP goal loop, run protocol, system overview
- `01_agents/01_strategy_agent/` ... `08_monitor_agent/` — 8 agents
- `02_handoffs/01_input_to_strategy/` ... `11_monitor_to_iteration/` + `failure_router/`
- `03_shared_knowledge/` — `audit_rubrics.md`, `commercial_boundary_rules.md`, `seo_principles.md`
- `04_projects/`, `05_runs/` (v02–v05 validation runs)
- `06_outputs/`, `07_templates/`, `08_tests/`, `09_docs/`
- `src/ai_seo_agent/` — Python pipeline (crawler, audit, report, performance, visibility)

### Existing 8 agents
1. Strategy Agent — business goal, content type, conversion, forbidden disclosures
2. Research Agent — search intent, SERP/competitor gap, cannibalization
3. Evidence Agent — facts, sources, anonymized cases, claims/evidence/reasoning
4. Risk Agent — commercial boundary + compliance filter
5. Content Architect Agent — blueprint, FAQ, schema, internal links
6. Writer Agent — drafts, meta, AI voice avoidance
7. Audit Agent — SEO, semantic, trust, AI-extractability, commercial risk, conversion
8. Monitor Agent — GSC/GA4/ranking/AI-citation/refresh backlog

### Existing handoffs (11 + failure_router)
1. input → strategy
2. strategy → research
3. research → evidence
4. evidence → risk
5. risk → architect
6. architect → writer
7. writer → audit
8. audit → human approval
9. approval → publish_or_deliver
10. publish → monitor
11. monitor → iteration
+ `failure_router/` — routes failures to the exact broken stage

---

## 2. ChatGPT Share — 4 turns of distilled content

### Turn 1 — User asks about a website + Google docs (with 2 screenshots)
> "图中网站里是什么内容？google是不是也发布了一个文档，在哪里？"

**Assistant identifies**: The Lazy Developer (thelazydeveloper.org) — a free
"AI-assisted dev / SEO / structured data" resource hub. Mentions Google Search
Central as the official structured data documentation source.

### Turn 2 — User asks to generate a markdown AI instruction
> "阅读这两个网站，生成 markdown 格式的 AI 指令，让 AI 完全掌握网站搭建、分析、修改结构化"

**Assistant delivers a comprehensive AI instruction**:
- **5 核心原则** (User-first / Google compliance / Evidence-first / Don't break business / Security on)
- **Phase 0–13 workflow**: Project ID → Architecture audit → Crawlability diagnosis → sitemap/robots/llms.txt → Metadata → Schema → Performance → Mobile/A11y → Security → Tracking/Validation → Modification plan → Output format
- **禁止事项** (forbidden acts): fake reviews, stuffed keywords, hidden schema, fake addresses, noindex abuse, etc.
- **输出格式**: 诊断摘要 + 问题清单 + Schema Map + 修改计划 + 代码修改 + 验证结果 + 后续建议

### Turn 3 — User asks about judgment evidence
> "判断的依据是什么？'是否合理'太粗了，需要详细规则"

**Assistant delivers 19 detailed judgment rubrics**:
1. Crawlability (HTML 是否可抓取 — CSR empty shell detection)
2. Title Tag (唯一性 / 准确性 / 不堆关键词)
3. Meta Description
4. Heading Structure (H1 唯一 / H2-H6 层级合理)
5. Canonical (首选 HTTPS 绝对 URL + 与 sitemap 一致 + 无 noindex/redirect)
6. Robots Meta (不是 noindex 误伤)
7. Sitemap (URL 准确性 + canonical 一致)
8. Robots.txt (sitemap 引用 + bot 访问控制)
9. Open Graph / Twitter Card
10. JSON-LD / Structured Data (rich result eligibility vs semantic enhancement)
11. llms.txt (AI crawler guidance)
12. Mobile / Responsive
13. Internal Linking
14. Content Quality (E-E-A-T, 不 thin content)
15. Performance (Core Web Vitals — LCP, INP, CLS)
16. Accessibility
17. Forms / API Security (XSS, CORS, CSP)
18. Tracking & Validation (GSC, GA4, Rich Results Test)
19. Final Report (修前/修后对比 + 证据)

**Each rubric follows**:
- Judgment Item
- Pass Criteria
- Fail Criteria
- Evidence
- Fix Action
- Risk Level: P0 / P1 / P2 / P3

### Turn 4 — User asks about keyword density
> "关键词放置 + H2-H6 架构里关键词数量有没有最优算法？插件建议关键词放在标题前 10%、频次等等"

**Assistant delivers Keyword Placement & Heading Architecture Module**:
- **No magic number**: Google has no official "best keyword density"; Yoast's 0.5%–3% is a heuristic, not a ranking formula
- **4 underlying principles** (cited Yoast / Rank Math / Google):
  1. **Prominence** (prominent position weight — Title/H1/H2)
  2. **Term frequency** (subject repetition signal — but no stuffing)
  3. **Distribution** (uniform distribution across the article)
  4. **Semantic coverage** (synonyms, related entities, not just exact match)
- **Keyword classification**: Primary / Secondary / Synonym / Entity / Long-tail Question
- **Title / H1 / Intro / H2-H6 / Anchor / Body rules** — each with Pass / Warning / Fail criteria

---

## 3. Gap Analysis — what we have vs. what we should add

| # | Topic from share | Current state | Gap | Action |
|---|---|---|---|---|
| 1 | 19 Pass/Fail rules (Crawlability, Title, Canonical, ...) | `audit_rubrics.md` has 5 high-level rubrics (SEO/Trust/AI/Commercial/Conversion) | Missing 19 detailed rules with P0-P3 risk levels | **MERGE into `audit_rubrics.md`** |
| 2 | Risk Level P0-P3分级 | Not standardized in handoffs | Need to add `risk_flags` field with P0-P3 values | **Update handoff schemas** |
| 3 | Phase 0-13 工作流 | Audit Agent has minimal checklist | Need full Phase SOP with output format | **Update `07_audit_agent/agent.md` + `checklist.md`** |
| 4 | Keyword Placement Module (Title/H1/Intro/H2-H6 rules) | Writer Agent has generic checklist | Need specific keyword placement + heading rules | **Update `06_writer_agent` + `05_content_architect_agent`** |
| 5 | Keyword Classification (Primary/Secondary/Synonym/Entity/Long-tail) | Not in our system | Need classification framework | **Add to `03_shared_knowledge/seo_principles.md`** |
| 6 | Prominence/Term frequency/Distribution/Semantic coverage | Not in our system | Need 4 principles module | **Add to `03_shared_knowledge/seo_principles.md`** |
| 7 | llms.txt check (Item 17 in 19 rules) | Mentioned in skill, not in audit | Need explicit llms.txt audit rule | **Add to `audit_rubrics.md` item 11** |
| 8 | JSON-LD: rich result eligibility vs semantic enhancement | Not distinguished | Need explicit distinction | **Add to `audit_rubrics.md` item 10** |
| 9 | Forbidden acts (no fake reviews, no keyword stuffing, etc.) | Partial in `commercial_boundary_rules.md` | Need explicit "禁止事项" list | **Add to `commercial_boundary_rules.md`** |
| 10 | Output format (诊断摘要/问题清单/Schema Map/修改计划/...) | Not standardized | Need template | **Add to `07_templates/`** |
| 11 | Modification audit (修前/修后对比 + 证据) | Not in our pipeline | Need before/after diff | **Add to `06_outputs/` or as a separate template** |
| 12 | Forms / API Security (XSS, CORS, CSP) | Not in our system | Out of SEO scope but mentioned in share | **Decision: keep out of pure-AI-SEO scope, but mention as cross-cutting concern** |

---

## 4. Decisions and rationale

### D1: Keep our 8-agent structure, do NOT add new agents
The share content does not introduce new specialized agent roles. It enhances
existing Audit Agent (07) with 19 rubrics, Writer Agent (06) with keyword
placement rules, and Content Architect Agent (05) with keyword classification.
No new agents needed.

### D2: Risk Level P0-P3 standardization
Add `risk_level: "P0" | "P1" | "P2" | "P3"` to:
- Handoff `risk_flags` field (per item)
- Audit Agent report (per finding)

Definitions (from share):
- **P0** = 阻止抓取、索引、构建、上线、安全的严重问题 (block crawl/index/build/deploy/security)
- **P1** = 明显影响 SEO、结构化数据资格、用户体验的问题 (clearly affects SEO/schema/UX)
- **P2** = 推荐优化项，不一定阻塞上线 (recommended optimization, not blocking)
- **P3** = 风格、维护性、增强型优化 (style/maintainability/enhancement)

### D3: Output format template
Audit Agent should emit the share's 7-section format:
A. 诊断摘要 / B. 问题清单 / C. 推荐 Schema Map / D. 修改计划 /
E. 代码修改 / F. 验证结果 / G. 后续建议

Add template: `07_templates/audit_report.template.md`

### D4: llms.txt audit rule (NEW)
llms.txt is the AI-crawler discovery file (like robots.txt but for LLMs).
Must be checked:
- File present at `/llms.txt` or `/llms-full.txt`
- Contains site description, key pages, key facts
- No forbidden disclosure

### D5: Out of scope
- Forms / API Security (XSS/CORS/CSP) — covered by Web Security Reviewer role, not AI-SEO Agent
- AI Overview citation guarantees — explicitly forbidden by share ("不要承诺")

---

## 5. Merge plan

| File to modify | Content to add |
|---|---|
| `03_shared_knowledge/audit_rubrics.md` | 19 Pass/Fail rules + llms.txt |
| `03_shared_knowledge/seo_principles.md` | 4 principles + Keyword classification |
| `03_shared_knowledge/commercial_boundary_rules.md` | 禁止事项 list |
| `01_agents/07_audit_agent/agent.md` | Phase 0-13 workflow + output format |
| `01_agents/07_audit_agent/checklist.md` | Phase-by-phase checklist |
| `01_agents/06_writer_agent/checklist.md` | Keyword placement rules |
| `01_agents/05_content_architect_agent/checklist.md` | Keyword classification + H2-H6 architecture |
| `02_handoffs/*/schema.json` (11 files) | Add `risk_level: P0-P3` field |
| `07_templates/audit_report.template.md` (NEW) | 7-section audit report template |
| `09_docs/workflow_diagram.html` (NEW) | New 8-agent workflow diagram |

---

## 6. Verification

After merge:
1. Run `git diff` and inspect changes
2. Verify all 8 agent checklists have new content
3. Verify all 11 handoff schemas have `risk_level` field
4. Render workflow diagram → verify visually
5. Commit + push to GitHub Pages
