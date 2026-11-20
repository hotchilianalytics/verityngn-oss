# Verity Engine OSS 3.0.1: An Open Video-to-Text Truthfulness and Risk Engine

Originally published on Substack at [https://ajjcop.substack.com](https://ajjcop.substack.com) · Release: OSS 3.0.1 · Apache-2.0 License · Engine Tip: 1b2cca8 · Package: `pip install 'verityngn[deep]==3.0.1'`

**Detailed technical release (PDF, checked into the repo):** [Verity Engine OSS 3.0.1 — Official Technical Architecture & Release Paper](https://github.com/hotchilianalytics/verityngn-oss/blob/v3.0.1/docs/releases/v3.0.1/verity-engine-oss-3.0.1-golden-release-paper.pdf)

***

## Part I. Whiteboard Front Page: Architectural Briefing

Modeled after the Emergent Mind research whiteboard architecture format ([Emergent Mind Reference](https://www.emergentmind.com/papers/2611.05217#whiteboard)), this front page synthesizes the core pipeline, visual recognition stack, epistemological taxonomy, domain pack expansion, and platform boundaries.

### Whiteboard Architectural Overview
![Verity Engine Video-to-Text Recognition Pipeline](whiteboard_video_recognition_pipeline.png)

### 1. The Operational Problem: Why Video Truthfulness Requires Multimodal Video-to-Text
Automated fact-checking tools have historically failed when applied to video media because of three fundamental design limitations:
* **Transcript-Only Blindness**: Traditional fact-checkers operate purely on audio speech-to-text. They are completely oblivious to on-screen presentation slides, financial tables, lower-third graphics, scientific diagrams, and silent disclaimer cards flashing across the screen.
* **The Binary Truth Trap**: Standard truth-checkers compress nuanced propositions onto an artificial True/False binary. This collapses empirical facts, complex statistical models, causal arguments, speculative projections, and subjective perspectives into a single moralizing score that analysts cannot defend.
* **Confirmation-Biased Retrieval**: Naive automated search queries search engines using the presenter's exact promotional wording, retrieving the subject's own press releases, affiliate marketing landing pages, and sponsored content as supposed corroboration.

Verity Engine OSS 3.0.1 re-engineers this discipline from first principles. It functions strictly as a video-to-text truthfulness and risk assessment application. It ingests video inputs (YouTube URLs or local MP4 video files), extracts spoken dialogue and visual pixel data in parallel, categorizes claims across a six-kind taxonomy, searches independently for contradictory records, and delivers an audited evidence binder.

### 2. High-Level Ingestion and Verification Flow
The engine executes an automated five-stage verification pipeline:
1. **Multimodal Recognition**: Ingests video frames and audio concurrently via adaptive 1–6 fps scene-aware keyframe sampling, Whisper speech transcription, and Optical Character Recognition (OCR).
2. **Claim Isolation and Typing**: Extracts discrete propositions and routes each into one of six epistemological claim kinds.
3. **Counter-Intelligence Retrieval**: Executes targeted adversarial search queries to surface disconfirming evidence, independent audits, and regulatory enforcement actions while down-weighting promotional press releases.
4. **Genre-Aware Evaluation Routing**: Automatically directs consumer media into the CRAAP framework (Currency, Relevance, Authority, Accuracy, Purpose) and routes analytical or legislative material into the SIFT framework (Stop, Investigate, Find better coverage, Trace).
5. **Grounded Deep Research Synthesis**: Applies a secondary analytical pass that stress-tests every claim against retrieved citations and outputs structured Markdown, HTML, JSON, and PDF dossiers.

### Whiteboard Claim Typology
![The Six Claim Kinds](whiteboard_six_claim_taxonomy.png)

### 3. The Six-Kind Claim Taxonomy
* **Source-Backed Fact**: Concrete empirical, historical, or physical propositions evaluated directly on an empirical True/False veracity ladder against verified public records.
* **Data-Derived Inference**: Quantitative conclusions, mathematical modeling, and statistical extrapolations evaluated for analytical validity and underlying data consistency.
* **Causal / Analytical Argument**: Explanatory theories linking actions to outcomes, evaluated for logical integrity, mechanism validity, and confounding variables.
* **Reasoned Opinion**: Perspective-driven assertions and philosophical arguments evaluated for internal consistency rather than empirical truth.
* **Prediction / Forecast**: Forward-looking probabilistic projections evaluated for residual reliance risk and baseline assumptions rather than binary truthfulness.
* **Unverified Assertion**: Unsupported propositions lacking verifiable evidence, flagged directly with high residual reliance risk for manual human inspection.

### Whiteboard Domain Expansion
![Domain Expansion: Health VSLs to Institutional Diligence](whiteboard_domain_packs_expansion.png)

### 4. Six Expanded Institutional Domain Packs
Moving beyond early versions that focused solely on consumer supplement advertisements and peptide sales, Verity Engine 3.0.1 establishes six dedicated institutional domain packs:
* **Consumer & VSL Sponsor-Readiness**: Evaluates affiliate marketing and sponsor-readiness under CRAAP rubrics (demonstrated on Lipozem with 39 extracted claims).
* **Legislative, Fiscal & Analyst Method Review**: Evaluates public policy hearings and quantitative briefings under SIFT rubrics (demonstrated on the Oregon SB 1507 legislative scorecard with 40 claims, where 45% of claims were pixel-only visual exhibits).
* **Executive & Leadership Interview Diligence**: Evaluates broadcast corporate statements against public regulatory filings and historical disclosures.
* **Legal Deposition & Sworn Spoken Testimony**: Structures testimonial statements into verifiable claims without transcript bloat (demonstrated on Butler Kahn legal testimony with 39 claims).
* **Health Sciences & Contested Clinical Research**: Counter-intelligence diligence targeting lab claims and aggressive bio-marketing (demonstrated on Carney Peptides with 40 claims).
* **Corporate Disclosure & Filing Reconciliation**: Pairs corporate 10-K Item 1A hedged risk factors directly against dated factual admissions.

### Whiteboard Open-Core Architecture
![Open-Core System Architecture](whiteboard_open_core_system.png)

### 5. Open-Core Platform Boundaries
* **Apache-2.0 Open-Source Engine**: Houses the complete video-to-text recognition pipeline, adaptive 1–6 fps OCR, speech transcription, six-kind claim typology, counter-evidence graph, SIFT/CRAAP rubrics, local CLI, and Streamlit workspace.
* **Optional Research Sleeves**: Non-default wheels for specialized computer vision landmarks, audio affect analysis, and executive delivery sensors.
* **Commercial Hosted Platform**: Managed cloud orchestration, team collaboration workspaces, persistent public verification galleries, and enterprise compliance services available on [https://verityindex.com](https://verityindex.com).

***
## Part II. Long-Form Release Essay: Engineering Verity Engine OSS 3.0.1

### 1. Defining the Core Mission: A Dedicated Video-to-Text Truthfulness and Risk App
Verity Engine OSS 3.0.1 is fundamentally an open-source video-to-text truthfulness and risk assessment application. In an information environment saturated with slick video pitches, synthetic media, and corporate broadcasts, knowing whether on-camera claims are true, misleading, or unsubstantiated has become an essential analytical requirement.

For years, automated media verification was trapped between two inadequate extremes:
* Raw speech transcription tools that dump text transcripts without evaluating veracity or risk.
* Superficial fact-checking widgets that slap a simplistic moralizing percentage across an entire production.

Verity Engine breaks through both limitations. Given a video input—either a YouTube URL or a local MP4 file—the engine systematically converts auditory and visual video data into an audited, claim-level ledger. It isolates exactly what was spoken, extracts what was presented visually on screen, searches independently for disconfirming evidence, and calculates the residual reliance risk should a consumer, investor, or legal team act upon those claims.

### 2. How the Engine Actually Recognizes Video
The core engineering differentiator of Verity Engine is its deep multimodal video-to-text recognition architecture. Most existing video analysis pipelines treat video as an audio file with an unnecessary picture attached: they run Whisper or scrape a YouTube caption file, pass the transcript to an LLM, and pretend they have analyzed the video.

That approach misses critical, often decisive, factual evidence:
* **Silent High-Risk Disclaimers**: In deceptive commercial pitches, the speaker discusses lifestyle benefits while high-risk legal disclaimers, unapproved medical warnings, or recurring billing traps flash silently in lower-third text.
* **Complex Data Displays**: In legislative hearings, policy debates, and investor presentations, the foundational numbers—tax rates, budget forecasts, clinical trial results, and revenue waterfalls—live exclusively on projected presentation slides, spreadsheets, and charts.

Verity Engine 3.0.1 solves this through a coordinated three-stage video ingestion pipeline:

1. **Adaptive 1–6 FPS Visual Frame Sampling**: The engine does not sample frames at a dumb, fixed interval. Instead, it utilizes scene-change detection. In static talking-head scenes, it samples at 1 frame per second to conserve processing cycles. The moment a document, slide, financial table, or lower-third graphic appears, frame rate dynamically throttles up to 6 frames per second to capture every visual element and transition.
2. **Optical Character Recognition (OCR) and Visual Entity Extraction**: Every selected keyframe is processed through high-precision OCR to extract visible headers, bullet points, spreadsheet rows, and credential badges. The engine automatically compiles an exhibit map (`exhibit_map.json`) that logs every visual text block with its exact millisecond timestamp.
3. **Synchronized Multimodal Alignment**: The engine performs audio speech-to-text transcription (via Whisper or verified VTT caption tracks) and synchronizes spoken dialogue with visual text blocks along a unified temporal timeline.

The empirical necessity of this multimodal recognition was demonstrated decisively in the primary-10 release benchmark. Across the benchmark suite, 81 verified claims existed exclusively in the video pixels and were never spoken aloud by the presenters. In the review of the Oregon SB 1507 legislative briefing, exactly 18 out of the 40 extracted claims (45%) were captured solely from on-screen legislative tables and slides. Had a standard transcript-only tool been employed, nearly half of the legislative analysis would have been missed entirely.

### 3. The Shift from Health Supplements to Six Institutional Domain Packs
In its early development, Verity Engine was focused primarily on consumer health protection—specifically debunking predatory Video Sales Letters (VSLs) selling dietary supplements, unverified peptide formulations, and aggressive wellness schemes. While that work proved the power of automated claim extraction, it represented only a fraction of what video verification requires.

With release 3.0.1, Verity Engine expands from supplement debunking into six institutional domain packs, adapting its claim extraction, evaluation rubrics, and reporting formats to the distinct epistemological requirements of each domain:

#### Pack 1: Consumer & Video Sales Letter (VSL) Sponsor-Readiness
Designed for advertising agencies, brand safety teams, and compliance officers evaluating commercial endorsements. The engine extracts promotional assertions, evaluates them against the CRAAP framework (Currency, Relevance, Authority, Accuracy, Purpose), and surfaces deceptive blink-and-you-miss-it disclosures. Tested on the Lipozem commercial video, extracting 39 verified claims and exposing silent credential cards.

#### Pack 2: Legislative, Fiscal & Analyst Method Review
Tailored for policy researchers, equity analysts, and civic watchdogs evaluating dense quantitative presentations. It replaces commercial rubrics with the SIFT methodology (Stop, Investigate, Find better coverage, Trace). Evaluated on the Oregon SB 1507 fiscal hearing (an Oregon state legislative tax measure, correcting earlier misattributions to California), isolating 40 complex claims where visual exhibits dominated the evidential record.

#### Pack 3: Executive & CEO Interview Diligence
Built for journalists, investor relations teams, and corporate boards evaluating unscripted broadcast interviews. The engine timestamps executive commitments, product release forecasts, and revenue claims, testing them against historical SEC filings and official press statements. Validated against broadcast leadership interviews across major tech and enterprise organizations.

#### Pack 4: Legal Depositions & Sworn Spoken Testimony
Constructed for litigation counsel, forensic accountants, and expert witnesses. Instead of overwhelming attorneys with a 200-page unstructured deposition transcript, the engine distills spoken testimony into a structured ledger of factual assertions, identifying internal contradictions and corroborating or refuting statements against trial discovery exhibits. Proven on the Butler Kahn legal deposition benchmark with 39 claims extracted.

#### Pack 5: Health Sciences & Contested Clinical Research
Constructed for clinicians, scientific reviewers, and health journalists investigating contested therapeutic claims, peptide marketing, and unapproved medical treatments. The engine actively searches biomedical indices (PubMed, clinical trials registers) to identify negative trials and safety warnings. Evaluated on the Carney Peptides clinical review, isolating 40 complex scientific assertions.

#### Pack 6: Corporate Disclosure & Filing Reconciliation
An enterprise compliance application that extracts forward-looking statements and risk assertions from corporate presentations, placing them directly alongside the organization's formal regulatory disclosures (such as 10-K Item 1A risk factors and 8-K filings) to identify governance discrepancies.

### 4. Empirical Validation: The Primary-10 Verification Battery
To prove operational robustness across diverse recording conditions, Verity Engine 3.0.1 was validated against a standardized battery of 10 diverse, real-world videos. Across the entire 10-video suite, the engine extracted and verified 342 discrete claims with zero pipeline failures.

| Lane | Video Target | Total Claims Extracted | Key Multimodal Recognition Characteristic |
| :--- | :--- | :--- | :--- |
| **Consumer Health** | Lipozem VSL (`tLJC8hkK-ao`) | 39 claims | Isolated unvoiced doctor credentials and fleeting text disclaimers |
| **Civic & Legislative** | Oregon SB 1507 Fiscal Briefing | 40 claims | 18 of 40 claims (45%) derived exclusively from on-screen fiscal slides |
| **Corporate Leadership** | Enterprise CEO CNBC Broadcast | 37 claims | Timestamped geopolitical and enterprise software capability claims |
| **Executive Forum** | Dual-CEO Tech Keynote | 32 claims | Separated corporate vision statements from empirical delivery facts |
| **Semiconductor & AI** | Semiconductor Leadership Broadcast | 16 claims | Verified GPU supply chain and architectural throughput assertions |
| **Global Economics** | Global Leadership Forum Address | 40 claims | Evaluated macro-defense policy assertions against sovereign data |
| **Enterprise Cloud** | Cloud Executive Broadcast | 19 claims | Aligned forward-looking cloud infrastructure projections with earnings |
| **Financial Analysis** | Bloomberg Odd Lots | 40 claims | Evaluated macro-financial hypotheses and market yield claims |
| **Sworn Testimony** | Butler Kahn Deposition | 39 claims | Extracted actionable factual admissions from formal spoken testimony |
| **Biomedical Review** | Carney Peptides Analysis | 40 claims | Counter-searched clinical literature against unregulated peptide claims |

### 5. Architectural Improvements in 3.0.1 and the Future Roadmap
The release of 3.0.1 introduces essential operational safeguards and lays the groundwork for the 3.1 and 3.2 release cycles:

* **Captions CLI Diagnostics (`verityngn captions <url>`)**: Resolves operator ambiguity by verifying whether valid YouTube VTT subtitle tracks have been downloaded, decoupling transcription verification from downstream API timeouts.
* **Automated Visual Risk Sidecars**: The engine now automatically generates `brand_safety_scores.json` and exhibit maps on all full diligence runs, providing automated visual risk metrics for compliance teams.
* **Distribution Hardening**: Explicitly yanked the broken 3.0.0 release candidate and established clean, opt-in dependency sleeves (`verityngn[vision]`, `verityngn[audio]`, `verityngn[predictions]`) so lightweight core installations remain unburdened by heavy scientific dependencies.
* **The 3.1 Engineering Milestone**: Targets physical demonstration verification. While 3.0.1 excels at OCR and slide recognition (capturing 77 of 81 visual claims from on-screen graphics), 3.1 introduces object, prop, and action semantics to detect physical product demonstrations, on-camera product tampering, and temporal splice cuts.
* **The 3.2 Engineering Milestone**: Integrates non-verbal congruence modeling, bringing facial landmark analysis (MediaPipe), vocal strain acoustics (librosa), and delivery conviction sensors into default-on operational status.
