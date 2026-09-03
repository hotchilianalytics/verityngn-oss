# Gemini 2026 capability gap vs VerityNgn OSS

**Date:** 2026-08-29  
**Branch:** `release/v3.0.0`  
**Purpose:** Decide what to adopt from Google’s current Gemini stack vs what our CI / claim pipeline still uniquely provides.

## Executive summary

Our OSS “Deep Research” today is a **single grounded `generate_content` call** over a sanitized `{video_id}_report.json` ([`verityngn/services/deepresearch/client.py`](../../verityngn/services/deepresearch/client.py)). Google now ships a true **Deep Research Agent** on the **Interactions API** (`deep-research-preview-04-2026` / Max) that plans, searches, and synthesizes over minutes with `background=true`. Separately, Gemini **native video understanding** (Files API, MM:SS timestamps, `media_resolution`) can extract claims/descriptions without our LangGraph segmentation path.

**Keep our differentiators:** counter-intel (YouTube reviews + press-release bias), self-referential evidence stripping, hard timeouts / checkpoints, URL safety, and claim-level probability calibration. **Spike next:** DR-direct ablation (this release) and optional Interactions-API agent behind a feature flag (Phase 2).

---

## Capability matrix

| Capability | Google surface | Relevance to OSS | Recommendation |
|------------|----------------|------------------|----------------|
| Deep Research Agent | Interactions API; agents `deep-research-preview-04-2026`, `deep-research-max-preview-04-2026`; `background=true` | Multi-step research with citations; **not** available via `generate_content` | Phase 2 adapter; do not rip out sanitize+CI yet |
| Visualization / charts in DR | Agent `visualization=auto` | Risk briefs with charts | Nice-to-have after agent spike |
| MCP / File Search / URL context / code execution | Default or configurable tools on agent | Ground on uploaded docs + web | Useful for legal dossiers (PDFs) |
| Native video understanding | Files API + generateContent; 1 FPS default; MM:SS refs; `media_resolution` | Claim discovery **without** full pipeline | Primary path for **DR-direct** ablation arm |
| File Search multimodal RAG | `gemini-embedding-2` stores | Index frames/transcripts | Optional later; not required for ablation |
| Grounding with Google Search | Already used in our DR client (`google_search` tool) | Keep for single-shot path | Keep |

Sources:
- https://ai.google.dev/gemini-api/docs/deep-research
- https://ai.google.dev/gemini-api/docs/video-understanding
- https://ai.google.dev/gemini-api/docs/file-search

---

## What our pipeline still buys

1. **Structured claim inventory** with timestamps and speakers → gallery / legal exhibit maps  
2. **Counter-intelligence** that actively seeks contradictory YouTube reviews and press-release-shaped sources  
3. **Self-referential evidence filter** so DR cannot cite the subject’s own PR as proof  
4. **Hard timeouts + checkpoints** — production resilience Google’s long agent runs do not replace  
5. **Calibrated TRUE/FALSE/UNCERTAIN** distributions (internal model; user-facing = risk labels)

## What Gemini may replace or shrink

1. Custom segmentation for *some* short videos if Files API video understanding is good enough for risk briefs  
2. Single-shot DR over JSON if the Interactions agent produces better cited briefs from video+transcript alone  
3. Manual “combined report” prose when agent outputs already include structure + charts  

## Ablation decision rule (this branch)

See `verityngn/services/ablation/`. If **DR-direct** ≥ full pipeline on human usefulness and ≥0.6 topic overlap on ≥2/3 seed videos → document DR-direct as **fast path**; keep full pipeline as **audit/CI path**. Else keep full as default; schedule Interactions agent as Phase-2 spike only.

## Phase-2 spike (not this PR)

- Adapter `verityngn/services/deepresearch/agent_client.py` wrapping `client.interactions.create(..., agent="deep-research-preview-04-2026", background=True)`  
- Feature flag `DEEP_RESEARCH_USE_AGENT=true`  
- Map agent steps → our `*_deep_private_report.md` + grounding audit JSON  

## Non-goals

- Predictions / RiskFactor product surfaces  
- Replacing URL safety or report sanitize  
- Claiming “Google Deep Research” brand as VerityNgn without disclosure
