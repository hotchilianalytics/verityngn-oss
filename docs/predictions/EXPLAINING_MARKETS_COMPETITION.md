# Explaining Markets — UChicago / Optiver competition

**Date:** 2026-08-14  
**Status:** Assessed · SDK register recommended · no competition-submission commitment until S00–S15 registry + CAR join work

---

## What it is

**Explaining Markets** is an open AI benchmark created by researchers at the **University of Chicago Booth School of Business** and launched in partnership with **Optiver**.

| | |
|--|--|
| **Site** | [explainingmarkets.ai](https://explainingmarkets.ai/) |
| **PIs** | Ralph S. J. Koijen · Bradford (Lynch) Levy |
| **Sponsor** | Optiver |
| **Paper** | *Assessing the Benefits of Optimized Agentic AI Systems for Asset Pricing* (BFI working paper) |
| **Press** | [UChicago News](https://news.uchicago.edu/story/how-ai-starting-explain-stock-price-moves) · [Optiver announcement](https://www.optiver.com/insights/news/explaining-markets-ai-competition/) |

### Task

Participants build agents that, as companies report earnings, receive a **transcript summary** and submit a prediction of how the market will respond — using **only information available at announcement time**. Predictions are scored against **live realized outcomes** on a public leaderboard.

### Headline result to beat

Best-optimized agentic systems more than double explained variation in contemporaneous stock returns around earnings announcements: **R² from ~8% → near 20%**.

### Why the design matches our hygiene doctrine

1. **Real-time out-of-sample** — kills look-ahead bias that infects any historical LLM backtest.  
2. **Reflexivity named explicitly** — as investors adopt AI, patterns erode; live scoring is the honest test.  
3. **Human-readable mechanisms** — agents produce explanations, not just scores (compatible with our categorical / congruence language).

### Timing

Current quarterly scoring period runs through **2026-10-02**. An **SDK** is published for researchers to evaluate agentic systems against the same benchmark.

---

## Related Chicago Booth work (cite carefully)

### Kim, Muhn & Nikolaev — *From Transcripts to Insights* (keep)

- **Title:** From Transcripts to Insights: Uncovering Corporate Risks Using Generative AI  
- **Cite:** BFI WP 2023-132 · [arXiv:2310.17721](https://arxiv.org/abs/2310.17721) · [Harvard CorpGov summary](https://corpgov.law.harvard.edu/2023/11/01/from-transcripts-to-insights-uncovering-corporate-risks-using-generative-ai/)  
- **Result:** GPT-derived firm-level **political / climate / AI risk exposure** from earnings-call transcripts beats dictionary measures at predicting abnormal volatility and some corporate choices.  
- **Use for us:** Anchor citation for the **risk reframe** (S15 disclosure risk) and for the Horner GC / quarterly-pack sleeve.

### Kim, Muhn & Nikolaev — *Financial Statement Analysis with LLMs* (caveat)

- **SSRN:** [4835311](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4835311) · arXiv:2407.17866  
- **Caveat:** Authors **temporarily withdrew** the paper after replication inconsistencies (stated on Nikolaev’s [ongoing research](https://faculty.chicagobooth.edu/valeri-nikolaev/ongoing-research-projects) page).  
- **Rule:** May cite as “related Booth LLM work under review / withdrawn”; **do not use its accuracy or Sharpe numbers in any deck**.

---

## VerityIndex position (committed)

| Action | Decision |
|--------|----------|
| Register for SDK / reproduce baseline | **Yes** — external scorecard for our **text** risk lane |
| Treat as product milestone | **No** |
| Submit a competition agent | **Not until** (a) S00–S15 registry is documented, (b) CAR join returns real `n_with_car`, (c) T011+ registered before peek |
| Our wedge vs their agent | They score **transcript → return explanation**. We add **video delivery risk** (congruence, venue prior, HFAsy, incongruence) that transcript-only agents miss — as a *risk measurement* layer, not a claim of higher R² |

---

## Mapping to our risk factors

| Competition / Booth construct | Our factor |
|-------------------------------|------------|
| Transcript-only return explanation | Text baseline (S15 + claim inventory) |
| Live OOS scoring | Same doctrine as T010 / trials ledger |
| Kim–Muhn–Nikolaev risk exposure | **S15 Disclosure risk exposure** |
| Missing multimodal delivery | S01, S05, S09, S12, S13 |

---

## Next steps

1. Create account / pull SDK from explainingmarkets.ai.  
2. Reproduce published baseline R² band on one quarterly window (document as trial T012+ when ready).  
3. Do **not** advertise competition placement or R² lifts until registered and measured.
