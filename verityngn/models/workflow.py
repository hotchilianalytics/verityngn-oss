from typing import Dict, List, Optional, Any, Union, TypedDict

class MediaEmbed(TypedDict, total=False):
    """Media embed information."""
    title: str
    video_id: str
    description: str
    thumbnail_url: str
    video_url: str

class InitialAnalysisState(TypedDict, total=False):
    """State for the initial analysis workflow."""
    video_url: str
    video_id: str
    out_dir_path: Optional[str]
    video_path: Optional[str]
    chunk_file_name: Optional[str]
    initial_report: Optional[Union[str, Dict[str, Any]]]
    transcription: Optional[str]
    claims: List[Dict[str, Any]]
    current_claim_index: int
    aggregated_evidence: List[Dict[str, Any]]
    markdown_report_content: Optional[str]
    claim_source_markdown_content: Optional[Dict[str, Any]]
    html_report_content: Optional[str]
    final_report: Optional[Dict[str, Any]]
    gcs_base_uri: Optional[str]
    html_path: Optional[str]
    media_embed: Optional[MediaEmbed]
    json_path: Optional[str]
    markdown_path: Optional[str]
    gcs_uri: Optional[str]
    video_info: Optional[Dict[str, Any]]

class ClaimVerificationState(TypedDict, total=False):
    """State for claim verification workflow."""
    claim: Optional[Dict[str, Any]]
    evidence: List[Dict[str, Any]]
    verification_result: Optional[Dict[str, Any]]
    video_url: str
    video_title: str 