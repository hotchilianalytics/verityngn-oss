"""
Dict-based data models for VerityNgn reports.
Replaces Pydantic models with simple dict structures and validation functions.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Union
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Utility: Quantum/human mapping for verification result
def map_probabilities_to_verification_result(prob_dist: dict) -> str:
    """Map probability distribution to verification result using enhanced, less conservative thresholds."""
    # Handle None probability distribution
    if prob_dist is None:
        return "UNCERTAIN"
    
    t = prob_dist.get("TRUE", 0.0) * 100
    f = prob_dist.get("FALSE", 0.0) * 100
    u = prob_dist.get("UNCERTAIN", 0.0) * 100
    
    # Enhanced probability mapping with 65% thresholds (from August 22nd analysis)
    false_uncertain_combined = f + u
    true_uncertain_combined = t + u
    
    if t > 70 and f < 10:
        return "HIGHLY_LIKELY_TRUE"
    elif true_uncertain_combined > 65 and f < 35:
        return "LIKELY_TRUE"
    elif false_uncertain_combined > 65 and t < 35:
        return "LIKELY_FALSE"
    elif f > 75:
        return "HIGHLY_LIKELY_FALSE"
    elif t > 50 and f < 20:
        return "LIKELY_TRUE"
    elif f > 45 and t < 25:
        return "LIKELY_FALSE"
    elif t > 40 and f < 35:
        return "LEANING_TRUE"
    elif f > 35 and t < 30:
        return "LEANING_FALSE"
    elif abs(t - f) < 10:
        return "UNCERTAIN"
    elif t > f:
        return "LEANING_TRUE"
    else:
        return "LEANING_FALSE"

class AssessmentLevel(str, Enum):
    HIGHLY_LIKELY_TRUE = "Highly Likely to be True"
    LIKELY_TRUE = "Likely to be True"
    LEANING_TRUE = "Leaning True"
    MIXED = "Mixed Truthfulness"
    UNCERTAIN = "Uncertain"
    LEANING_FALSE = "Leaning False"
    LIKELY_FALSE = "Likely to be False"
    HIGHLY_LIKELY_FALSE = "Highly Likely to be False"
    UNABLE_DETERMINE = "Unable to Determine"

class CredibilityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    MIXED = "Mixed"

# Dict schema functions (replacement for Pydantic models)

def create_media_embed(title: str, video_id: str, thumbnail_url: str, 
                      embed_url: Optional[str] = None, duration: Optional[str] = None) -> Dict[str, Any]:
    """Create a media embed dictionary."""
    return {
        "title": str(title),
        "video_id": str(video_id),
        "thumbnail_url": str(thumbnail_url),
        "embed_url": str(embed_url) if embed_url else None,
        "duration": str(duration) if duration else None
    }

def create_key_finding(finding: str, confidence: str) -> Dict[str, Any]:
    """Create a key finding dictionary."""
    return {
        "finding": str(finding),
        "confidence": str(confidence)
    }

def create_evidence_source(url: str, source_type: str, credibility_level: str,
                          title: Optional[str] = None, snippet: Optional[str] = None,
                          source_name: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """Create an evidence source dictionary."""
    return {
        "url": str(url),
        "source_type": str(source_type),
        "credibility_level": str(credibility_level),
        "title": str(title) if title else None,
        "snippet": str(snippet) if snippet else None,
        "source_name": str(source_name) if source_name else None,
        "text": str(text) if text else None
    }

def create_claim(claim_id: int, claim_text: str, timestamp: str, speaker: str,
                initial_assessment: str, final_assessment: str, probability_distribution: Dict[str, float],
                evidence_sources: Optional[List[Dict[str, Any]]] = None, 
                verification_result: Optional[Union[str, Dict[str, Any]]] = None,
                source_type: str = "video_analysis", global_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a claim dictionary."""
    return {
        "claim_id": int(claim_id),
        "claim_text": str(claim_text),
        "timestamp": str(timestamp),
        "speaker": str(speaker),
        "initial_assessment": str(initial_assessment),
        "final_assessment": str(final_assessment),
        "probability_distribution": dict(probability_distribution) if probability_distribution else {},
        "evidence_sources": list(evidence_sources) if evidence_sources else [],
        "verification_result": verification_result,
        "source_type": str(source_type),
        "global_id": str(global_id) if global_id else None
    }

def create_craap_criteria(currency: str, relevance: str, authority: str, 
                         accuracy: str, purpose: str) -> Dict[str, Any]:
    """Create a CRAAP criteria dictionary."""
    return {
        "currency": str(currency),
        "relevance": str(relevance),
        "authority": str(authority),
        "accuracy": str(accuracy),
        "purpose": str(purpose)
    }

def create_source_credibility(overall_score: float, craap_analysis: Dict[str, Any],
                             reputation_factors: List[str]) -> Dict[str, Any]:
    """Create a source credibility dictionary."""
    return {
        "overall_score": float(overall_score),
        "craap_analysis": dict(craap_analysis),
        "reputation_factors": list(reputation_factors)
    }

def create_quick_summary(truthfulness_overview: str, key_findings: List[Dict[str, Any]],
                        credibility_assessment: str) -> Dict[str, Any]:
    """Create a quick summary dictionary."""
    return {
        "truthfulness_overview": str(truthfulness_overview),
        "key_findings": list(key_findings),
        "credibility_assessment": str(credibility_assessment)
    }

def create_verity_report(media_embed: Dict[str, Any], claims_breakdown: List[Dict[str, Any]],
                        overall_assessment: str, source_credibility: Dict[str, Any],
                        quick_summary: Dict[str, Any], 
                        youtube_counter_intelligence: Optional[List[Dict[str, Any]]] = None,
                        press_release_counter_intelligence: Optional[List[Dict[str, Any]]] = None,
                        analysis_timestamp: Optional[str] = None) -> Dict[str, Any]:
    """Create a verity report dictionary."""
    return {
        "media_embed": dict(media_embed),
        "claims_breakdown": list(claims_breakdown),
        "overall_assessment": str(overall_assessment),
        "source_credibility": dict(source_credibility),
        "quick_summary": dict(quick_summary),
        "youtube_counter_intelligence": list(youtube_counter_intelligence) if youtube_counter_intelligence else [],
        "press_release_counter_intelligence": list(press_release_counter_intelligence) if press_release_counter_intelligence else [],
        "analysis_timestamp": str(analysis_timestamp) if analysis_timestamp else str(datetime.now().isoformat())
    }

# Validation functions (replacement for Pydantic validation)

def validate_evidence_source(source: Dict[str, Any]) -> bool:
    """Validate an evidence source dictionary."""
    required_fields = ["url", "source_type", "credibility_level"]
    return all(field in source and source[field] for field in required_fields)

def validate_claim(claim: Dict[str, Any]) -> bool:
    """Validate a claim dictionary."""
    required_fields = ["claim_id", "claim_text", "timestamp", "speaker", "initial_assessment", "final_assessment"]
    return all(field in claim and claim[field] is not None for field in required_fields)

def validate_verity_report(report: Dict[str, Any]) -> bool:
    """Validate a verity report dictionary."""
    required_fields = ["media_embed", "claims_breakdown", "overall_assessment", "source_credibility", "quick_summary"]
    if not all(field in report for field in required_fields):
        return False
    
    # Validate claims
    for claim in report.get("claims_breakdown", []):
        if not validate_claim(claim):
            return False
    
    return True

# Helper functions for backward compatibility

def dict_to_pydantic_style(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert dict to have similar interface as Pydantic (for gradual migration)."""
    class DictWithMethods:
        def __init__(self, data):
            self.__dict__.update(data)
        
        def model_dump(self):
            return self.__dict__
        
        def dict(self):  # Deprecated Pydantic v1 method
            return self.__dict__
    
    return DictWithMethods(data)

def ensure_dict(obj: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """Ensure object is a dictionary, converting from Pydantic if needed."""
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, dict):
        return obj
    else:
        # Fallback: try to convert to dict
        try:
            return dict(obj)
        except:
            logger.warning(f"Could not convert object to dict: {type(obj)}")
            return {}