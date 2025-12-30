import logging
import json
import os
import sys
import tempfile
from typing import Dict, Any, List, Tuple, Optional, TypedDict
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from langchain_core.output_parsers import JsonOutputParser
from langgraph.graph import StateGraph, END, START
from datetime import datetime
import re
from pydantic import BaseModel
from enum import Enum

# Custom JSON encoder for datetime and other objects
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        if hasattr(o, '__pydantic_serializer__'):
            return o.__pydantic_serializer__()
        return super().default(o)

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from verityngn.models.workflow import InitialAnalysisState
from verityngn.models.report import (
    AssessmentLevel, 
    CredibilityLevel,
    VerityReport,
    KeyFinding,
    Claim,
    SourceCredibility,
    QuickSummary,
    MediaEmbed,
    EvidenceSource
)
from verityngn.config.prompts import FINAL_REPORT_PROMPT
from verityngn.services.storage.unified_storage import unified_storage
from verityngn.config.settings import (
    AGENT_MODEL_NAME, 
    OUTPUTS_DIR, 
    MAX_OUTPUT_TOKENS_2_0_FLASH, 
    MAX_OUTPUT_TOKENS_2_5_FLASH,
    STORAGE_BACKEND,
    StorageBackend
)

from verityngn.services.report.unified_generator import log_report_system_usage
from verityngn.utils.date_utils import get_current_date_context

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create file handler
    log_file = os.path.join(log_dir, 'final_report.log')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Custom JSON encoder for Pydantic models and other types
class CustomJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, Path):
            return str(o)
        if hasattr(o, 'model_dump_json'):
            # Use Pydantic v2's model_dump_json method
            return json.loads(o.model_dump_json())
        if isinstance(o, BaseModel):
            return o.model_dump(mode='json')
        from pydantic import HttpUrl
        if isinstance(o, HttpUrl):
            return str(o)
        return super().default(o)

# Helper function to get values from either dict or object
def get_state_value(state, key, default=None):
    if isinstance(state, dict):
        return state.get(key, default)
    else:
        return getattr(state, key, default)

def get_recommendations_from_agent(video_title: str, claims: List[Claim]) -> List[str]:
    """Generate smart recommendations based on the verified claims."""
    try:
        llm = ChatVertexAI(model_name=AGENT_MODEL_NAME, temperature=0.3, max_output_tokens=MAX_OUTPUT_TOKENS_2_0_FLASH)
        
        prompt = ChatPromptTemplate.from_template("""
        Based on the following video title and verified claims, provide 5-7 specific, actionable recommendations 
        for viewers who may have watched this content. Focus on evidence-based advice.
        
        Video Title: {title}
        
        Claims and Their Verification:
        {claims_summary}
        
        Provide your recommendations as a list of specific, actionable advice points.
        Each recommendation should be evidence-based and directly relate to the claims being made.
        Format your response as a simple list with one recommendation per line.
        """)
        
        claims_summary = ""
        for claim in claims:
            result = claim.verification_result or {}
            claims_summary += f"- Claim: \"{claim.claim_text}\" | Assessment: {result.get('result', 'Unknown')} | Explanation: {result.get('explanation', 'No explanation provided')}\n"
        
        response = llm.invoke(prompt.format(title=video_title, claims_summary=claims_summary))
        
        # Extract and clean recommendations
        recommendations_text = response.content
        recommendations = [line.strip().replace("- ", "") for line in recommendations_text.split("\n") if line.strip()]
        
        return recommendations[:7]  # Limit to 7 recommendations max
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return ["Consult healthcare professionals before acting on health claims in this video",
                "Verify information from reputable sources before making decisions",
                "Be cautious of products claiming rapid or miraculous results"]

def generate_craap_analysis(video_title: str, claims: List[Claim]) -> Dict[str, Tuple[CredibilityLevel, str]]:
    """Generate a comprehensive CRAAP analysis of the content."""
    try:
        llm = ChatVertexAI(model_name=AGENT_MODEL_NAME, temperature=0.2, max_output_tokens=MAX_OUTPUT_TOKENS_2_5_FLASH)
        
        # SHERLOCK FIX: Inject current date context to prevent LLM from treating 2025 sources as "future-dated"
        current_date = get_current_date_context()
        
        prompt = ChatPromptTemplate.from_template(f"""
        IMPORTANT DATE CONTEXT:
        Today's date is {current_date}. When evaluating Currency:
        - Sources from 2025 are current, NOT future-dated
        - The year 2025 is the current year
        - Evaluate recency relative to today ({current_date})
        - Do not penalize sources simply because they have 2025 dates
        
        Perform a CRAAP (Currency, Relevance, Authority, Accuracy, Purpose) analysis on the following video 
        and its claims. Provide a detailed assessment for each criterion.
        
        Video Title: {{title}}
        
        Claims and Their Verification:
        {{claims_summary}}
        
        For each CRAAP criterion, provide:
        1. A rating level (LOW, MEDIUM, or HIGH)
        2. A detailed explanation (2-3 sentences)
        
        Format your response as:
        Currency: RATING_LEVEL
        Currency explanation: Your detailed explanation here.
        
        Relevance: RATING_LEVEL
        Relevance explanation: Your detailed explanation here.
        
        Authority: RATING_LEVEL
        Authority explanation: Your detailed explanation here.
        
        Accuracy: RATING_LEVEL
        Accuracy explanation: Your detailed explanation here.
        
        Purpose: RATING_LEVEL
        Purpose explanation: Your detailed explanation here.
        """)
        
        claims_summary = ""
        for claim in claims:
            result = claim.verification_result or {}
            claims_summary += f"- Claim: \"{claim.claim_text}\" | Assessment: {result.get('result', 'Unknown')} | Explanation: {result.get('explanation', 'No explanation provided')}\n"
        
        response = llm.invoke(prompt.format(title=video_title, claims_summary=claims_summary))
        
        # Parse the CRAAP analysis response
        analysis_text = response.content
        logger.info(f"📊 CRAAP LLM response received for '{video_title}' ({len(analysis_text)} chars)")
        if not analysis_text.strip():
            logger.warning("⚠️ Received empty CRAAP analysis text")
            
        craap_analysis = {}
        
        # Extract ratings and explanations using regex
        criteria = ["Currency", "Relevance", "Authority", "Accuracy", "Purpose"]
        for criterion in criteria:
            rating_match = re.search(rf"{criterion}: (LOW|MEDIUM|HIGH)", analysis_text, re.IGNORECASE)
            explanation_match = re.search(rf"{criterion} explanation: (.*?)(?=\n\n|\n[a-zA-Z]+:|\Z)", analysis_text, re.DOTALL | re.IGNORECASE)
            
            rating = CredibilityLevel.MEDIUM  # Default
            if rating_match:
                rating_text = rating_match.group(1).upper()
                if rating_text == "LOW":
                    rating = CredibilityLevel.LOW
                elif rating_text == "HIGH":
                    rating = CredibilityLevel.HIGH
                logger.info(f"✅ CRAAP {criterion} rating: {rating_text}")
            else:
                logger.warning(f"⚠️ CRAAP {criterion} rating not found in response, using default MEDIUM")
            
            explanation = "Assessment in progress"
            if explanation_match:
                explanation = explanation_match.group(1).strip()
            else:
                logger.warning(f"⚠️ CRAAP {criterion} explanation not found in response")
            
            craap_analysis[criterion.lower()] = (rating, explanation)
        
        logger.info(f"✅ CRAAP analysis generation successful for '{video_title}'")
        return craap_analysis
        
    except Exception as e:
        logger.error(f"❌ Error generating CRAAP analysis: {e}", exc_info=True)
        default_analysis = {
            "currency": (CredibilityLevel.MEDIUM, "Assessment in progress"),
            "relevance": (CredibilityLevel.MEDIUM, "Assessment in progress"),
            "authority": (CredibilityLevel.MEDIUM, "Assessment in progress"),
            "accuracy": (CredibilityLevel.MEDIUM, "Assessment in progress"),
            "purpose": (CredibilityLevel.MEDIUM, "Assessment in progress")
        }
        return default_analysis

def generate_key_findings(claims: List[Claim]) -> List[KeyFinding]:
    """Generate key findings based on the verified claims."""
    try:
        if not claims:
            return []
        
        llm = ChatVertexAI(model_name=AGENT_MODEL_NAME, temperature=0.2, max_output_tokens=MAX_OUTPUT_TOKENS_2_0_FLASH)
        
        # Count claim assessments
        assessment_counts = {}
        for claim in claims:
            result = claim.verification_result or {}
            assessment = result.get("result", "UNKNOWN")
            assessment_counts[assessment] = assessment_counts.get(assessment, 0) + 1
        
        # Prepare summary of claims for the agent
        claims_summary = ""
        for claim in claims:
            result = claim.verification_result or {}
            claims_summary += f"- Claim: \"{claim.claim_text}\" | Assessment: {result.get('result', 'Unknown')} | Explanation: {result.get('explanation', 'No explanation provided')}\n"
        
        prompt = ChatPromptTemplate.from_template("""
        Based on the following verified claims, identify 3-5 key findings or patterns. 
        Focus on the most important insights that would help someone understand the overall credibility of the content.
        
        Claims Assessment Summary:
        {assessment_summary}
        
        Detailed Claims:
        {claims_summary}
        
        For each key finding, provide:
        1. A category/label (e.g., "Scientific Validity", "Source Credibility", "Misleading Claims")
        2. A detailed 1-2 sentence explanation
        
        Format your response as:
        Category 1: Short Label/Title
        Description 1: Detailed explanation
        
        Category 2: Short Label/Title
        Description 2: Detailed explanation
        
        And so on.
        """)
        
        # Prepare assessment summary
        assessment_summary = ""
        for assessment, count in assessment_counts.items():
            assessment_summary += f"{assessment}: {count} claims\n"
        
        response = llm.invoke(prompt.format(
            assessment_summary=assessment_summary,
            claims_summary=claims_summary
        ))
        
        # Parse the findings
        findings_text = response.content
        findings = []
        
        finding_pattern = r"Category \d+: (.*?)\nDescription \d+: (.*?)(?=\n\nCategory|\Z)"
        matches = re.finditer(finding_pattern, findings_text, re.DOTALL)
        
        for match in matches:
            category = match.group(1).strip()
            description = match.group(2).strip()
            
            # Clean up any quotes or prefixes that might be in the data
            if category.startswith("category="):
                category = category.split("=", 1)[1].strip("'\"")
                
            if description.startswith("description="):
                description = description.split("=", 1)[1].strip("'\"")
                
            findings.append(KeyFinding(category=category, description=description))
        
        # If no findings were extracted, create default findings
        if not findings:
            if "HIGHLY_LIKELY_FALSE" in assessment_counts or "LIKELY_FALSE" in assessment_counts:
                findings.append(KeyFinding(
                    category="Misleading Claims",
                    description="The content contains multiple claims that are likely false or misleading, suggesting a pattern of misinformation."
                ))
            if "HIGHLY_LIKELY_TRUE" in assessment_counts or "LIKELY_TRUE" in assessment_counts:
                findings.append(KeyFinding(
                    category="Accurate Information",
                    description="Some claims in the content are supported by credible evidence and appear to be accurate."
                ))
            findings.append(KeyFinding(
                category="Evidence Quality",
                description="The overall quality of evidence presented in the content is questionable, with limited scientific backing for key claims."
            ))
        
        return findings
        
    except Exception as e:
        logger.error(f"Error generating key findings: {e}")
        return [
            KeyFinding(
                category="Verification Issues",
                description="There were technical issues during the verification process. The assessment may be incomplete."
            )
        ]

def generate_sophisticated_assessment(claims: List[Claim]) -> Tuple[AssessmentLevel, str, List[str]]:
    """Generate sophisticated assessment with verdict, key issue, and main concerns."""
    if not claims:
        return AssessmentLevel.MIXED, "No claims to analyze", []
    
    # Count verification results
    result_counts = {}
    total_claims = len(claims)
    main_concerns = []
    
    for claim in claims:
        result = claim.verification_result
        if result:
            verification_result = result.get("result", "UNCERTAIN")
            result_counts[verification_result] = result_counts.get(verification_result, 0) + 1
            
            # Collect explanations for false/concerning claims
            if verification_result in ["FALSE", "HIGHLY_LIKELY_FALSE", "LIKELY_FALSE"]:
                explanation = result.get("explanation", "")
                if explanation and len(explanation) > 50:
                    # Extract key concern from explanation, limit to 300 chars
                    concern = explanation[:300] + "..." if len(explanation) > 300 else explanation
                    main_concerns.append(concern)
    
    # Calculate percentages
    false_count = (result_counts.get("FALSE", 0) + 
                   result_counts.get("HIGHLY_LIKELY_FALSE", 0) + 
                   result_counts.get("LIKELY_FALSE", 0))
    true_count = (result_counts.get("TRUE", 0) + 
                  result_counts.get("HIGHLY_LIKELY_TRUE", 0) + 
                  result_counts.get("LIKELY_TRUE", 0))
    uncertain_count = result_counts.get("UNCERTAIN", 0)
    
    false_percentage = (false_count / total_claims) * 100
    true_percentage = (true_count / total_claims) * 100
    uncertain_percentage = (uncertain_count / total_claims) * 100
    
    # Determine verdict based on distribution (matching Aug 22nd logic)
    if false_percentage >= 60:
        verdict = AssessmentLevel.LIKELY_FALSE
        key_issue = f"This video contains predominantly false or misleading claims. {false_percentage:.1f}% of claims appear false or likely false, while {true_percentage:.1f}% appear true or likely true."
    elif true_percentage >= 60:
        verdict = AssessmentLevel.LIKELY_TRUE
        key_issue = f"This video contains predominantly accurate claims. {true_percentage:.1f}% of claims appear true or likely true, while {false_percentage:.1f}% appear false or likely false."
    elif uncertain_percentage >= 50:
        verdict = AssessmentLevel.MIXED
        key_issue = f"This video contains claims that require additional verification. {uncertain_percentage:.1f}% of claims are uncertain due to insufficient evidence."
    elif false_percentage > true_percentage:
        verdict = AssessmentLevel.LIKELY_FALSE
        key_issue = f"This video contains a mix of claims with varying credibility levels. {false_percentage:.1f}% of claims appear false or likely false, while {true_percentage:.1f}% appear true or likely true."
    else:
        verdict = AssessmentLevel.MIXED
        key_issue = f"This content contains a mix of true and false claims ({false_percentage:.1f}% false, {true_percentage:.1f}% true), requiring careful evaluation."
    
    # Limit main concerns to top 3
    return verdict, key_issue, main_concerns[:3]

def generate_evidence_summary(claims: List[Claim], state: InitialAnalysisState) -> List[EvidenceSource]:
    """
    Generate a summary of evidence for each claim.
    """
    try:
        # Collect all sources from claims
        all_sources = {}
        
        # Debug logs
        logging.info(f"Processing {len(claims)} claims for evidence summary")
        source_counts = 0
        
        for claim in claims:
            result = claim.verification_result or {}
            sources = result.get("sources", [])
            claim_text = claim.claim_text
            claim_assessment = result.get("result", "Unknown")
            
            # Log sources for debugging
            logging.info(f"Claim '{claim_text[:30]}...' has {len(sources)} sources")
            source_counts += len(sources)
            
            # Skip empty sources lists
            if not sources:
                continue
                
            for source in sources:
                source_key = None
                
                # Extract the source key properly based on the source type
                if isinstance(source, str):
                    source_key = source
                elif isinstance(source, dict):
                    source_key = source.get('url', str(hash(str(source))))
                else:
                    # Skip invalid sources
                    logging.warning(f"Skipping invalid source type: {type(source)}")
                    continue
                
                # Debug log source associations
                logging.info(f"Associating source '{source_key[:30]}...' with claim '{claim_text[:30]}...'")
                
                if source_key not in all_sources:
                    # Initialize with basic info
                    source_info = {
                        "claims_count": 1,
                        "claims_supported": [{"text": claim_text, "assessment": claim_assessment}]
                    }
                    
                    if isinstance(source, str):
                        # Process string URL
                        source_url = source
                        source_type = "Web"
                        source_name = "Referenced Source"
                        
                        # Determine source type and credibility based on URL
                        if 'nih.gov' in source_url or 'ncbi.nlm.nih.gov' in source_url or 'pubmed' in source_url:
                            source_type = "Scientific Journal"
                            source_name = "PubMed/NCBI"
                            credibility = "HIGH"
                        elif 'wikipedia.org' in source_url:
                            source_type = "Encyclopedia"
                            source_name = "Wikipedia"
                            credibility = "MEDIUM"
                        elif 'mayoclinic.org' in source_url or 'clevelandclinic.org' in source_url:
                            source_type = "Medical Institution"
                            source_name = "Mayo/Cleveland Clinic"
                            credibility = "HIGH"
                        elif 'fda.gov' in source_url or '.gov' in source_url:
                            source_type = "Government"
                            source_name = "Government Source"
                            credibility = "HIGH"
                        elif 'youtube.com' in source_url or 'youtu.be' in source_url:
                            source_type = "Video"
                            source_name = "YouTube"
                            credibility = "LOW"
                        elif 'scholar.google' in source_url:
                            source_type = "Academic Research"
                            source_name = "Google Scholar"
                            credibility = "HIGH"
                        elif 'news.google' in source_url:
                            source_type = "News Articles"
                            source_name = "Google News"
                            credibility = "MEDIUM"
                        elif '.edu' in source_url:
                            source_type = "Academic"
                            source_name = "Academic Source"
                            credibility = "HIGH"
                        elif 'harvard.edu' in source_url or 'harvard.' in source_url:
                            source_type = "Academic"
                            source_name = "Harvard"
                            credibility = "HIGH"
                        else:
                            # Extract domain name for better display
                            try:
                                from urllib.parse import urlparse
                                domain = urlparse(source_url).netloc
                                # Clean up domain name
                                if domain.startswith('www.'):
                                    domain = domain[4:]
                                source_name = domain.split('.')[0].capitalize()
                            except:
                                source_name = "Web Reference"
                        
                        # Create a more descriptive relevance description
                        description_by_domain = {
                            'mayoclinic': 'Authoritative medical source on safe and effective weight loss',
                            'pubmed': 'Research on turmeric\'s health effects',
                            'ncbi.nlm.nih': 'Scientific research on health topics',
                            'harvard': 'Evidence-based information on effective weight loss methods',
                            'healthline': 'Health information on weight loss and nutrition',
                            'medicalnewstoday': 'Medical news and research on health topics',
                            'verywellhealth': 'Health information from medical reviewers',
                            'youtube': 'Original video content being analyzed',
                            'nih.gov': 'Authoritative government medical research',
                            'cdc.gov': 'Public health information from government source',
                            'who.int': 'Global health guidelines and information',
                            'webmd': 'General medical information for consumers'
                        }
                        
                        relevance_desc = f"Supporting evidence for claim: '{claim_text[:50]}...'"
                        
                        # Check for known domains to provide better descriptions
                        for domain, description in description_by_domain.items():
                            if domain in source_url.lower():
                                relevance_desc = description
                                break
                        
                        source_info.update({
                            "url": source_url,
                            "source_name": source_name,
                            "type": source_type,
                            "credibility": credibility if 'credibility' in locals() else "MEDIUM",
                            "relevance": relevance_desc
                        })
                        
                    elif isinstance(source, dict):
                        # Process dictionary source object
                        source_info.update({
                            "url": source.get('url', ''),
                            "source_name": source.get('source_name', 'Unknown Source'),
                            "type": source.get('source_type', 'Web'),
                            "credibility": source.get('credibility_level', 'MEDIUM'),
                            "relevance": source.get('text', f"Supporting evidence for claim: '{claim_text[:50]}...'")
                        })
                        
                    all_sources[source_key] = source_info
                else:
                    # Update existing source with additional claim info
                    all_sources[source_key]["claims_count"] += 1
                    all_sources[source_key]["claims_supported"].append({"text": claim_text, "assessment": claim_assessment})
        
        # If no sources were found, generate default sources for context
        if not all_sources:
            logging.warning(f"No sources found in {source_counts} total sources across {len(claims)} claims for video {state.video_id}")
            
            # Add some default sources for context
            default_sources = generate_default_sources(state)
            logging.info(f"Added {len(default_sources)} default sources for context")
            
            return default_sources
            
        # Sort sources by number of claims they support
        sorted_sources = sorted(all_sources.values(), key=lambda x: x["claims_count"], reverse=True)
        
        # Limit to top sources and format for display
        top_sources = sorted_sources[:10]  # Reduced from 15 to 10
        formatted_sources = []
        
        for i, source in enumerate(top_sources):
            # Format the relevance field based on claims supported
            if len(source["claims_supported"]) > 1:
                relevance = f"Used in {source['claims_count']} claims - Supports multiple claims including: '{source['claims_supported'][0]['text'][:30]}...'"
            elif source["claims_count"] > 0:
                relevance = f"Used in {source['claims_count']} claim - {source['relevance']}"
            elif "relevance" in source:
                relevance = source["relevance"]
            else:
                relevance = f"Supporting evidence for: '{source['claims_supported'][0]['text'][:50]}...'"
            
            formatted_source = EvidenceSource(
                source_name=source.get("source_name", "Unknown Source"),
                source_type=source.get("type", "Web"),
                url=source.get("url", ""),
                text=relevance,  # Store the formatted relevance with claim counts in the text field
                title=source.get("source_name", "Source")
            )
            formatted_sources.append(formatted_source)
        
        logging.info(f"Generated {len(formatted_sources)} formatted sources")
        return formatted_sources
        
    except Exception as e:
        logger.error(f"Error generating evidence summary: {e}")
        return []

def generate_default_sources(state: InitialAnalysisState) -> List[EvidenceSource]:
    """Generate default evidence sources when no claims are found."""
    logger.warning(f"No evidence sources derived from claims for video {get_state_value(state, 'video_id', 'unknown')}. Adding default sources.")
    return [
        EvidenceSource(
            source_name="Original Video Source",
            source_type="video",
            url=str(get_state_value(state, 'video_url', '')),
            title="Original Video",
            text="The primary video content that was analyzed."
        )
    ]

def generate_overall_assessment(claims: List[Claim]) -> Tuple[AssessmentLevel, str]:
    """Generate an overall assessment based on the verified claims."""
    try:
        if not claims:
            return AssessmentLevel.UNABLE_DETERMINE, "Assessment in progress"
        
        # Count claim assessments
        assessment_counts = {}
        total_claims = len(claims)
        
        for claim in claims:
            result = claim.verification_result or {}
            assessment = result.get("result", "UNABLE_DETERMINE")
            assessment_counts[assessment] = assessment_counts.get(assessment, 0) + 1
        
        # Determine the primary assessment based on majority
        if not assessment_counts:
            primary_assessment = "UNABLE_DETERMINE"
        else:
            primary_assessment = max(assessment_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate percentages
        false_claims = assessment_counts.get("HIGHLY_LIKELY_FALSE", 0) + assessment_counts.get("LIKELY_FALSE", 0)
        false_percentage = (false_claims / total_claims) * 100 if total_claims > 0 else 0
        
        true_claims = assessment_counts.get("HIGHLY_LIKELY_TRUE", 0) + assessment_counts.get("LIKELY_TRUE", 0)
        true_percentage = (true_claims / total_claims) * 100 if total_claims > 0 else 0
        
        # Map string assessment to enum
        assessment_map = {
            "HIGHLY_LIKELY_TRUE": AssessmentLevel.HIGHLY_LIKELY_TRUE,
            "LIKELY_TRUE": AssessmentLevel.LIKELY_TRUE,
            "MIXED": AssessmentLevel.MIXED,
            "LIKELY_FALSE": AssessmentLevel.LIKELY_FALSE,
            "HIGHLY_LIKELY_FALSE": AssessmentLevel.HIGHLY_LIKELY_FALSE,
            "UNABLE_DETERMINE": AssessmentLevel.UNABLE_DETERMINE
        }
        
        enum_assessment = assessment_map.get(primary_assessment, AssessmentLevel.UNABLE_DETERMINE)
        
        # Generate explanation
        if false_percentage >= 70:
            explanation = f"The majority of claims ({false_percentage:.1f}%) in this video are assessed as false or likely false, indicating significant credibility issues."
        elif true_percentage >= 70:
            explanation = f"The majority of claims ({true_percentage:.1f}%) in this video are assessed as true or likely true, suggesting generally reliable information."
        else:
            explanation = f"This video contains a mix of claims with varying credibility levels. {false_percentage:.1f}% of claims appear false or likely false, while {true_percentage:.1f}% appear true or likely true."
        
        return enum_assessment, explanation
        
    except Exception as e:
        logger.error(f"Error generating overall assessment: {e}")
        return AssessmentLevel.UNABLE_DETERMINE, "Assessment in progress due to processing error"

def generate_quick_summary(claims: List[Claim]) -> QuickSummary:
    """Generate a quick summary based on the verified claims."""
    try:
        if not claims:
            return QuickSummary(
                verdict=AssessmentLevel.UNABLE_DETERMINE,
                key_issue="Assessment in progress",
                main_concerns=[]
            )
            
        verdict, explanation = generate_overall_assessment(claims)
        
        # Identify main concerns based on false claims
        main_concerns = []
        for claim in claims:
            result = claim.verification_result or {}
            assessment = result.get("result", "")
            
            if assessment in ["HIGHLY_LIKELY_FALSE", "LIKELY_FALSE"]:
                explanation_text = result.get("explanation", "")
                if explanation_text and len(explanation_text) > 20:  # Ensure it's a meaningful explanation
                    main_concerns.append(explanation_text)
        
        # Limit and deduplicate concerns
        unique_concerns = list(set(main_concerns))
        key_concerns = unique_concerns[:3]  # Limit to top 3 concerns
        
        return QuickSummary(
            verdict=verdict,
            key_issue=explanation,
            main_concerns=key_concerns
        )
        
    except Exception as e:
        logger.error(f"Error generating quick summary: {e}")
        return QuickSummary(
            verdict=AssessmentLevel.UNABLE_DETERMINE,
            key_issue="Assessment in progress",
            main_concerns=[]
        )

async def state_to_report(state: Dict[str, Any]) -> 'VerityReport':
    """Convert workflow state to final report using the unified system."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 [FINAL_REPORT] Starting report generation for video: {state.get('video_id', 'unknown')}")
    logger.info(f"📊 [FINAL_REPORT] State keys: {list(state.keys())}")
    logger.info(f"🔍 [FINAL_REPORT] Claims count: {len(state.get('claims', []))}")
    logger.info(f"📝 [FINAL_REPORT] Initial report present: {'initial_report' in state}")
    
    try:
        # Extract video information
        video_id = state.get("video_id", "unknown")
        video_url = state.get("video_url", "")
        video_info = state.get("video_info", {})
        
        logger.info(f"🎬 [FINAL_REPORT] Processing video: {video_id}")
        
        # Get output directory path
        out_dir_path = state.get("out_dir_path", "")
        if not out_dir_path:
            # Create a default output directory
            import tempfile
            out_dir_path = os.path.join(tempfile.gettempdir(), "verity_outputs", video_id)
            os.makedirs(out_dir_path, exist_ok=True)
            logger.info(f"📁 [FINAL_REPORT] Created default output directory: {out_dir_path}")
        
        logger.info(f"📁 [FINAL_REPORT] Using output directory: {out_dir_path}")
        
        # Check if we have claims to process
        claims = state.get("claims", [])
        if not claims:
            logger.warning(f"⚠️ [FINAL_REPORT] No claims found in state for video {video_id}")
            # Create a minimal report with error information
            minimal_report = {
                "video_id": video_id,
                "video_url": video_url,
                "error": "No claims were extracted during analysis",
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
            
            # Save minimal report
            json_path = os.path.join(out_dir_path, f"{video_id}_final_report.json")
            with open(json_path, 'w') as f:
                json.dump(minimal_report, f, indent=2)
            
            logger.info(f"📄 [FINAL_REPORT] Saved minimal error report to: {json_path}")
            
            return {
                **state,
                "final_report": minimal_report,
                "json_path": json_path,
                "markdown_path": None,
                "html_path": None
            }
        
        logger.info(f"✅ [FINAL_REPORT] Found {len(claims)} claims to process")
        
        # Create the unified report generator
        from verityngn.services.report.unified_generator import UnifiedReportGenerator
        generator = UnifiedReportGenerator(video_id, out_dir_path)
        
        logger.info(f"🔧 [FINAL_REPORT] Created UnifiedReportGenerator for {video_id}")
        
        # Generate the VerityReport object (construct only at the end; state remains dicts)
        from verityngn.models.report import (
            VerityReport,
            MediaEmbed,
            QuickSummary,
            AssessmentLevel,
            KeyFinding,
            Claim,
            EvidenceSource,
        )

        # Build MediaEmbed from available video info with robust fallbacks
        # Coalesce possible keys and sanitize empty strings to valid defaults
        raw_thumb = (
            video_info.get("thumbnail")
            or video_info.get("thumbnail_url")
            or ""
        )
        # Default to standard YouTube thumbnail if missing/empty/invalid
        default_thumb = f"https://img.youtube.com/vi/{video_id}/0.jpg"
        thumbnail_url = raw_thumb if (isinstance(raw_thumb, str) and raw_thumb.startswith("http")) else default_thumb

        raw_video_url = (
            video_url
            or video_info.get("webpage_url")
            or video_info.get("url")
            or ""
        )
        default_video_url = f"https://youtu.be/{video_id}"
        video_url_final = raw_video_url if (isinstance(raw_video_url, str) and raw_video_url.startswith("http")) else default_video_url

        # Fallback: populate description via simple yt-dlp if empty
        description_value = video_info.get("description", "") or ""
        if not description_value:
            try:
                from verityngn.services.video_service import fetch_youtube_info_and_subs_simple
                temp_dir = os.path.join(out_dir_path, "analysis")
                simple = fetch_youtube_info_and_subs_simple(video_url_final, temp_dir, logging.getLogger(__name__))
                info_simple = simple.get("info") or {}
                description_value = info_simple.get("description", "") or ""
                if description_value:
                    video_info["description"] = description_value
            except Exception:
                pass

        media_embed = MediaEmbed(
            title=video_info.get("title", f"Video {video_id}"),
            video_id=video_id,
            thumbnail_url=thumbnail_url,
            video_url=video_url_final,
            description=description_value,
            channel=video_info.get("channel", None),
            upload_date=video_info.get("upload_date", None),
            view_count=video_info.get("view_count", None),
        )

        # Convert claims to typed Claim objects (claim_id must be int; ensure required fields)
        claims_typed = []
        for i, claim in enumerate(claims):
            logger.info(f"📋 [FINAL_REPORT] Processing claim {i+1}: {claim.get('claim_text', '')[:80]}...")
            initial_assessment = (claim.get("verification_result", {}) or {}).get("result", "UNVERIFIED")
            c = Claim(
                claim_id=i,
                claim_text=claim.get("claim_text", ""),
                timestamp=claim.get("timestamp", "00:00"),
                speaker=claim.get("speaker", ""),
                initial_assessment=initial_assessment,
                verification_result=claim.get("verification_result", {}),
                explanation=claim.get("explanation", ""),
                evidence=None,
            )
            claims_typed.append(c)
        logger.info(f"📋 [FINAL_REPORT] Created {len(claims_typed)} typed claims")

        # Generate sophisticated key findings using LLM analysis
        key_findings = generate_key_findings(claims_typed)
        if not key_findings:
            # Fallback to minimal if LLM generation fails
            key_findings = [
                KeyFinding(category="Summary", description=f"Analyzed {len(claims_typed)} claims for video {video_id}.")
            ]

        # Generate sophisticated assessment and verdict
        verdict, overall_msg, main_concerns = generate_sophisticated_assessment(claims_typed)
        quick_summary = QuickSummary(verdict=verdict, key_issue=overall_msg, main_concerns=main_concerns)

        # Evidence summary (best-effort from aggregated evidence)
        evidence_sources: list = []
        try:
            aggregated = state.get("aggregated_evidence", []) or []
            for e in aggregated[:10]:
                if isinstance(e, dict):
                    evidence_sources.append(EvidenceSource(
                        source_name=e.get("source_name", "Referenced Source"),
                        source_type=e.get("source_type", "web"),
                        url=e.get("source_url") or e.get("url"),
                        text=e.get("text", ""),
                        title=e.get("title", None),
                    ))
        except Exception:
            pass
        
        if not evidence_sources:
            # Always include original video as a source
            evidence_sources.append(EvidenceSource(
                source_name="Original Video",
                source_type="Video Source",
                url=f"https://youtu.be/{video_id}",
                text="Primary content source analyzed for claims",
                title=video_info.get("title", f"Video {video_id}"),
            ))

        # Aggregate press release and YouTube CI counts and sources from claims
        pr_count = 0
        yt_count = 0
        press_release_counter_intelligence = []
        youtube_counter_intelligence = []
        
        try:
            for c in claims:
                vr = c.get("verification_result") or {}
                if isinstance(vr, dict):
                    # Aggregate PR sources
                    pr_list = vr.get("pr_sources") or []
                    if isinstance(pr_list, list):
                        pr_count += len(pr_list)
                        for pr_source in pr_list:
                            if isinstance(pr_source, dict) and pr_source.get("url"):
                                # Convert to consistent format for report-level aggregation
                                aggregated_pr = {
                                    'url': pr_source.get('url', ''),
                                    'title': pr_source.get('title', pr_source.get('source_name', 'Press Release')),
                                    'description': pr_source.get('text', ''),
                                    'source_name': pr_source.get('source_name', 'Press Release'),
                                    'source_type': 'press_release_counter_intelligence',
                                    'self_referential': pr_source.get('self_referential', False),
                                    'self_referential_score': pr_source.get('validation_power', 1.0) * 100 if pr_source.get('self_referential') else 0,
                                    'supports_claim': pr_source.get('supports_claim', False),
                                    'claim_text': c.get('claim_text', '')[:100] + '...' if len(c.get('claim_text', '')) > 100 else c.get('claim_text', '')
                                }
                                press_release_counter_intelligence.append(aggregated_pr)
                    
                    # Aggregate YouTube CI sources
                    yt_list = vr.get("youtube_counter_sources") or []
                    if isinstance(yt_list, list):
                        yt_count += len(yt_list)
                        for yt_source in yt_list:
                            if isinstance(yt_source, dict) and yt_source.get("url"):
                                # Convert to consistent format for report-level aggregation  
                                aggregated_yt = {
                                    'video_id': yt_source.get('url', '').split('v=')[-1] if 'youtube.com' in yt_source.get('url', '') else 'unknown',
                                    'title': yt_source.get('title', yt_source.get('source_name', 'YouTube Source')),
                                    'url': yt_source.get('url', ''),
                                    'description': yt_source.get('text', ''),
                                    'source_name': yt_source.get('source_name', 'YouTube Counter-Intelligence'),
                                    'source_type': 'youtube_counter_intelligence'
                                }
                                youtube_counter_intelligence.append(aggregated_yt)
        except Exception as e:
            logger.warning(f"Error aggregating CI sources: {e}")
            pass

        # Add CRAAP analysis if available via generator
        craap: Dict[str, Any] = {}
        try:
            craap = generate_craap_analysis(video_info.get("title", f"Video {video_id}"), claims_typed) or {}
        except Exception as e:
            logger.error(f"Error generating CRAAP analysis: {e}")

        # Generate LLM-based recommendations (not fallback)
        recommendations: List[str] = []
        try:
            logger.info(f"🤖 Generating LLM-based recommendations for video: {video_info.get('title', video_id)}")
            recommendations = get_recommendations_from_agent(
                video_info.get("title", f"Video {video_id}"),
                claims_typed
            )
            logger.info(f"✅ Generated {len(recommendations)} recommendations")
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            # Fallback to generic recommendations only if LLM generation fails
            recommendations = [
                "Verify information from reputable sources before making decisions",
                "Consult experts in the field for professional advice",
                "Be cautious of claims that seem too good to be true",
                "Cross-reference information with multiple independent sources"
            ]

        report = VerityReport(
            media_embed=media_embed,
            title=video_info.get("title", f"Video {video_id}"),
            description=video_info.get("description", ""),
            quick_summary=quick_summary,
            overall_assessment=(verdict, overall_msg),
            key_findings=key_findings,
            claims_breakdown=claims_typed,
            evidence_summary=evidence_sources,
            youtube_counter_intelligence=youtube_counter_intelligence,
            press_release_counter_intelligence=press_release_counter_intelligence,
            press_release_count=pr_count,
            youtube_response_count=yt_count,
            craap_analysis=craap,
            recommendations=recommendations,  # Add LLM-generated recommendations
        )
        logger.info(f"📊 [FINAL_REPORT] Created VerityReport object with {len(claims_typed)} claims")
        
        # Return the model; file generation happens in run_generate_report
        return report
        
    except Exception as e:
        logger.error(f"❌ [FINAL_REPORT] Report generation failed: {e}")
        import traceback
        logger.error(f"📋 [FINAL_REPORT] Traceback: {traceback.format_exc()}")
        raise

# REMOVED: Legacy report generation functions - replaced by unified system
# - write_all_reports: Redundant function only called by unused process_final_report
# - process_final_report: Unused function not called by main workflow
# - build_final_report_workflow: Unused workflow not used by main system
# All report generation now goes through run_generate_report -> generate_unified_reports

async def generate_claims_json_output(state: Dict[str, Any]) -> str:
    """Generate JSON file with detailed claim information for external consumption."""
    logger = logging.getLogger(__name__)
    
    video_id = state.get("video_id", "unknown")
    claims = state.get("claims", [])
    out_dir_path = state.get("out_dir_path", "")
    
    if not out_dir_path:
        logger.warning("No output directory specified for claims JSON")
        return ""
    
    # Create claims JSON with the requested format
    claims_data = []
    for claim in claims:
        claim_entry = {
            "claim_text": claim.get("claim_text", ""),
            "timestamp": claim.get("timestamp", ""),
            "speaker": claim.get("speaker", "Unknown"),
            "source_type": claim.get("source_type", "spoken"),
            "initial_assessment": claim.get("initial_assessment", "Unknown")
        }
        claims_data.append(claim_entry)
    
    # Save claims JSON file
    claims_json_path = os.path.join(out_dir_path, f"{video_id}_claims_detailed.json")
    with open(claims_json_path, 'w', encoding='utf-8') as f:
        json.dump(claims_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📄 Generated claims JSON: {claims_json_path} with {len(claims_data)} claims")
    return claims_json_path

async def create_completion_marker(state: Dict[str, Any], claims_json_path: str) -> str:
    """Create completion marker file with all generated outputs."""
    logger = logging.getLogger(__name__)
    
    video_id = state.get("video_id", "unknown")
    out_dir_path = state.get("out_dir_path", "")
    
    if not out_dir_path:
        logger.warning("No output directory specified for completion marker")
        return ""
    
    # Create completion marker
    completion_data = {
        "video_id": video_id,
        "completion_timestamp": datetime.now().isoformat(),
        "status": "complete",
        "generated_files": {
            "claims_json": os.path.basename(claims_json_path) if claims_json_path else None,
            "final_report_json": f"{video_id}_final_report.json",
            "final_report_markdown": f"{video_id}_final_report.md",
            "final_report_html": f"{video_id}_final_report.html"
        },
        "claims_count": len(state.get("claims", [])),
        "processing_summary": {
            "total_claims_analyzed": len(state.get("claims", [])),
            "verification_completed": True,
            "reports_generated": True
        }
    }
    
    # Save completion marker
    marker_path = os.path.join(out_dir_path, f"{video_id}.complete_markers")
    with open(marker_path, 'w', encoding='utf-8') as f:
        json.dump(completion_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Created completion marker: {marker_path}")
    return marker_path

async def run_generate_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final reports from verified claims using the UNIFIED report generator."""
    import logging
    logger = logging.getLogger(__name__)
    
    video_id = state.get("video_id", "unknown")
    log_report_system_usage("run_generate_report", video_id, "run_generate_report")
    
    logger.info("📄 Generating final reports using UNIFIED template")
    
    try:
        claims = state.get("claims", [])
        aggregated_evidence = state.get("aggregated_evidence", [])
        media_embed = state.get("media_embed", {})
        video_info = state.get("video_info", {})
        out_dir_path = state.get("out_dir_path", "")
        video_id = state.get("video_id", "")
        
        # Convert dict state to proper VerityReport using the GOOD state_to_report function
        from verityngn.models.workflow import InitialAnalysisState
        
        # Ensure video_info is properly populated if missing
        if not video_info and media_embed:
            video_info = {
                "id": video_id,
                "title": media_embed.get("title", f"Video {video_id}"),
                "description": media_embed.get("description", ""),
                "thumbnail": media_embed.get("thumbnail_url", f"https://img.youtube.com/vi/{video_id}/0.jpg"),
                "webpage_url": media_embed.get("video_url", ""),
                "uploader": media_embed.get("uploader", "Unknown"),
                "view_count": media_embed.get("view_count"),
                "upload_date": media_embed.get("upload_date")
            }
        
        # Create a proper InitialAnalysisState from the dict state
        initial_analysis_state = InitialAnalysisState(
            video_id=video_id,
            video_url=state.get("video_url", ""),
            out_dir_path=out_dir_path,
            claims=claims,
            aggregated_evidence=aggregated_evidence,
            media_embed=media_embed,
            transcription=state.get("transcription", ""),
            video_info=video_info
        )
        
        # Use the GOOD report generation system
        logger.info("📊 Using GOOD report generation system (state_to_report)")
        report = await state_to_report(initial_analysis_state)

        # Merge CI-once links (from dict state) into report.youtube_counter_intelligence
        try:
            # Support both legacy 'counter_intel_once' and new 'ci_once' keys
            ci_once = (state.get("counter_intel_once", []) or state.get("ci_once", []) or [])
            if ci_once:
                seen = set(x.get('url','') for x in (report.youtube_counter_intelligence or []))
                merged = list(report.youtube_counter_intelligence or [])
                added = 0
                for item in ci_once:
                    if not isinstance(item, dict):
                        continue
                    url = item.get('url','')
                    if not url or url in seen:
                        continue
                    merged.append({
                        'video_id': url.split('v=')[-1] if ('youtube.com' in url or 'youtu.be' in url) else item.get('video_id','unknown'),
                        'title': item.get('title', item.get('source_name','YouTube Source')),
                        'url': url,
                        'description': item.get('text', item.get('description','')),
                        'source_name': item.get('source_name', ''),
                        'source_type': item.get('source_type', 'youtube_counter_intelligence')
                    })
                    seen.add(url)
                    added += 1
                if added:
                    report.youtube_counter_intelligence = merged
                    logger.info(f"🎯 Injected {added} CI-once links into report.youtube_counter_intelligence")
        except Exception as e:
            logger.warning(f"Failed to merge CI-once links: {e}")
        
        # Use the UNIFIED report generation system
        from verityngn.services.report.unified_generator import UnifiedReportGenerator
        
        logger.info("🚀 Using UNIFIED report generation system")
        generator = UnifiedReportGenerator(video_id, out_dir_path)
        report_paths = await generator.generate_all_reports(report)
        
        # Generate additional JSON output and completion marker
        claims_json_path = await generate_claims_json_output(state)
        completion_marker_path = await create_completion_marker(state, claims_json_path)
        
        logger.info(f"✅ [UNIFIED] Reports generated successfully: {list(report_paths.keys())}")
        logger.info(f"📄 [UNIFIED] Claims JSON: {claims_json_path}")
        logger.info(f"✅ [UNIFIED] Completion marker: {completion_marker_path}")
        
        return {
            **state,
            "final_report": report.model_dump(),
            "json_path": report_paths["json_path"],
            "markdown_path": report_paths["markdown_path"],
            "html_path": report_paths["html_path"],
            "claim_files": report_paths.get("claim_files", []),
            "claims_json_path": claims_json_path,
            "completion_marker_path": completion_marker_path
        }
        
    except Exception as e:
        logger.error(f"❌ [UNIFIED] Report generation failed: {e}")
        raise

async def notify_job_completion(job_id: str, video_id: str, status: str, gcs_path: str) -> None:
    """
    Notify Cloud Run that a video has completed processing via Pub/Sub.
    
    Args:
        job_id: Batch job ID
        video_id: YouTube video ID
        status: Completion status (success/failure)
        gcs_path: GCS path to the completed reports
    """
    try:
        try:
            from google.cloud import pubsub_v1
        except ImportError:
            logger.info("ℹ️ Pub/Sub library not installed, skipping notification.")
            return

        from verityngn.config.settings import PROJECT_ID
        import json
        from datetime import datetime
        
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(PROJECT_ID, 'batch-completions')
        
        message_data = {
            'job_id': job_id,
            'video_id': video_id,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'gcs_path': gcs_path
        }
        
        # Publish message
        future = publisher.publish(
            topic_path,
            json.dumps(message_data).encode('utf-8')
        )
        
        # Wait for publish to complete
        message_id = future.result()
        logger.info(f"📤 Published completion notification for {video_id} (message_id: {message_id})")
        
    except Exception as e:
        # Don't fail the workflow if notification fails
        logger.warning(f"⚠️ Failed to publish completion notification: {e}")


async def run_upload_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Upload reports to cloud storage."""
    import logging
    import glob
    from verityngn.config.settings import ENABLE_LOCAL_GCS_BACKUP, GCS_LOCAL_OUTPUTS_BUCKET
    logger = logging.getLogger(__name__)
    logger.info("☁️ Uploading reports to cloud storage")
    
    try:
        out_dir_path = state.get("out_dir_path", "")
        video_id = state.get("video_id", "")
        uploaded_files = []
        
        # Determine if we should actually upload to cloud
        should_upload = STORAGE_BACKEND == StorageBackend.GCS
        
        logger.info(f"💾 Storage backend detected: {STORAGE_BACKEND} (should_upload={should_upload})")
        
        if not should_upload:
            logger.info(f"ℹ️ {STORAGE_BACKEND.value}-first mode: skipping cloud upload (saving only to local outputs)")
            return {
                **state,
                "gcs_uri": None,
                "gcs_base_uri": None,
                "uploaded_files": []
            }

        # Use unified storage to save files if they aren't already there
        # but for now we keep the existing glob logic but use unified_storage.storage.save_file
        if ENABLE_LOCAL_GCS_BACKUP and out_dir_path:
            logger.info(f"🗂️ Local GCS backup enabled - uploading from {out_dir_path}")
            
            # Find all files in the output directory
            output_files = glob.glob(os.path.join(out_dir_path, "*"))
            
            for file_path in output_files:
                if os.path.isfile(file_path):
                    filename = os.path.basename(file_path)
                    # Use the local outputs bucket for backup
                    gcs_path = f"{video_id}/{filename}"
                    try:
                        gcs_uri = upload_to_gcs(file_path, gcs_path, bucket_name=GCS_LOCAL_OUTPUTS_BUCKET)
                        uploaded_files.append(f"Local: {filename} -> {gcs_uri}")
                        logger.info(f"📤 Uploaded to local backup: {filename}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to upload {filename} to local backup: {e}")
        
        # Upload JSON report to GCS (main bucket)
        json_path = state.get("json_path", "")
        if json_path and os.path.exists(json_path):
            gcs_path = f"reports/{video_id}/{os.path.basename(json_path)}"
            gcs_uri = upload_to_gcs(json_path, gcs_path)
            uploaded_files.append(f"JSON: {gcs_uri}")
        else:
            gcs_uri = None
        
        # Upload HTML report to GCS
        html_path = state.get("html_path", "")
        if html_path and os.path.exists(html_path):
            gcs_path = f"reports/{video_id}/{os.path.basename(html_path)}"
            html_gcs_uri = upload_to_gcs(html_path, gcs_path)
            uploaded_files.append(f"HTML: {html_gcs_uri}")
        
        # Upload Markdown report to GCS
        markdown_path = state.get("markdown_path", "")
        if markdown_path and os.path.exists(markdown_path):
            gcs_path = f"reports/{video_id}/{os.path.basename(markdown_path)}"
            md_gcs_uri = upload_to_gcs(markdown_path, gcs_path)
            uploaded_files.append(f"MD: {md_gcs_uri}")
        
        # Upload all claim source files (both .md and .html)
        if out_dir_path:
            claim_files = glob.glob(os.path.join(out_dir_path, f"{video_id}_claim_*_sources.*"))
            for claim_file in claim_files:
                if os.path.exists(claim_file):
                    gcs_path = f"reports/{video_id}/{os.path.basename(claim_file)}"
                    claim_gcs_uri = upload_to_gcs(claim_file, gcs_path)
                    uploaded_files.append(f"Claim: {os.path.basename(claim_file)}")
        
        # 🚀 SHERLOCK FIX: Upload counter intelligence files (YouTube and Press Release)
        if out_dir_path:
            # Upload YouTube counter intelligence files
            youtube_ci_files = glob.glob(os.path.join(out_dir_path, f"{video_id}_youtube_counter_intel.*"))
            logger.info(f"🔍 [SHERLOCK] Found {len(youtube_ci_files)} YouTube counter-intelligence files to upload")
            for ci_file in youtube_ci_files:
                if os.path.exists(ci_file):
                    gcs_path = f"reports/{video_id}/{os.path.basename(ci_file)}"
                    ci_gcs_uri = upload_to_gcs(ci_file, gcs_path)
                    uploaded_files.append(f"YouTube CI: {os.path.basename(ci_file)}")
                    logger.info(f"✅ [SHERLOCK] Uploaded YouTube CI file: {os.path.basename(ci_file)} -> {ci_gcs_uri}")
            
            # Upload Press Release counter intelligence files  
            pr_ci_files = glob.glob(os.path.join(out_dir_path, f"{video_id}_press_release_counter_intel.*"))
            logger.info(f"🔍 [SHERLOCK] Found {len(pr_ci_files)} Press Release counter-intelligence files to upload")
            for ci_file in pr_ci_files:
                if os.path.exists(ci_file):
                    gcs_path = f"reports/{video_id}/{os.path.basename(ci_file)}"
                    ci_gcs_uri = upload_to_gcs(ci_file, gcs_path)
                    uploaded_files.append(f"Press Release CI: {os.path.basename(ci_file)}")
                    logger.info(f"✅ [SHERLOCK] Uploaded Press Release CI file: {os.path.basename(ci_file)} -> {ci_gcs_uri}")
        
        # Upload workflow log file to GCS for debugging
        log_path = state.get("log_path", "")
        if not log_path and out_dir_path:
            # Fallback: try to find log file in output directory
            log_path = os.path.join(out_dir_path, f"{video_id}_workflow.log")
        if log_path and os.path.exists(log_path):
            gcs_path = f"reports/{video_id}/{os.path.basename(log_path)}"
            log_gcs_uri = upload_to_gcs(log_path, gcs_path)
            uploaded_files.append(f"LOG: {log_gcs_uri}")
            logger.info(f"📝 Uploaded workflow log: {os.path.basename(log_path)} -> {log_gcs_uri}")
        
        logger.info(f"✅ Uploaded {len(uploaded_files)} files to GCS:")
        for uploaded_file in uploaded_files:
            logger.info(f"  📄 {uploaded_file}")
        
        # Notify batch job completion if BATCH_JOB_ID is set
        batch_job_id = os.environ.get('BATCH_JOB_ID')
        if batch_job_id:
            # Determine correct GCS path based on storage backend
            from verityngn.config.settings import GCS_BUCKET_NAME
            if USE_TIMESTAMPED_STORAGE:
                # Using timestamped storage - get path from state
                timestamped_dir = state.get("timestamped_dir", "")
                if timestamped_dir:
                    gcs_path = f"gs://{GCS_BUCKET_NAME}/vngn_reports/{video_id}/"
                else:
                    gcs_path = f"gs://{GCS_BUCKET_NAME}/reports/{video_id}/"
            else:
                # Legacy upload system
                gcs_path = f"gs://{GCS_LOCAL_OUTPUTS_BUCKET if ENABLE_LOCAL_GCS_BACKUP else GCS_BUCKET_NAME}/reports/{video_id}/"
            
            logger.info(f"📤 Sending Pub/Sub notification for job {batch_job_id}")
            await notify_job_completion(
                job_id=batch_job_id,
                video_id=video_id,
                status='success',
                gcs_path=gcs_path
            )
        
        return {
            **state,
            "gcs_uri": gcs_uri,
            "gcs_base_uri": gcs_uri,
            "uploaded_files": uploaded_files
        }
        
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        
        # Notify batch job failure if BATCH_JOB_ID is set
        batch_job_id = os.environ.get('BATCH_JOB_ID')
        if batch_job_id:
            video_id = state.get("video_id", "unknown")
            await notify_job_completion(
                job_id=batch_job_id,
                video_id=video_id,
                status='failure',
                gcs_path=''
            )
        
        # Don't fail the whole workflow for upload issues
        return {
            **state,
            "gcs_uri": None,
            "gcs_base_uri": None,
            "uploaded_files": []
        }

def create_final_report(
    claims: List[Dict[str, Any]], 
    evidence: List[Dict[str, Any]], 
    media_embed: Dict[str, Any],
    video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """Create the final verification report."""
    from datetime import datetime
    
    # Calculate overall assessment
    total_claims = len(claims)
    if total_claims == 0:
        overall_verdict = "Unable to Determine"
        key_issue = "No verifiable claims were identified in this content."
    else:
        # Count claim results
        true_count = sum(1 for claim in claims if claim.get("verification_result", {}).get("result") in ["TRUE", "HIGHLY_LIKELY_TRUE", "LIKELY_TRUE"])
        false_count = sum(1 for claim in claims if claim.get("verification_result", {}).get("result") in ["FALSE", "HIGHLY_LIKELY_FALSE", "LIKELY_FALSE"])
        uncertain_count = sum(1 for claim in claims if claim.get("verification_result", {}).get("result") in ["UNCERTAIN", "UNABLE_DETERMINE"])
        
        false_percentage = (false_count / total_claims) * 100
        true_percentage = (true_count / total_claims) * 100
        
        # Use correct AssessmentLevel enum values
        if false_percentage >= 70:
            overall_verdict = "Highly Likely to be False"
            key_issue = f"The majority of claims ({false_percentage:.1f}%) in this content are assessed as false or likely false, indicating significant credibility issues."
        elif false_percentage >= 50:
            overall_verdict = "Likely to be False"
            key_issue = f"A significant portion ({false_percentage:.1f}%) of claims in this content are assessed as false, raising credibility concerns."
        elif true_percentage >= 70:
            overall_verdict = "Highly Likely to be True"
            key_issue = f"The majority of claims ({true_percentage:.1f}%) in this content are assessed as true or likely true, indicating high credibility."
        elif true_percentage >= 50:
            overall_verdict = "Likely to be True"
            key_issue = f"Most claims ({true_percentage:.1f}%) in this content appear to be accurate and reliable."
        elif false_percentage > 20 or true_percentage > 20:
            overall_verdict = "Mixed Truthfulness"
            key_issue = f"This content contains a mix of true and false claims ({false_percentage:.1f}% false, {true_percentage:.1f}% true), requiring careful evaluation."
        else:
            overall_verdict = "Unable to Determine"
            key_issue = f"Most claims require additional verification due to insufficient evidence ({uncertain_count} uncertain claims)."
    
    # Analyze claim patterns for key findings
    key_findings = analyze_claim_patterns(claims)
    
    # Get main concerns from false claims
    main_concerns = []
    for claim in claims:
        verification_result = claim.get("verification_result", {})
        if verification_result.get("result") in ["FALSE", "HIGHLY_LIKELY_FALSE", "LIKELY_FALSE", "UNCERTAIN", "ERROR"]:
            explanation = verification_result.get("explanation", "")
            if explanation and len(explanation) > 20:
                main_concerns.append(explanation[:200] + "..." if len(explanation) > 200 else explanation)
    
    # Create final report structure
    final_report = {
        "media_embed": media_embed,
        "description": video_info.get("description", ""),
        "title": media_embed.get("title", ""),
        "quick_summary": {
            "verdict": overall_verdict,
            "key_issue": key_issue,
            "main_concerns": main_concerns[:3],  # Top 3 concerns
            "analysis_date": datetime.now().isoformat()
        },
        "overall_assessment": [overall_verdict, key_issue],
        "key_findings": key_findings,
        "claims_breakdown": [],
        "evidence_summary": evidence[:10] if evidence else [],  # Add evidence summary
        "secondary_sources": [],  # Required field
        "craap_analysis": {  # Required field with default values
            "currency": ["Medium", "Assessment in progress"],
            "relevance": ["Medium", "Assessment in progress"], 
            "authority": ["Medium", "Assessment in progress"],
            "accuracy": ["Medium", "Assessment in progress"],
            "purpose": ["Medium", "Assessment in progress"]
        },
        "recommendations": [  # Required field
            "Verify information from reputable sources before making decisions",
            "Consult experts in the field for professional advice",
            "Be cautious of claims that seem too good to be true"
        ],
        "evidence_details": []  # Required field
    }
    
    # Add detailed claims breakdown
    for i, claim in enumerate(claims):
        verification_result = claim.get("verification_result", {})
        claim_evidence = claim.get("evidence", [])
        
        claim_breakdown = {
            "claim_id": claim.get("claim_id", i + 1),
            "claim_text": claim.get("claim_text", ""),
            "timestamp": claim.get("timestamp", "00:00"),
            "speaker": claim.get("speaker", "Speaker"),
            "initial_assessment": claim.get("initial_assessment", ""),
            "verification_result": verification_result,
            "explanation": verification_result.get("explanation", ""),
            "evidence": claim_evidence[:10]  # Limit evidence items
        }
        
        final_report["claims_breakdown"].append(claim_breakdown)
    
    return final_report

def analyze_claim_patterns(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze patterns in claims to identify key findings."""
    patterns = []
    
    false_claims = [c for c in claims if c.get("verification_result", {}).get("result") == "FALSE"]
    uncertain_claims = [c for c in claims if c.get("verification_result", {}).get("result") == "UNCERTAIN"]
    
    if len(false_claims) > 0:
        patterns.append({
            "category": "Unverified Claims and Lack of Evidence",
            "description": f"A significant number of claims ({len(false_claims)}) lack sufficient supporting evidence or are demonstrably false, indicating potential issues with factual accuracy."
        })
    
    if len(uncertain_claims) > 0:
        patterns.append({
            "category": "Uncertain or Ambiguous Claims", 
            "description": f"Several claims ({len(uncertain_claims)}) require additional verification due to insufficient or conflicting evidence."
        })
    
    # Add more pattern analysis as needed
    overstated_claims = [c for c in claims if "everything" in c.get("claim_text", "").lower() or "all" in c.get("claim_text", "").lower()]
    if len(overstated_claims) > 0:
        patterns.append({
            "category": "Overstatement and Exaggeration",
            "description": "Several claims use hyperbolic language which may be demonstrably false or highly unlikely, suggesting a tendency to exaggerate for effect."
        })
    
    return patterns[:4]  # Limit to top 4 patterns

# Add system tracking - Updated to reflect consolidation
REPORT_SYSTEMS = {
    "run_generate_report": "✅ ACTIVE: Main workflow report generation (uses unified system)",
    "write_all_reports": "❌ REMOVED: Legacy report generation (redundant - replaced by unified system)", 
    "vi_agent_full": "⚠️ ISOLATED: Old agentic system (separate workflow - no claim source files)",
    "test_report": "✅ ACTIVE: Test report generation (uses unified system)"
}
