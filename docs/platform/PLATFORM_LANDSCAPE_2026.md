# Platform landscape notes — October 2026

Research snapshot used to place VerityNgn 3.0 in an industry schema. Not a competitive teardown; citations for product decisions.

## Schema patterns we adopt

### 1. Open engine → hosted control plane (LangChain / LangSmith)

- OSS agent stack (Deep Agents / LangChain / LangGraph) + hosted LangSmith for observability, deploy, billing
- Topologies: SaaS, BYOC, customer-operated
- **Map:** VerityNgn L1–L3 OSS → L4 verityindex.com (SaaS first; BYOC later)

Sources: [LangChain OSS overview](https://www.langchain.com/oss-overview), LangSmith marketplace / enterprise topology docs (2026).

### 2. Domain / policy packs (AI governance vendors)

- Credo AI, Holistic AI, Arthur: registry + framework packs (NIST AI RMF, EU AI Act) + evidence trails
- Arthur also ships an open evaluation engine with hosted control
- **Map:** Our “policy packs” are **domain packs** (CRAAP, SIFT, securities disclosure, legal, health, brand) — claim-risk domains, not model-governance GRC. We are adjacent, not a Credo clone.

Sources: buyer guides / NIST AI RMF tool roundups (2026); Holistic AI / Credo / Arthur public positioning.

### 3. Agent-native distribution (MCP + Agent Skills / Plugins)

- Marketplaces (mog, MCPRush, AgentStack) and portable **Agent Plugins 1.0** (`plugin.json` + `skills/` + `mcp.json`)
- **Map:** Phase 1 / 3.1.0 ships a minimal MCP server + skill pack; do not wait on marketplace monetization for the release.

Sources: [agent-plugins.org](https://agent-plugins.org/), MCP marketplace landing pages (2026).

### 4. Decision infrastructure, not more data (Glimmer)

- Glimmer: detect → interpret for *this* company → activate owners (market brain)
- Derrick Horner pointed at Glimmer’s 7-step context ladder (Oct 2026)
- **Map:** RiskFactor / ClearFactor owns steps **4–5** (connect dots; own-context ground truth on a filing calendar). Decline steps 1–2 (crawl/surveil) and real-time step 7 as product scope.

Sources: [itsglimmer.com](https://itsglimmer.com/en); internal `CONTEXT_STACK.md` / Sherlock session 2026-10-08.

## Where we deliberately differ

| Competitor class | They sell | We sell |
|------------------|-----------|---------|
| Fact-check SaaS | Truth score / social feed | Claim-level risk abatement artifacts |
| Filing terminals (AlphaSense et al.) | Search / extract | Same-incident disclosure **actions** |
| Market intel (Glimmer) | Outside signals → team action | Own-record hedge vs admission |
| AI GRC (Credo / Holistic) | Model/agent governance | Media + disclosure claim risk |

## Implications for 3.0.0 collateral

1. Lead with **platform layers + domain packs**, not “we fact-check YouTube.”
2. Disambiguate **two RiskFactor products**.
3. verityindex.com = control plane, not “the closed engine.”
4. ClearFactor = first app; engine sleeve goes Apache.

## Refresh cadence

Re-run entity watch via `~/proj/history/verityngn-oss/ai-monitor/` (7-day loop). Entities: Glimmer, SonicAlpha, AlphaSense, Credo, Holistic, Arthur, LangSmith, MCP/Agent Plugins, SEC Item 1A / 1.05.
