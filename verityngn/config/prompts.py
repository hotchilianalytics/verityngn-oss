"""
Prompts used throughout the VerityNgn application.
"""

# Report template prompt
REPORT_TEMPLATE = """# Verity Engine Final Report

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

# Initial analysis prompt
INITIAL_ANALYSIS_PROMPT = """
You are a fact-checking expert analyzing a video. Your task is to:
0. Analyze the actual video deeply for information in all modes (video, audio , OCR, tables), so that you can provide a comprehensive analysis for truth and fact checking.
1. Identify the main claims made in the video, annotated with a timestamp if possible
2. Assess the overall credibility of the content, and add in external results of reviews or collateral external to the video.
3. Provide an initial assessment of truthfulness, akong with any external info (e.g. Rick Astley's video is also an internet meme called RickRolling
4. Provide a list of claims that you believe are false or misleading, and provide a timestamp for each claim.
5. Look externally for the meta information on the reputation of the maker of the video, and take that into account when listing the claims.

Watch the video carefully and provide a structured analysis, including timestamps where that makes sense.
"""

# Claim verification prompt
CLAIM_VERIFICATION_PROMPT = """
You are verifying the following claim from a video:

Claim: {claim_text}

Your task is to:
1. Search for evidence that supports or refutes this claim, using the claim and a small 100 character or less context for the claim in your search
2. Evaluate the credibility of the sources
3. Provide a verification result with explanation

Be thorough and objective in your analysis.
"""

# Final report generation prompt
FINAL_REPORT_PROMPT = """
You are generating a final verification report for a video. Your task is to create a comprehensive JSON report that follows this exact structure:

{
    "media_embed": {
        "title": "Video Title",
        "video_id": "video_id",
        "thumbnail_url": "https://img.youtube.com/vi/video_id/0.jpg",
        "video_url": "https://youtu.be/video_id"
    },
    "quick_summary": {
        "verdict": "Assessment Level",
        "key_issue": "Main issue identified",
        "main_concerns": ["Concern 1", "Concern 2"]
    },
    "title": "Video Title",
    "overall_assessment": ["Assessment Level", "Detailed explanation"],
    "key_findings": [
        {"category": "Category 1", "description": "Description 1"},
        {"category": "Category 2", "description": "Description 2"}
    ],
    "claims_breakdown": [
        {"claim_text": "Claim 1", "verification_result": "Result 1", "explanation": "Explanation 1"},
        {"claim_text": "Claim 2", "verification_result": "Result 2", "explanation": "Explanation 2"}
    ],
    "evidence_summary": [
        {"source_name": "Source 1", "source_type": "Type 1", "text": "Evidence 1"},
        {"source_name": "Source 2", "source_type": "Type 2", "text": "Evidence 2"}
    ],
    "secondary_sources": ["Source 1", "Source 2"],
    "craap_analysis": {
        "currency": ["Level", "Explanation"],
        "relevance": ["Level", "Explanation"],
        "authority": ["Level", "Explanation"],
        "accuracy": ["Level", "Explanation"],
        "purpose": ["Level", "Explanation"]
    },
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "evidence_details": [
        {"source_name": "Source 1", "credibility_level": "Level", "justification": "Justification 1"},
        {"source_name": "Source 2", "credibility_level": "Level", "justification": "Justification 2"}
    ]
}

Requirements:
1. Your response must be valid JSON that matches this structure exactly
2. Do not include any text before or after the JSON object
3. Do not include markdown code blocks or any other formatting
4. All arrays must have at least one item
5. All required fields must be present
6. Use the provided AssessmentLevel and CredibilityLevel enums for their respective fields
7. Include specific evidence and sources from the input data
8. Provide detailed explanations for each section
""" 