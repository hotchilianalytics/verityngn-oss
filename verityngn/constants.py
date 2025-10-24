VNgnReportPrompt = """# Verity Engine Final Report

## Media Embedding
[![{video_title}](https://img.youtube.com/vi/{video_id}/0.jpg)](https://youtu.be/{video_id})

## Overall Truthfulness Assessment

Based on the evidence gathered, this video is:

| Assessment Level | Explanation |
|-----------------|-------------|
| Highly Likely to be True | The vast majority of claims were verified by strong, reliable evidence |
| Likely to be True | Most claims were verified, with minor discrepancies |
| Mixed Truthfulness | Some claims verified, others false or misleading |
| Likely to be False | Most claims unsupported or contradicted by evidence |
| Highly Likely to be False | Overwhelming majority of claims demonstrably false |
| Unable to Determine | Insufficient evidence to verify or refute key claims |
| Partially True | Some claims verified, main claim true |
| Mostly False | Some claims verified, main claim false |

Selected Assessment: _____________
Detailed Explanation: _____________

## Summary
Provide a concise overview of the main claims and key findings from the verification process. Focus on the most significant evidence and conclusions.

## Claims Breakdown

| Claim | Assessment | Supporting Evidence |
|-------|------------|-------------------|
| Claim 1: Discovery of Ivermectin | True/False/Partial | Include key evidence and sources |
| Claim 2: Properties and Effects | True/False/Partial | Include key evidence and sources |
| Claim 3: Research Findings | True/False/Partial | Include key evidence and sources |

## Evidence Summary

### Primary Sources
List the most credible sources used for verification:
- Scientific papers
- Clinical studies
- Expert testimonies
- Original research data

### Secondary Sources
Additional supporting evidence:
- Medical journals
- Expert analysis
- Fact-check reports
- Verified news coverage

## CRAAP Analysis

| Category | Criteria | Original Analysis | Updated Analysis | Credibility Score |
|----------|----------|-------------------|------------------|------------------|
| Currency | • Publication date<br>• Information timeliness<br>• Recent developments | Describe initial timing assessment | Add new findings | 1-5 |
| Relevance | • Topic relevance<br>• Audience appropriateness<br>• Information depth | Describe initial relevance | Add new findings | 1-5 |
| Authority | • Author credentials<br>• Source reputation<br>• Expert qualifications | Describe initial authority | Add new findings | 1-5 |
| Accuracy | • Evidence support<br>• Peer review<br>• Verification status<br>• Bias check | Describe initial accuracy | Add new findings | 1-5 |
| Purpose | • Information intent<br>• Objectivity<br>• Bias assessment | Describe initial purpose | Add new findings | 1-5 |

## Recommendations

### Further Investigation
List specific areas requiring additional research:
- Gaps in current evidence
- Conflicting information
- Needed expert consultation

### Platform Actions
Recommend appropriate actions:
- Content warnings needed
- Fact-check requirements
- Additional context needed

## Evidence Details

### Source Credibility
| Source | Type | Credibility | Key Findings |
|--------|------|------------|--------------|
| Scientific Paper | Primary | High/Medium/Low | Main conclusions |
| Expert Analysis | Secondary | High/Medium/Low | Key points |

### Verification Timeline
1. Initial Analysis: {current_date}
2. Source Verification: List key verification steps
3. Expert Consultation: Note any expert input
4. Final Assessment: Date of final review

## Technical Notes
- Video ID: {video_id}
- Analysis Date: {current_date}
- Verification Tools: List specific tools used
"""
