# VerityNgn OSS 3.0.0 — release and legal-use-case brief

Prepared for Alan Coppola / HotChili Analytics, LLC. Verified 27 October 2026.

## Release summary

**VerityNgn OSS 3.0.0 is an Apache-2.0 multimodal claim-risk engine for YouTube and local video. It helps a reviewer identify claims, distinguish facts from inference or prediction, inspect supporting and opposing evidence, and decide what needs further review. It is not a lie detector or an automated legal decision-maker.**

The release highlights analysis tiers; unified captions; Deep Research in OSS; six claim kinds; genre-aware CRAAP/SIFT review; adaptive visual analysis; optional predictions/RiskFactor sensors; and reports for human or downstream review. The MCP/plugin code is included, but its own documentation calls the interface 3.1.0 and the analysis/disclosure tools return commands rather than launching live jobs. [Release](https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0) · [Tagged README](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md) · [Open core](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md) · [MCP](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/agent/MCP.md).

The six kinds are source-backed fact, data-derived inference, causal/analytical, reasoned opinion, prediction, and unverified assertion. Only source-backed facts feed the core true/false histogram; other kinds remain separately reviewable. [Taxonomy](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/verityngn/workflows/claim_kind.py).

## Best initial positioning

**Recommended first GC pilot:** public product or executive-communications review. This matches the video engine without starting with privileged data or promising an unfinished disclosure integration.

**Recommended litigation pilot:** a public deposition or expert-testimony recording. The engine can organize factual assertions and source questions; counsel should verify against the certified transcript and exhibits. The release test battery includes a Butler Kahn deposition with 39 extracted claims, a functional result rather than a legal-accuracy result. [Test matrix](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_TEST_MATRIX_v3.md).

**Strategic GC expansion:** Item 1A risk-factor review against the issuer’s own public record through the separate rfkit / ClearFactor path. The tagged extract documentation still describes a pre-publication gate and a separate companion checkout; the disclosure extra has empty dependencies. Do not sell this as a turnkey capability of a core-only v3.0.0 install. [Companion status](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md) · [Commercial map](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md).

## Legal and general counsel use cases

All rows below are **proposed workflows**, not claims of deployed customer use or guaranteed outcomes. “Core fit” means compatible research ingredients exist—not that a dedicated legal application is complete.

| Workflow / buyer | Input and proposed review | What remains human or additional | Status |
|---|---|---|---|
| Deposition preparation / litigation counsel | Cleared recording; organize assertions, evidence gaps, and follow-up questions | Check certified transcript, exhibits, procedural context, and exact language | Core video path; one public deposition fixture tested |
| Expert-witness preparation / litigation counsel | Separate factual assertions, inference, assumptions, and predictions in expert testimony | Assess qualifications, methodology, admissibility, and cross-examination strategy | Core research fit; no automated expert-admissibility assessment |
| Advertising substantiation / GC or marketing counsel | Review recorded demos, product videos, supplement claims, and webinars | Compare approved substantiation; decide qualification, escalation, or legal clearance | Core video/research fit; legal review required |
| Executive public statements / GC or securities counsel | Separate historical facts from forecasts in interviews or public presentations | Reconcile with approved disclosure, materiality assessments, and counsel’s advice | Core video fit; no automated Reg FD or safe-harbor determination |
| Item 1A disclosure review / GC, securities counsel, disclosure committee | Compare risk wording with own 8-K/public incident record; draft review actions | Companion engine, approved integration, materiality and filing decisions | Phase 1 separate rfkit companion; not turnkey core |
| Investigations / GC, compliance, outside counsel | Research factual claims in public allegations or authorized recordings | Consent, privilege, privacy, evidence preservation, intent/credibility judgments | Core research fit; no forensic authentication or case-management platform |
| Sponsor or influencer review / brand counsel | Examine video/overlays for visual flags and unsupported product promises | Contractual standards, domain policy, clearance, placement decision | Domain-pack/research fit; no live ad-buy integration claimed |
| Regulatory and legislative intelligence / GC or public policy | Analyze public hearings or policy videos and verify claims against primary sources | Current-law research, jurisdiction, legal interpretation and advice | Analyst video fit; not a legal citator |
| Acquisition or vendor public-claims diligence / GC or transaction counsel | Analyze public product/executive videos and produce a list of representations to test | Data-room review, private records, warranties, legal diligence conclusions | Proposed core-based workflow; no data-room integration claimed |
| Counsel / board reporting | Reuse sourced research as input to a human-approved issue memo | Confidentiality, privilege assessment, action ownership, final drafting | Manual workflow; paid packaging/vault is separate scope |

Sources: [Domain packs](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md), [Open core](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md), [Commercial map](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md), [Taxonomy](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/verityngn/workflows/claim_kind.py). For advertising context, see [FTC health-products guidance](https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance). For risk-factor context, see [Regulation S-K Item 105](https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.100/section-229.105). These authorities do not certify the product or its outputs.

## Illustrative legal scenario

A fictional product-webinar claim says: “Our service has never experienced a material outage.” Suggested review questions: What period does “never” cover? What does “material” mean in context? Do approved incident records support the wording? Should the statement be qualified? This is an illustrative workflow—not an extracted result or a claim that core automatically ingests private incident logs.

## Legal safeguards

- Start with public, consented, or expressly cleared material; do not solicit privileged facts in public GitHub issues.
- Local-first is not offline/private inference: map model/search calls, retention, training terms, authorization, access controls, and logs.
- Apply the governing jurisdiction’s ethical rules, applicable privacy/recording requirements, protective orders, and engagement terms.
- Preserve original media, transcripts, exhibits, source copies, versions, run configuration, and reviewer sign-off in your own controlled process.
- Verify source quotations, dates, authority, context, and contrary evidence; let counsel decide legal significance and action.
- Do not equate face, voice, gaze, or affect cues with intent, truthfulness, or guilt.
- Do not claim automatic privilege, admissibility, certified chain of custody, e-discovery completeness, legal-citation validation, or compliance.

ABA Formal Opinion 512 provides relevant guidance on competence, confidentiality, communication, and review. It is not a product approval or a substitute for local rules. [ABA guidance](https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/).

## What the release evidence establishes

The project reports a Primary-10 functional battery PASS with a documented Huang-video substitution. The expansion rows 3–10 contain 263 extracted claims; the deposition row contains 39. These are project-reported execution results, **not independent accuracy, legal reliability, ROI, or adoption evidence**. The deck intentionally omits legacy v2 precision/calibration claims. [Battery](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/BATTERY_RESULTS_v3.md) · [Test matrix](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_TEST_MATRIX_v3.md).

## Launch checks and installation

- GitHub tag `v3.0.0` resolves to `644e5b4b6005b80863490dcfbd77a25ca5edd133`, committed 27 October 2026. Main matched this SHA when checked.
- The GitHub release was updated 27 October 2026 but retains an original `published_at` of 29 August 2026. Use “updated/tagged today,” not an assertion that the release record was first published today.
- The PyPI `https://pypi.org/pypi/verityngn/3.0.0/json` endpoint returned HTTP 404 at verification. GitHub availability is established; PyPI publication was not verified.
- The `disclosure` extra is currently an empty dependency marker. The rfkit extract document retains a pre-publication gate; verify the companion’s public availability separately.
- The MCP interface included in this tree identifies as 3.1.0: `analyze_video` and `review_disclosure` return CLI commands. `get_report` returns local report metadata/top keys, not a full autonomous agent analysis.
- Some broader workspace/control-plane features are target capabilities in the commercial map, not independently verified live deployments.
- No end-to-end engine execution or private customer deployment was performed for this brief.

Documented source path (use a fresh Python 3.12+ environment; API costs may apply):

```bash
git clone --branch v3.0.0 --depth 1 https://github.com/hotchilianalytics/verityngn-oss.git
cd verityngn-oss
pip install -e ".[deep,vision,audio]"
# Configure Gemini/Vertex and search credentials via .env.example.
verityngn analyze --file cleared_clip.mp4 --tier full --modality video --deep
```

## Using the decks

The full editable deck has 16 main slides plus two presenter-QA appendices. Sources and expanded caveats are embedded in native PowerPoint speaker notes. The seven-slide Demolicious cut is designed for approximately 2:45 including a short hand-raise interaction; rehearse it rather than assuming the timing is guaranteed. PDF is provided for easy distribution. The PDF does not include speaker notes; this brief preserves the talk track and release checks in text for reuse or NotebookLM.

### Demolicious script


**Slide 1 / 0:00–0:15**

Raise your hand if a video has ever made you ask, “What supports that claim?” VerityNgn OSS 3.0.0 turns video into claims and evidence you can inspect.

**Slide 2 / 0:15–0:35**

Give it a YouTube link or a cleared local recording. It analyzes words and visuals, classifies claims, researches evidence, and produces a reviewable record. This is a research aid, not an automatic legal conclusion.

**Slide 3 / 0:35–1:00**

Version three puts Deep Research, six claim kinds, flexible analysis tiers, genre-aware review, visual cues, and optional research sensors in the open core. Facts, opinions, and predictions should not all get the same treatment.

**Slide 4 / 1:00–1:30**

For a litigator, start with a public deposition. Organize assertions, inspect sources, and prepare stronger questions. Our release battery includes a deposition with thirty-nine extracted claims. That is functional evidence—not proof of legal correctness, and never a witness honesty score.

**Slide 5 / 1:30–1:55**

For general counsel, start with public product demos or executive statements. What evidence supports the promise? Is this a fact or a forecast? The lawyer remains responsible for the judgment. These are proposed pilots, not a list of existing legal customers.

**Slide 6 / 1:55–2:25**

Which would you actually try? A: deposition preparation. B: public-claims review. C: disclosure review through the separate Phase One companion. Raise your hand. [Pause five seconds; take one brief response.] Tell us your role, a public example, and the output you need.

**Slide 7 / 2:25–2:45**

The engine is Apache-licensed and available on GitHub. Scan for the release. Inspect it, contribute, or bring a public example. Open core. Human judgment. Better questions. And if this is a workflow you want built, vote for us tonight.

## Full-deck presenter notes

### Slide 1

VerityNgn OSS 3.0.0 is our open-source multimodal claim-risk engine. It turns a video into claims and evidence that a person can review. The focus is risk assessment, not a machine declaring who is telling the truth. Today we are inviting users, particularly legal teams, to help choose the next useful workflow.

Release provenance: GitHub retains an original published_at of 2026-08-29. The v3.0.0 tag resolves to 644e5b4b6005b80863490dcfbd77a25ca5edd133, a 2026-10-27 commit; the release was updated 2026-10-27. Do not call this the original publication date.

Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md

### Slide 2

Start with a public YouTube link or a cleared local video. The engine extracts and classifies claims, checks sources and counter-evidence, and produces reports. Auto routing may choose transcript-first analysis; use full video mode when visuals matter. A report is a research aid, not an admissibility or compliance finding.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md

### Slide 3

The release combines flexible analysis tiers, Deep Research, six claim kinds, genre-aware review, adaptive vision, and optional research sensors. CRAAP means Currency, Relevance, Authority, Accuracy, and Purpose. SIFT means Stop, Investigate the source, Find better coverage, and Trace claims to their original context. The optional sensors are not demonstrated deception detectors or trading signals.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.0.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md

### Slide 4

This distinction is especially useful for legal work. A historical assertion, an expert inference, and a forward-looking prediction require different review. The code places only source-backed facts in the core true/false histogram; the other kinds remain separately visible. Classification itself can be wrong and needs review.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/verityngn/workflows/claim_kind.py

### Slide 5

VerityNgn OSS owns the engine and research quality. VerityIndex handles hosted delivery and commercial packaging; the platform map calls several broader features targets, so do not market all of them as deployed. Securities disclosure review is a separate Phase 1 rfkit companion path. The disclosure extra currently has empty dependencies and is not a standalone turnkey reviewer.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/pyproject.toml

### Slide 6

For litigators, the immediate workflow is deposition or expert-testimony preparation. Run a public or approved recording; inspect factual assertions, opinions, evidence, and gaps; then have counsel verify every point against the certified transcript and exhibits. The release battery includes a Butler Kahn deposition with 39 extracted claims. That proves a run completed—not that the report is legally correct. Private exhibit ingestion and cross-case comparison are not established turnkey features.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_TEST_MATRIX_v3.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/BATTERY_RESULTS_v3.md
https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/

### Slide 7

For general counsel, I would begin with public marketing, product, or executive videos. The engine supplies typed claims and research; counsel decides whether substantiation, qualification, escalation, or no change is appropriate. Other pilots include public hearing research and a sourced handoff to outside counsel. These are workflow proposals, not existing legal departments using the system. It is not a general-purpose contract redliner, legal-citation validator, or e-discovery platform.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/verityngn/workflows/claim_kind.py
https://www.ftc.gov/business-guidance/resources/health-products-compliance-guidance

### Slide 8

Securities disclosure is a strategically strong GC use case but must be labeled accurately. The documented companion compares Item 1A language with the issuer’s own public record and proposes review actions. The extract document still lists a pre-publication gate, and the disclosure optional dependency is empty. Therefore this slide describes a Phase 1 companion workflow, not a fully shipped standalone v3 feature. Item 105 supplies the general risk-factor context; no automated conclusion about materiality, scienter, safe harbor, liability, or compliance is implied.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/pyproject.toml
https://www.ecfr.gov/current/title-17/chapter-II/part-229/subpart-229.100/section-229.105

### Slide 9

An investigation team can start with public fraud or reputational claims and build a research list. Original media and evidence handling remain in the team’s established process. Do not infer intent, guilt, or credibility from voice, gaze, affect, hesitation, or facial motion. Do not upload private whistleblower or employee recordings without appropriate authorization, provider review, and legal safeguards. Cross-record review is a human or future-integration step.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md
https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/

### Slide 10

Outside legal, researchers can examine scam or supplement videos, agencies can use brand-safety flags as review inputs, and analysts can explore optional CEO-video sensors. This is not continuous surveillance or automated ad-buy integration, and it does not promise trading alpha. The same core can support different users without claiming every workflow is already a finished application.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.0.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md

### Slide 11

This is a fictional example, not an extracted claim or product screenshot. The engine can help expose a factual assertion in a recording. The reviewer must define scope, locate approved records, test the word material in context, and decide whether qualification is necessary. Do not imply the engine automatically connected to the company’s private incident system.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/verityngn/workflows/claim_kind.py
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md

### Slide 12

These are the project’s reported results, not an independent audit. The Primary-10 fixture set is marked PASS with one documented Huang video swap. The expansion rows three through ten produced 263 claims, including 39 from a deposition. Do not call 263 the total for all ten rows. The battery establishes functional completion and specified gates; it is not a legal ground-truth evaluation, an error-rate guarantee, or a customer outcome study.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/BATTERY_RESULTS_v3.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_TEST_MATRIX_v3.md

### Slide 13

This is a documented source-based quick start, not a sandbox-tested end-to-end install. Use Python 3.12 or later and a fresh environment. Clone the v3.0.0 tag, install the requested extras, and configure credentials per .env.example. The local video command is for a public or cleared file; live Gemini and search services may receive data. At verification, the PyPI verityngn/3.0.0 JSON endpoint returned 404, so this deck intentionally does not advertise pip install verityngn==3.0.0 as verified.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.0.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/pyproject.toml

### Slide 14

ABA Formal Opinion 512 provides relevant guidance about competence, confidentiality, communication, and reviewing AI work. It is guidance under the Model Rules, not a universal deployment certification. Running locally does not eliminate third-party model or search calls. Counsel must apply the governing jurisdiction’s rules and the actual engagement requirements. Attorney participation, a private folder, or the label counsel brief does not automatically establish privilege. No admissibility, chain-of-custody certification, or regulatory-compliance guarantee is made.



Sources (verified 27 October 2026):
https://www.americanbar.org/news/abanews/aba-news-archives/2024/07/aba-issues-first-ethics-guidance-ai-tools/
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.0.md

### Slide 15

Let’s choose with the room. Raise your hand for A, deposition preparation; B, public product or executive claims; or C, a disclosure workflow using the separate companion. Take one short response only. If no one responds, ask who regularly reviews claims in video. Invite people to share their role, a public example, and the output they need. Do not solicit private cases or privileged details in a public issue. C is explicitly a Phase 1 companion workflow.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md

### Slide 16

VerityNgn OSS 3.0.0 is open to inspection and contribution. Scan the code to reach the exact GitHub release. We are looking for users who can bring a public or cleared video, identify the review decision they face, and tell us what evidence or question would help. Our promise is an inspectable research engine—not an automatic legal conclusion.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md

### Slide 17

This appendix corrects several easy overstatements. The MCP server is present but self-identifies as 3.1.0; analyze_video and review_disclosure return CLI commands. get_report returns local report metadata/top keys, not a full autonomous legal analysis. Authenticity adapters include stubs or cues; do not market them as established deepfake forensics. Disclosure needs the companion checkout. The domain pack schema is labeled a target; do not claim every pack already emits a unified production schema.



Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/README.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/OPEN_CORE.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/agent/MCP.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/COMMERCIAL_MAP.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/DOMAIN_PACKS.md

### Slide 18

This is a presenter-only QA appendix. The GitHub release was updated today, and the v3.0.0 tag resolves to a commit dated today. GitHub’s release published_at remains August 29. Do not misrepresent the original publication date. The PyPI version endpoint was unavailable, so use source install until package publishing is confirmed. The rfkit publication gate remains in the tagged documents. Main and tag matched at verification. This deck is based on documentation and code inspection, not a fresh live engine run.

API provenance: https://api.github.com/repos/hotchilianalytics/verityngn-oss/releases/tags/v3.0.0 ; https://api.github.com/repos/hotchilianalytics/verityngn-oss/commits/v3.0.0 ; https://pypi.org/pypi/verityngn/3.0.0/json

Sources (verified 27 October 2026):
https://github.com/hotchilianalytics/verityngn-oss/releases/tag/v3.0.0
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/RELEASE_NOTES_v3.0.0.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/platform/RFKIT_OSS_EXTRACT.md
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/pyproject.toml
https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.0/docs/launch/BATTERY_RESULTS_v3.md
