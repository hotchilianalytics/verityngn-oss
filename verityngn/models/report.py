from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any
from pydantic import BaseModel, Field, HttpUrl
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
    MIXED = "Mixed Truthfulness"
    LIKELY_FALSE = "Likely to be False"
    HIGHLY_LIKELY_FALSE = "Highly Likely to be False"
    UNABLE_DETERMINE = "Unable to Determine"

class CredibilityLevel(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    MIXED = "Mixed"

class MediaEmbed(BaseModel):
    """Embedding details for the media content."""
    title: str = Field(..., description="Title of the media content")
    video_id: str = Field(..., description="Unique ID of the video")
    thumbnail_url: HttpUrl = Field(..., description="URL of the video thumbnail")
    video_url: HttpUrl = Field(..., description="URL of the video")
    description: str = Field(..., description="Description of the video")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of video processing or analysis")
    channel: Optional[str] = Field(None, description="Name of the channel")
    channel_follower_count: Optional[int] = Field(None, description="Number of followers/subscribers")
    comment_count: Optional[int] = Field(None, description="Number of comments")
    upload_date: Optional[str] = Field(None, description="Date the video was uploaded (YYYYMMDD)")
    uploader: Optional[str] = Field(None, description="Name of the uploader")
    uploader_id: Optional[str] = Field(None, description="ID of the uploader")
    uploader_url: Optional[HttpUrl] = Field(None, description="URL of the uploader's channel")
    view_count: Optional[int] = Field(None, description="Number of views")

    def to_markdown(self) -> str:
        if not self.thumbnail_url:
            self.thumbnail_url = f"https://img.youtube.com/vi/{self.video_id}/0.jpg"
        if not self.video_url:
            self.video_url = f"https://youtu.be/{self.video_id}"
        
        # Use HTML div structure for better display, including title and description
        return f"""<div class="video-embed">
    <h2>{self.title}</h2>
    <a href="{self.video_url}" target="_blank">
        <img src="{self.thumbnail_url}" alt="{self.title}" width="560">
    </a>
    <div class="video-description">
        <h3>YouTube Video Description:</h3>
        <p>{self.description}</p>
    </div>
</div>"""

class KeyFinding(BaseModel):
    category: str
    description: str

# Define EvidenceSource before Claim uses it
class EvidenceSource(BaseModel):
    source_name: str
    source_type: str
    url: Optional[str]
    text: str
    title: Optional[str]

class Claim(BaseModel):
    claim_id: int
    claim_text: str
    timestamp: str
    speaker: str
    initial_assessment: str
    verification_result: Optional[Dict[str, Any]] = None
    explanation: str = ""
    evidence: Optional[List[EvidenceSource]] = None
    probability_distribution: Optional[Dict[str, float]] = None
    pr_sources: Optional[List[EvidenceSource]] = None
    youtube_counter_sources: Optional[List[EvidenceSource]] = None

    def get_verification_result(self):
        if hasattr(self, 'probability_distribution') and self.probability_distribution:
            return map_probabilities_to_verification_result(self.probability_distribution)
        # fallback to stored result
        if hasattr(self, 'verification_result') and isinstance(self.verification_result, dict):
            return self.verification_result.get('result', 'UNCERTAIN')
        return 'UNCERTAIN'

    def to_markdown(self) -> str:
        """Convert the claim to markdown format."""
        # Format claim column with centered subfields
        claim_cell = [
            f"**Claim {self.claim_id}**",
            "",
            "<div align='center'>",
            f"**Timestamp:** {self.timestamp}",
            f"**Speaker:** {self.speaker}",
            f"**Initial Assessment:** {self.initial_assessment}",
            "</div>",
            "",
            self.claim_text
        ]

        # Format verification result with probability distribution
        verification_result = self.get_verification_result()
        result = verification_result.get("result", "Unknown")
        prob_dist = ""
        if verification_result.get("probability_distribution"):
            prob_dist = "\n\n**Probability Distribution:**\n"
            for outcome, prob in verification_result["probability_distribution"].items():
                prob_dist += f"- {outcome}: {prob*100:.1f}%\n"

        result_cell = f"{result}{prob_dist}"

        return f"|{'<br>'.join(claim_cell)}|{result_cell}|{self.explanation}|"

    def to_json(self):
        """Convert the claim to a JSON dictionary."""
        data = super().dict()
        verification_result = self.get_verification_result()
        data['verification_result'] = verification_result
        return data

class CRAAPCriteria(BaseModel):
    currency: tuple[CredibilityLevel, str]
    relevance: tuple[CredibilityLevel, str]
    authority: tuple[CredibilityLevel, str]
    accuracy: tuple[CredibilityLevel, str]
    purpose: tuple[CredibilityLevel, str]

class SourceCredibility(BaseModel):
    source_name: str
    credibility_level: CredibilityLevel
    justification: str

class QuickSummary(BaseModel):
    verdict: AssessmentLevel
    key_issue: str
    main_concerns: List[str]
    analysis_date: datetime = datetime.now()

class VerityReport(BaseModel):
    media_embed: MediaEmbed
    title: str
    description: str = ""
    quick_summary: QuickSummary
    overall_assessment: Tuple[AssessmentLevel, str]
    key_findings: List[KeyFinding]
    claims_breakdown: List[Claim]
    evidence_summary: List[EvidenceSource]
    secondary_sources: List[EvidenceSource] = []
    craap_analysis: Dict[str, Any] = {}
    recommendations: List[str] = []
    evidence_details: List[Dict[str, Any]] = []
    press_release_count: int = 0
    youtube_response_count: int = 0
    metadata: Optional[Dict[str, Any]] = {}
    
    # NEW: Counter-Intelligence Analysis fields
    youtube_counter_intelligence: List[Dict[str, Any]] = []
    press_release_counter_intelligence: List[Dict[str, Any]] = []

    def dict(self, **kwargs):
        """Convert the report to a dictionary with serializable values."""
        data = super().dict(**kwargs)
        
        # Convert AssessmentLevel to string
        if isinstance(data.get('overall_assessment'), tuple):
            level, explanation = data['overall_assessment']
            data['overall_assessment'] = [str(level), explanation]
            
        # Convert CRAAP analysis tuples to lists
        if isinstance(data.get('craap_analysis'), dict):
            data['craap_analysis'] = {
                k: [str(v[0]), v[1]] for k, v in data['craap_analysis'].items()
            }
            
        return data

    def _get_craap_explanation(self, criterion: str) -> str:
        """Get the explanation for a CRAAP criterion.
        
        Args:
            criterion (str): The CRAAP criterion (currency, relevance, authority, accuracy, purpose)
            
        Returns:
            str: The explanation for the criterion
        """
        if criterion in self.craap_analysis:
            return self.craap_analysis[criterion][1]
        return "No explanation available"

    def _get_craap_level(self, criterion: str) -> CredibilityLevel:
        """Get the credibility level for a CRAAP criterion.
        
        Args:
            criterion (str): The CRAAP criterion (currency, relevance, authority, accuracy, purpose)
            
        Returns:
            CredibilityLevel: The credibility level for the criterion
        """
        if criterion in self.craap_analysis:
            return self.craap_analysis[criterion][0]
        return CredibilityLevel.LOW

    def _ensure_web_sources(self):
        """Ensure that the evidence summary has at least one web source."""
        # Check if we already have web sources
        has_web_source = False
        has_creator_info = False
        has_scholarly_source = False
        has_news_source = False
        
        for source in self.evidence_summary:
            source_type_lower = source.source_type.lower()
            if source_type_lower in ["web", "website", "online article", "news"]:
                has_web_source = True
            if "creator" in source_type_lower or "channel" in source_type_lower:
                has_creator_info = True
            if "academic" in source_type_lower or "journal" in source_type_lower or "scholar" in source_type_lower:
                has_scholarly_source = True
            if "news" in source_type_lower:
                has_news_source = True
        
        # Create default search queries based on the video title and content
        # Remove special characters and replace spaces with + for URL
        clean_title = re.sub(r'[^\w\s]', '', self.title)
        search_terms = "+".join(clean_title.split())
        
        # Add standard web sources if we don't have enough sources
        if not self.evidence_summary or len(self.evidence_summary) < 2:
            logger.info(f"Adding default evidence sources for video {self.media_embed.video_id}")
            
            # Add YouTube video details as first source
            video_source = EvidenceSource(
                source_name="Original Video",
                source_type="Video Source",
                url=f"https://youtu.be/{self.media_embed.video_id}",
                text="Primary content source - Original video that was analyzed for claim verification",
                title=self.title
            )
            self.evidence_summary.append(video_source)
            
            # Add a Google search for general information
            general_source = EvidenceSource(
                source_name="General Information",
                source_type="Web Search",
                url=f"https://www.google.com/search?q={search_terms}",
                text="Referenced across multiple claims - General information related to the topics discussed in the video",
                title="Web Search Results"
            )
            self.evidence_summary.append(general_source)
        
        # Add scholarly sources if needed
        if not has_scholarly_source:
            # Add a Google Scholar search for academic sources
            scholarly_source = EvidenceSource(
                source_name="Academic Research",
                source_type="Web / Academic",
                url=f"https://scholar.google.com/scholar?q={search_terms}",
                text="Academic validation source - Provides scientific context and peer-reviewed research related to claims made in the video",
                title="Scholarly Research Database"
            )
            self.evidence_summary.append(scholarly_source)
        
        # Add news sources if needed
        if not has_news_source:
            # Add a Google News search for recent news coverage
            news_source = EvidenceSource(
                source_name="Recent News Coverage",
                source_type="Web / News",
                url=f"https://news.google.com/search?q={search_terms}",
                text="Current context source - Offers recent news articles and updates on the topics discussed in the video",
                title="News Articles Database"
            )
            self.evidence_summary.append(news_source)
        
        # Add creator information if this might be an expose video and we don't have creator info
        if not has_creator_info and self._is_expose_video():
            # Extract channel ID from video ID or create YouTube URL
            channel_url = f"https://www.youtube.com/watch?v={self.media_embed.video_id}"
            
            creator_source = EvidenceSource(
                source_name="Video Creator Profile",
                source_type="Channel Assessment",
                url=channel_url,
                text="Authority assessment source - Essential for evaluating the creator's expertise, previous work, and potential biases",
                title="Creator Background Research"
            )
            self.evidence_summary.append(creator_source)
    
    def _is_expose_video(self):
        """Determine if this is likely an expose or investigative video."""
        expose_keywords = ["expose", "investigation", "uncovered", "truth", "revealed", 
                          "scandal", "secret", "hidden", "conspiracy", "shocking", 
                          "what they don't want you to know", "fraud", "deception"]
        
        title_lower = self.title.lower()
        desc_lower = self.description.lower()
        
        # Check title and description for expose keywords
        for keyword in expose_keywords:
            if keyword in title_lower or keyword in desc_lower:
                return True
                
        return False
        
    def to_markdown(self) -> str:
        md = []
        
        # Ensure we have at least one web source in the evidence summary
        self._ensure_web_sources()
        
        # Use the MediaEmbed's to_markdown method for consistency
        md.append(self.media_embed.to_markdown())
        md.append("")
        
        # Add video description section
        md.append("## Video Description")
        md.append(self.description)
        md.append("")
        
        # Overall Assessment
        md.append(f"## 1. Overall Truthfulness Assessment: {self.overall_assessment[0]}")
        md.append(self.overall_assessment[1])
        md.append("")
        
        # Key Findings
        md.append("## 2. Summary of Key Findings")
        md.append("|Finding|Description|")
        md.append("|-------|-----------|")
        for finding in self.key_findings:
            md.append(f"|**{finding.category}**|{finding.description}|")
        md.append("")
        
        # Claims Breakdown
        md.append("## 3. Claims Breakdown with Verification Results")
        md.append("|Claim|Verification Result|Explanation|")
        md.append("|-----|-------------------|-----------|")
        for claim in self.claims_breakdown:
            md.append(claim.to_markdown())
        md.append("")
        
        # Evidence Summary
        md.append("## 4. Evidence Summary")
        
        # Add statistics summary
        total_sources = len(self.evidence_summary)
        source_types = {}
        for source in self.evidence_summary:
            source_type = source.source_type
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        # Calculate high-quality source percentage
        high_quality_types = ["Scientific Journal", "Medical Institution", "Government", "Academic"]
        high_quality_count = sum(count for type_, count in source_types.items() if type_ in high_quality_types)
        high_quality_percentage = (high_quality_count / total_sources * 100) if total_sources > 0 else 0
        
        # Add summary statistics
        md.append("### Evidence Statistics")
        md.append(f"- Total Sources: {total_sources}")
        md.append(f"- High-Quality Sources: {high_quality_count} ({high_quality_percentage:.1f}%)")
        md.append(f"- Source Types: {len(source_types)} different categories")
        md.append("")
        
        # Add source type breakdown
        md.append("### Source Type Breakdown")
        md.append("|Type|Count|Percentage|")
        md.append("|----|-----|----------|")
        for source_type, count in sorted(source_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_sources * 100) if total_sources > 0 else 0
            md.append(f"|{source_type}|{count}|{percentage:.1f}%|")
        md.append("")
        
        # Add primary sources table
        md.append("### Primary Sources")
        md.append("|Source|Type|Relevance|Link|")
        md.append("|------|-----|---------|-----|")
        for source in self.evidence_summary:
            # Generate a descriptive source name without the URL
            source_name = source.source_name
            if (source_name == "Click Here" or source_name == "") and source.title:
                source_name = source.title
            elif (source_name == "Click Here" or source_name == "") and source.url:
                # Extract a readable name from the URL
                url_parts = source.url.split('/')
                domain = url_parts[2] if len(url_parts) > 2 else "Unknown Source"
                
                # Format domain names more nicely
                if "mayoclinic.org" in domain:
                    source_name = "Mayo Clinic"
                elif "ncbi.nlm.nih.gov" in domain:
                    source_name = "PubMed/NCBI"
                elif "harvard.edu" in domain:
                    source_name = "Harvard Health"
                elif "scholar.google" in domain:
                    source_name = "Academic Research"
                elif "news.google" in domain:
                    source_name = "News Articles"
                elif "youtube.com" in domain:
                    source_name = "YouTube Channel"
                else:
                    # Try to extract a clean domain name
                    domain_parts = domain.split('.')
                    if len(domain_parts) >= 2:
                        source_name = domain_parts[-2].capitalize()
                    else:
                        source_name = domain.capitalize()
            
            # Create a separate link field
            link_field = f"[View Source]({source.url})" if source.url else "Not available"
            
            # Generate a better relevance description
            if source.text and len(source.text.strip()) > 0:
                # Use the text field directly, which should now include claim count information
                relevance = source.text
            elif "mayoclinic" in str(source.url) or "harvard" in str(source.url) or "nih.gov" in str(source.url):
                relevance = "Authoritative medical source on safe and effective weight loss"
            elif "scholar.google" in str(source.url):
                relevance = "Provides scientific context and peer-reviewed research related to claims made in the video"
            elif "news.google" in str(source.url):
                relevance = "Offers recent news articles and updates on the topics discussed in the video"
            elif "youtube.com/channel" in str(source.url):
                relevance = "Essential for evaluating the creator's expertise, previous work, and potential biases"
            else:
                relevance = "Supporting evidence for video claims"
            
            md.append(f"|{source_name}|{source.source_type}|{relevance}|{link_field}|")
        md.append("")
        
        # Add creator reputation analysis section if this is an expose video
        if self._is_expose_video():
            md.append("### Creator Credibility Assessment")
            md.append("*This section evaluates the creator's credibility, which is particularly important for investigative content.*")
            md.append("")
            md.append("|Factor|Assessment|Method to Verify|")
            md.append("|------|----------|----------------|")
            md.append("|Previous Accuracy|Evaluation of the creator's track record on factual claims.|Fact-check previous videos, verify past claims with reliable sources.|")
            md.append("|Domain Expertise|Assessment of the creator's qualifications in this subject area.|Research creator's background, education, experience in the field.|")
            md.append("|Transparency|How transparent is the creator about sources and methods?|Examine citation practices, disclosure of conflicts, and methodology.|")
            md.append("|Conflicts of Interest|Identification of potential biases in the presentation.|Check financial ties, affiliations, and disclosure statements.|")
            md.append("|Community Reputation|How the creator is viewed by experts in the field.|Review expert opinions, third-party evaluations, and professional recognition.|")
            md.append("")
        
        # Secondary Sources
        if self.secondary_sources:
            md.append("### Secondary Sources")
            for source in self.secondary_sources:
                md.append(f"- {source}")
            md.append("")
        
        # CRAAP Analysis
        md.append("## 5. CRAAP Analysis")
        md.append("|Criterion|Score|Explanation|")
        md.append("|---------|------|-----------|")
        for criterion in self.craap_analysis:
            level = self._get_craap_level(criterion)
            explanation = self._get_craap_explanation(criterion)
            md.append(f"|{criterion}|{level}|{explanation}|")
        md.append("")
        
        # Recommendations
        if self.recommendations:
            md.append("## 6. Recommendations")
            for rec in self.recommendations:
                md.append(f"- {rec}")
            md.append("")
        
        # Evidence Details
        if self.evidence_details:
            md.append("## 7. Evidence Details")
            for detail in self.evidence_details:
                md.append(f"### {detail.source_name}")
                md.append(f"- **Credibility Level:** {detail.credibility_level}")
                md.append(f"- **Justification:** {detail.justification}")
                md.append("")
        
        return "\n".join(md) 