# File Ownership & Relationships — v0.6

> Each file belongs to exactly one **layer** (00–09). Some files are
> consumed by multiple **agents** (cross-references). This table is the
> canonical reference for "where does this file live" and "who reads it".

**Last updated**: 2026-07-05 (v0.6)
**Backup**: `/home/ubuntu/ai_seo_agent_backup_before_v05_chatgpt_merge_*.tar.gz`

---

## Layer 00 — `00_system/`

System-level configuration. Read at startup by all agents.

| File | Purpose | Consumed by |
|---|---|---|
| `global_config.example.json` | Global defaults | All agents (read once at startup) |
| `mvp_goal_loop.md` | MVP iteration loop definition | All agents |
| `run_protocol.md` | How to run a single iteration | 02_research → 08_monitor |
| `system_overview.md` | What the whole system is | New agents / onboarding |

---

## Layer 01 — `01_agents/01..08_<name>_agent/`

**Each agent has 4 files**:

| File pattern | Purpose |
|---|---|
| `README.md` | Human-readable summary of the agent |
| `agent.md` | Role + input + output + working principles + completion criteria |
| `checklist.md` | Step-by-step checklist (per-Phase for audit agent) |
| `input_schema.json` | Expected input shape |
| `output_schema.json` | Output shape this agent produces |

### Agent ownership (which files each agent owns)

| Agent | Owns (writes) | Consumes (reads) |
|---|---|---|
| **01_strategy_agent** | `02_handoffs/01_input_to_strategy/handoff.json` | `00_system/*`, `04_projects/<id>/project_config.yaml`, user input |
| **02_research_agent** | `02_handoffs/02_strategy_to_research/handoff.json` | `01_strategy_agent/handoff`, `03_shared/seo_principles.md` |
| **03_evidence_agent** | `02_handoffs/03_research_to_evidence/handoff.json` | `02_research_agent/handoff`, public sources |
| **04_risk_agent** | `02_handoffs/04_evidence_to_risk/handoff.json` | `03_evidence_agent/handoff`, `03_shared/commercial_boundary_rules.md` |
| **05_content_architect_agent** | `02_handoffs/05_risk_to_architect/handoff.json`, `05_runs/<id>/content_brief.md`, `keyword_map.md`, `outline.md`, `faq_block.md`, `schema_snippet.json`, `meta.md`, `internal_link_plan.md` | `04_risk_agent/handoff`, `03_shared/audit_rubrics.md` (Keyword Module + Rules 2/4/10/14), `03_shared/seo_principles.md` |
| **06_writer_agent** | `02_handoffs/06_architect_to_writer/handoff.json`, `05_runs/<id>/draft.md` | `05_content_architect_agent/handoff`, `03_shared/audit_rubrics.md` (Keyword Module), `03_shared/commercial_boundary_rules.md` |
| **07_audit_agent** ★ | `02_handoffs/07_writer_to_audit/handoff.json`, `05_runs/<id>/audit_report.md`, `audit_report.json` | `06_writer_agent/handoff`, `03_shared/audit_rubrics.md` (all 19 rules + Keyword Module), `03_shared/commercial_boundary_rules.md`, `05_runs/<id>/draft.md`, crawl evidence |
| **08_monitor_agent** | `02_handoffs/11_monitor_to_iteration/handoff.json` | `09/10 publish output`, GSC/GA4 (if access granted), `03_shared/audit_rubrics.md` |

---

## Layer 02 — `02_handoffs/`

**Each handoff folder has 3 files**: `schema.json` + `handoff.md` + `example.json`

### Handoff chain (data flow direction)

```
00_input
  → 01_input_to_strategy  → 02_strategy_to_research
  → 03_research_to_evidence → 04_evidence_to_risk
  → 05_risk_to_architect  → 06_architect_to_writer
  → 07_writer_to_audit    → 08_audit_to_human_approval
  → 09_approval_to_publish_or_deliver
  → 10_publish_to_monitor → 11_monitor_to_iteration (back to 02 or 03)

+ failure_router/         (on fail, route to specific broken agent)
```

### Handoff file ownership

| Handoff | Produced by | Consumed by |
|---|---|---|
| `01_input_to_strategy/` | User / external input | 01_strategy_agent |
| `02_strategy_to_research/` | 01_strategy_agent | 02_research_agent |
| `03_research_to_evidence/` | 02_research_agent | 03_evidence_agent |
| `04_evidence_to_risk/` | 03_evidence_agent | 04_risk_agent |
| `05_risk_to_architect/` | 04_risk_agent | 05_content_architect_agent |
| `06_architect_to_writer/` | 05_content_architect_agent | 06_writer_agent |
| `07_writer_to_audit/` | 06_writer_agent | 07_audit_agent |
| `08_audit_to_human_approval/` | 07_audit_agent | Human approver |
| `09_approval_to_publish_or_deliver/` | Human approver | Publisher (out of scope of AI agent — manual or cron) |
| `10_publish_to_monitor/` | Publisher | 08_monitor_agent |
| `11_monitor_to_iteration/` | 08_monitor_agent | (any earlier agent — refresh) |
| `failure_router/` | 07_audit_agent (on fail) | (any earlier agent — back-route to broken stage) |

### v0.6 schema additions (all 12 files updated)

- `risk_levels` field: `{P0, P1, P2, P3}` with definitions
- `risk_flags` field: structured array of `{id, risk_level, category, rule_reference, description, evidence, fix_action, owner_agent}`
- `version: "0.6"` + `last_updated: "2026-07-05"`

---

## Layer 03 — `03_shared_knowledge/`

**Owned by no single agent — read by many.**

| File | Consumed by (who reads it) |
|---|---|
| `audit_rubrics.md` | **07_audit_agent** (all 19 rules + Phase 0-13) · **06_writer_agent** (Keyword Module: Title/H1/Intro/H2-H6/Anchor/Body) · **05_content_architect_agent** (Keyword classification + H2-H6 + Schema) · **08_monitor_agent** (refresh backlogs) |
| `seo_principles.md` | **02_research_agent** (4 principles) · **05_content_architect_agent** (H2-H6 architecture) · **06_writer_agent** (anchor rules) |
| `commercial_boundary_rules.md` | **04_risk_agent** (DNP filter) · **06_writer_agent** (commercial checklist) · **07_audit_agent** (Commercial Risk Audit) |

---

## Layer 04 — `04_projects/`

Per-client project config.

| File pattern | Owned by | Consumed by |
|---|---|---|
| `<project_id>/project_config.yaml` | Project owner | 01_strategy_agent (init), then all agents via handoff |

---

## Layer 05 — `05_runs/`

**Per-run outputs**. One folder per `run_id`.

| File pattern | Owned by | Consumed by |
|---|---|---|
| `draft.md` | 06_writer_agent | 07_audit_agent |
| `content_brief.md` | 05_content_architect_agent | 06_writer_agent |
| `keyword_map.md` | 05_content_architect_agent | 06_writer_agent |
| `outline.md` | 05_content_architect_agent | 06_writer_agent |
| `faq_block.md` | 05_content_architect_agent | 06_writer_agent |
| `schema_snippet.json` | 05_content_architect_agent | 06_writer_agent |
| `meta.md` | 05_content_architect_agent | 06_writer_agent |
| `internal_link_plan.md` | 05_content_architect_agent | 06_writer_agent |
| `audit_report.md` | 07_audit_agent | Human approver |
| `audit_report.json` | 07_audit_agent | 07_audit_agent itself (machine-readable), downstream tools |
| `summary.json` | pipeline (`src/ai_seo_agent/pipeline.py`) | All run-record consumers |
| `report.html` | `src/ai_seo_agent/report.py` | Human reviewer |
| `report.pdf` | `src/ai_seo_agent/report.py` | Human reviewer / stakeholder |

---

## Layer 06 — `06_outputs/`

Final approved deliverables. Read-only archive after human approval.

| File pattern | Owned by | Notes |
|---|---|---|
| `<run_id>/final_*.md` | 09 (publish) | Once published, never modified |

---

## Layer 07 — `07_templates/`

Reusable templates. Owned by 05/06/07 agents.

| File | Owned by | Consumed by |
|---|---|---|
| `project_config.template.json` | 01_strategy_agent | 04_projects (per-client copies) |
| `content_brief.template.md` | 05_content_architect_agent | 05_runs (per-run copies) |
| `run_record.template.json` | pipeline | 05_runs (per-run copies) |
| `audit_report.template.md` (NEW v0.6) | 07_audit_agent | 05_runs/<id>/audit_report.md |

---

## Layer 08 — `08_tests/`

Test code. Owned by `src/ai_seo_agent/` maintainers.

| File pattern | Purpose |
|---|---|
| `fixtures/site/*` | Sample HTML / sitemap / robots.txt for crawler testing |
| `fixtures/gsc_sample.csv` | Sample GSC export for performance analyzer |
| `fixtures/ga4_sample.csv` | Sample GA4 export |
| `fixtures/ai_visibility_sample.csv` | Sample AI answer observations |
| `unit/test_*.py` | Unit tests per module |
| `integration/test_cli_e2e.py` | End-to-end CLI tests |

---

## Layer 09 — `09_docs/`

Documentation + diagrams.

| File | Purpose |
|---|---|
| `folder_structure.md` | Old folder structure doc (kept for reference) |
| `implementation_notes.md` | Implementation notes |
| `what_we_have_vs_chatgpt_share.md` (NEW v0.6) | Comparison of existing system vs ChatGPT share 6a491641 |
| `workflow_diagram.html` (NEW v0.6) | 8-Agent workflow diagram (HTML) |
| `workflow_diagram.png` (NEW v0.6) | 8-Agent workflow diagram (PNG export) |
| `file_ownership_and_relationships.md` (NEW v0.6) | THIS file |

---

## `资料导入/` (project root)

| File | Purpose |
|---|---|
| `chatgpt_share_6a491641_extracted.md` (NEW v0.6) | Full ChatGPT share conversation extraction (4 turns, 76KB) |

---

## Code layer — `src/ai_seo_agent/`

Python pipeline. Owned by 07_audit_agent + 08_monitor_agent.

| File | Purpose | Triggered by |
|---|---|---|
| `__init__.py` | Package init | n/a |
| `models.py` | Data models | All |
| `pipeline.py` | Pipeline orchestration | CLI |
| `crawler.py` | Public-page crawler (respects robots.txt) | 07_audit_agent |
| `site_audit.py` | Site audit logic | 07_audit_agent |
| `audit.py` | Audit logic (per-rule) | 07_audit_agent |
| `report.py` | HTML/PDF report generation | 07_audit_agent |
| `performance.py` | GSC/GA4 CSV analyzer | 08_monitor_agent |
| `visibility.py` | AI Visibility Monitor (CSV-based, manual) | 08_monitor_agent |
| `cli.py` | CLI entry point | shell |

---

## File-to-Agent Quick Reference (most-asked mapping)

| File path | Owning agent(s) | Primary consumer(s) |
|---|---|---|
| `03_shared_knowledge/audit_rubrics.md` | 07_audit_agent (maintainer) | 07_audit_agent, 06_writer_agent, 05_content_architect_agent |
| `03_shared_knowledge/seo_principles.md` | 02_research_agent (maintainer) | 02_research_agent, 05_content_architect_agent, 06_writer_agent |
| `03_shared_knowledge/commercial_boundary_rules.md` | 04_risk_agent (maintainer) | 04_risk_agent, 06_writer_agent, 07_audit_agent |
| `01_agents/07_audit_agent/agent.md` | 07_audit_agent | 07_audit_agent |
| `01_agents/07_audit_agent/checklist.md` | 07_audit_agent | 07_audit_agent |
| `01_agents/06_writer_agent/checklist.md` | 06_writer_agent | 06_writer_agent |
| `01_agents/05_content_architect_agent/checklist.md` | 05_content_architect_agent | 05_content_architect_agent |
| `07_templates/audit_report.template.md` | 07_audit_agent | 07_audit_agent |
| `02_handoffs/*/schema.json` | The source agent of that handoff | The target agent |
| `09_docs/workflow_diagram.html` | 07_audit_agent (visual owner) | Stakeholders, new agents |
| `09_docs/what_we_have_vs_chatgpt_share.md` | 01_strategy_agent (visual owner) | Stakeholders |

---

## Cross-Reference Graph (text version)

```
00_system/*
    ↓ (read at startup)
01_strategy_agent ──→ 02_strategy_to_research
    ↓                       ↓
                          02_research_agent ──→ 03_research_to_evidence
                              ↓                       ↓
                                                    03_evidence_agent ──→ 04_evidence_to_risk
                                                        ↓                       ↓
                                                                              04_risk_agent ──→ 05_risk_to_architect
                                                                                  ↓                       ↓
                                                                                                            05_content_architect_agent ──→ 06_architect_to_writer
                                                                                                                ↓                       ↓
                                                                                                                                          06_writer_agent ──→ 07_writer_to_audit
                                                                                                                                              ↓                       ↓
                                                                                                                                                                    07_audit_agent ──→ 08_audit_to_human_approval
                                                                                                                                                                        ↓                       ↓
                                                                                                                                                                                              human_approval ──→ 09_approval_to_publish_or_deliver
                                                                                                                                                                                                                  ↓
                                                                                                                                                                                                                    publish ──→ 10_publish_to_monitor
                                                                                                                                                                                                                                ↓
                                                                                                                                                                                                                                  08_monitor_agent ──→ 11_monitor_to_iteration
                                                                                                                                                                                                                                      ↓ (back to 02 or 03)
                                                                                                                                                                                                                                        loop

shared:
  03_shared_knowledge/audit_rubrics.md          ← consumed by 05, 06, 07
  03_shared_knowledge/seo_principles.md          ← consumed by 02, 05, 06
  03_shared_knowledge/commercial_boundary_rules.md ← consumed by 04, 06, 07
  07_templates/audit_report.template.md         ← consumed by 07

side paths:
  failure_router ← (07 fails) → back to specific broken agent
  资料导入/chatgpt_share_6a491641_extracted.md   ← source provenance (read-only)
```
