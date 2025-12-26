# agents/workflows/claim_processor.py
"""
Advanced Claim Processing Subsystem

This module provides comprehensive claim processing capabilities including:
1. Multi-source claim integration (video analysis, YouTube counter-intel, press releases)
2. Generalized ranking criteria applicable to any video content
3. Semantic clustering with representative selection
4. Temporal distribution optimization
5. Unified claim list output for downstream processing
"""

import json
import logging
import os
import re
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.getLogger(__name__).warning(
        "scikit-learn not available, using simple clustering fallback"
    )

class ClaimProcessor:
    """
    Advanced claim processing system that integrates multiple claim sources,
    applies generalized ranking criteria, performs semantic clustering,
    and selects representative claims for verification.
    """
    
    def __init__(self, video_id: str, video_duration_minutes: float = 30.0, target_claims_per_minute: float = 1.0, max_claims: int = None):
        """
        Initialize the claim processor.
        
        Args:
            video_id: Video identifier
            video_duration_minutes: Duration of the video in minutes
            target_claims_per_minute: Target number of claims per minute for final selection
            max_claims: Explicit limit on the number of claims to process (overrides duration-based heuristics)
        """
        self.video_id = video_id
        self.video_duration_minutes = video_duration_minutes
        self.target_claims_per_minute = target_claims_per_minute
        
        if max_claims is not None:
            self.max_claims = max_claims
            logger.info(f"🎯 Using explicit max_claims limit: {self.max_claims}")
        else:
            # Calculate target claims with reasonable min/max bounds
            # Adjusted for quality: Allow more claims as requested by user
            calculated_claims = int(video_duration_minutes * target_claims_per_minute)
            
            # Get min_claims from config if available
            from verityngn.config.settings import get_config
            config = get_config()
            config_min_claims = config.get("processing.min_claims", 20)
            
            # Heuristics for max_claims
            if video_duration_minutes > 30:
                self.max_claims = max(config_min_claims, min(40, calculated_claims))
            elif video_duration_minutes > 15:
                self.max_claims = max(max(15, config_min_claims), min(30, calculated_claims))
            else:
                self.max_claims = max(config_min_claims, min(20, calculated_claims))
        
        # Claim sources
        self.video_analysis_claims = []
        self.youtube_counter_claims = []
        self.press_release_claims = []
        
        # Processing results
        self.all_claims = []
        self.ranked_claims = []
        self.clustered_claims = []
        self.final_claims = []
        
        logger.info(f"🔧 ClaimProcessor initialized for video {video_id}")
        logger.info(f"📊 Target: {self.max_claims} claims from {video_duration_minutes:.1f} minute video")
    
    def add_video_analysis_claims(self, claims: List[Dict[str, Any]]) -> None:
        """Add claims from video analysis (multimodal LLM output)."""
        self.video_analysis_claims = claims
        logger.info(f"📺 Added {len(claims)} video analysis claims")
    
    def add_youtube_counter_claims(self, claims: List[Dict[str, Any]]) -> None:
        """Add claims from YouTube counter-intelligence analysis."""
        self.youtube_counter_claims = claims
        logger.info(f"🎬 Added {len(claims)} YouTube counter-intelligence claims")
    
    def add_press_release_claims(self, claims: List[Dict[str, Any]]) -> None:
        """Add claims from press release analysis."""
        self.press_release_claims = claims
        logger.info(f"📰 Added {len(claims)} press release claims")
    
    def integrate_all_claims(self) -> List[Dict[str, Any]]:
        """
        Integrate claims from all sources into a unified list.
        
        Returns:
            List of all claims with source metadata
        """
        logger.info("🔄 Integrating claims from all sources...")
        
        integrated_claims = []
        
        # Add video analysis claims
        for i, claim in enumerate(self.video_analysis_claims):
            integrated_claim = claim.copy()
            integrated_claim['source_type'] = 'video_analysis'
            integrated_claim['source_priority'] = 3  # Highest priority
            integrated_claim['global_id'] = f"video_{i}"
            integrated_claims.append(integrated_claim)
        
        # Add YouTube counter-intelligence claims
        for i, claim in enumerate(self.youtube_counter_claims):
            integrated_claim = claim.copy()
            integrated_claim['source_type'] = 'youtube_counter'
            integrated_claim['source_priority'] = 2  # Medium priority
            integrated_claim['global_id'] = f"youtube_{i}"
            # Ensure required fields exist
            if 'timestamp' not in integrated_claim:
                integrated_claim['timestamp'] = '00:00'
            if 'speaker' not in integrated_claim:
                integrated_claim['speaker'] = 'Counter-Intelligence Source'
            if 'initial_assessment' not in integrated_claim:
                integrated_claim['initial_assessment'] = 'Counter-intelligence evidence requiring verification'
            integrated_claims.append(integrated_claim)
        
        # Add press release claims
        for i, claim in enumerate(self.press_release_claims):
            integrated_claim = claim.copy()
            integrated_claim['source_type'] = 'press_release'
            integrated_claim['source_priority'] = 1  # Lower priority
            integrated_claim['global_id'] = f"press_{i}"
            # Ensure required fields exist
            if 'timestamp' not in integrated_claim:
                integrated_claim['timestamp'] = '00:00'
            if 'speaker' not in integrated_claim:
                integrated_claim['speaker'] = 'Press Release Source'
            if 'initial_assessment' not in integrated_claim:
                integrated_claim['initial_assessment'] = 'Press release claim requiring verification'
            integrated_claims.append(integrated_claim)
        
        self.all_claims = integrated_claims
        logger.info(f"✅ Integrated {len(integrated_claims)} total claims from all sources")
        logger.info(f"📊 Breakdown: Video={len(self.video_analysis_claims)}, "
                   f"YouTube={len(self.youtube_counter_claims)}, "
                   f"Press={len(self.press_release_claims)}")
        
        return integrated_claims
    
    def calculate_generalized_ranking_scores(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply generalized ranking criteria to all claims.
        
        Args:
            claims: List of integrated claims
            
        Returns:
            List of claims with ranking scores
        """
        logger.info("🎯 Applying generalized ranking criteria...")
        
        scored_claims = []
        
        for claim in claims:
            score = 0
            claim_text = claim.get('claim_text', '').lower()
            speaker = claim.get('speaker', '').lower()
            initial_assessment = claim.get('initial_assessment', '').lower()
            timestamp = claim.get('timestamp', '00:00')
            source_type = claim.get('source_type', 'unknown')
            source_priority = claim.get('source_priority', 1)
            
            # 1. SOURCE TYPE AND PRIORITY
            score += source_priority * 10  # 10-30 points based on source
            
            # 2. TEMPORAL DISTRIBUTION (favor distributed coverage)
            time_seconds = self._get_time_seconds(timestamp)
            time_position = time_seconds / (self.video_duration_minutes * 60)  # 0-1 normalized
            
            # Favor claims from different quartiles
            if time_position < 0.25:  # First quarter
                score += 8
            elif time_position < 0.5:  # Second quarter
                score += 12
            elif time_position < 0.75:  # Third quarter
                score += 15
            else:  # Final quarter
                score += 18
            
            # 3. CLAIM CONTENT ANALYSIS (generalized patterns)
            content_score = self._analyze_claim_content(claim_text)
            score += content_score
            
            # 4. SPEAKER AUTHORITY (generalized patterns)
            authority_score = self._analyze_speaker_authority(speaker)
            score += authority_score
            
            # 5. ASSESSMENT SEVERITY (how problematic/important the claim is)
            severity_score = self._analyze_assessment_severity(initial_assessment)
            score += severity_score
            
            # 6. CLAIM COMPLEXITY AND VERIFIABILITY
            complexity_score = self._analyze_claim_complexity(claim_text)
            score += complexity_score
            
            # 7. UNIQUENESS POTENTIAL (based on content patterns)
            uniqueness_score = self._analyze_uniqueness_potential(claim_text)
            score += uniqueness_score
            
            scored_claim = claim.copy()
            scored_claim['ranking_score'] = score
            scored_claim['scoring_breakdown'] = {
                'source_priority': source_priority * 10,
                'temporal_position': score - (content_score + authority_score + severity_score + complexity_score + uniqueness_score + source_priority * 10),
                'content_analysis': content_score,
                'speaker_authority': authority_score,
                'assessment_severity': severity_score,
                'claim_complexity': complexity_score,
                'uniqueness_potential': uniqueness_score
            }
            
            scored_claims.append(scored_claim)
        
        # Sort by score (highest first)
        scored_claims.sort(key=lambda x: x['ranking_score'], reverse=True)
        
        self.ranked_claims = scored_claims
        logger.info(f"✅ Ranked {len(scored_claims)} claims")
        logger.info(f"📊 Score range: {scored_claims[-1]['ranking_score']:.1f} - {scored_claims[0]['ranking_score']:.1f}")
        
        return scored_claims
    
    def perform_semantic_clustering(self, claims: List[Dict[str, Any]], n_clusters: int = None) -> List[List[Dict[str, Any]]]:
        """
        Perform semantic clustering to group similar claims.
        
        Args:
            claims: List of ranked claims
            n_clusters: Number of clusters (auto-calculated if None)
            
        Returns:
            List of claim clusters
        """
        logger.info("🔬 Performing semantic clustering...")
        
        if len(claims) <= self.max_claims:
            logger.info(f"✅ Claims ({len(claims)}) already within target ({self.max_claims}), skipping clustering")
            self.clustered_claims = [[claim] for claim in claims]
            return self.clustered_claims
        
        # Extract claim texts for vectorization
        claim_texts = [claim.get('claim_text', '') for claim in claims]
        
        # Check if sklearn is available
        if not SKLEARN_AVAILABLE:
            logger.info("Using simple keyword-based clustering (sklearn not available)")
            return self._simple_keyword_clustering(claims)
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            max_df=0.8,
            min_df=2
        )
        
        try:
            tfidf_matrix = vectorizer.fit_transform(claim_texts)
        except ValueError as e:
            logger.warning(f"TF-IDF vectorization failed: {e}. Using simple clustering.")
            # Fallback to simple clustering based on keywords
            return self._simple_keyword_clustering(claims)
        
        # Determine optimal number of clusters
        # Reduced clustering aggressiveness: use // 2 instead of // 3 to preserve more claims
        if n_clusters is None:
            n_clusters = min(self.max_claims, max(5, len(claims) // 2))
        
        logger.info(f"🎯 Clustering {len(claims)} claims into {n_clusters} clusters")
        
        # Perform K-means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)
        
        # Group claims by cluster
        clusters = defaultdict(list)
        for i, label in enumerate(cluster_labels):
            clusters[label].append(claims[i])
        
        # Convert to list of clusters
        clustered_claims = list(clusters.values())
        
        # Sort clusters by average ranking score (highest first)
        if SKLEARN_AVAILABLE:
            clustered_claims.sort(key=lambda cluster: np.mean([c['ranking_score'] for c in cluster]), reverse=True)
        else:
            clustered_claims.sort(key=lambda cluster: sum([c['ranking_score'] for c in cluster]) / len(cluster), reverse=True)
        
        self.clustered_claims = clustered_claims
        logger.info(f"✅ Created {len(clustered_claims)} clusters")
        logger.info(f"📊 Cluster sizes: {[len(cluster) for cluster in clustered_claims]}")
        
        return clustered_claims
    
    def select_representative_claims(self, clusters: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Select the best representative claim from each cluster.
        
        Args:
            clusters: List of claim clusters
            
        Returns:
            List of representative claims
        """
        logger.info("🎯 Selecting representative claims from clusters...")
        
        representative_claims = []
        
        for i, cluster in enumerate(clusters):
            if len(representative_claims) >= self.max_claims:
                break
            
            # Find the best representative based on multiple criteria
            best_claim = self._select_best_representative(cluster)
            best_claim['cluster_id'] = i
            best_claim['cluster_size'] = len(cluster)
            
            representative_claims.append(best_claim)
        
        # Ensure temporal distribution
        representative_claims = self._ensure_temporal_distribution(representative_claims)
        
        self.final_claims = representative_claims
        logger.info(f"✅ Selected {len(representative_claims)} representative claims")
        
        return representative_claims
    
    def process_all_claims(self) -> List[Dict[str, Any]]:
        """
        Execute the complete claim processing pipeline.
        
        Returns:
            Final list of processed claims ready for verification
        """
        logger.info("🚀 Starting complete claim processing pipeline...")
        
        # Step 1: Integrate all claim sources
        integrated_claims = self.integrate_all_claims()
        
        # Step 2: Apply ranking criteria
        ranked_claims = self.calculate_generalized_ranking_scores(integrated_claims)
        
        # Step 3: Perform semantic clustering
        clusters = self.perform_semantic_clustering(ranked_claims)
        
        # Step 4: Select representative claims
        final_claims = self.select_representative_claims(clusters)
        
        logger.info(f"✅ Claim processing complete: {len(integrated_claims)} → {len(final_claims)} claims")
        
        return final_claims
    
    def save_claim_processing_report(self, output_dir: str) -> str:
        """
        Save a comprehensive report of the claim processing results.
        
        Args:
            output_dir: Directory to save the report
            
        Returns:
            Path to the saved report file
        """
        report_data = {
            "video_id": self.video_id,
            "processing_timestamp": datetime.now().isoformat(),
            "configuration": {
                "video_duration_minutes": self.video_duration_minutes,
                "target_claims_per_minute": self.target_claims_per_minute,
                "max_claims": self.max_claims
            },
            "source_statistics": {
                "video_analysis_claims": len(self.video_analysis_claims),
                "youtube_counter_claims": len(self.youtube_counter_claims),
                "press_release_claims": len(self.press_release_claims),
                "total_integrated_claims": len(self.all_claims)
            },
            "processing_results": {
                "ranked_claims_count": len(self.ranked_claims),
                "clusters_created": len(self.clustered_claims),
                "final_claims_count": len(self.final_claims)
            },
            "final_claims": self.final_claims,
            "ranking_analysis": self._generate_ranking_analysis(),
            "temporal_distribution": self._generate_temporal_analysis(),
            "cluster_analysis": self._generate_cluster_analysis()
        }
        
        # Save report
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, f"{self.video_id}_claim_processing_report.json")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # Also save just the final claims list for easy consumption
        claims_list_path = os.path.join(output_dir, f"{self.video_id}_final_claims.json")
        with open(claims_list_path, 'w', encoding='utf-8') as f:
            json.dump(self.final_claims, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Saved claim processing report: {report_path}")
        logger.info(f"📋 Saved final claims list: {claims_list_path}")
        
        return report_path
    
    # Helper methods for content analysis
    
    def _get_time_seconds(self, timestamp: str) -> int:
        """Convert timestamp MM:SS to seconds."""
        try:
            if ':' in timestamp:
                parts = timestamp.split(':')
                if len(parts) == 2:
                    minutes, seconds = map(int, parts)
                    return minutes * 60 + seconds
                elif len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    return hours * 3600 + minutes * 60 + seconds
            return 0
        except:
            return 0
    
    def _analyze_claim_content(self, claim_text: str) -> int:
        """Analyze claim content for importance (generalized patterns)."""
        score = 0
        text_lower = claim_text.lower()
        
        # Scientific/research terms
        if any(term in text_lower for term in ['study', 'research', 'clinical', 'trial', 'peer-reviewed', 'journal', 'published']):
            score += 20
        
        # Authority/credential terms
        if any(term in text_lower for term in ['university', 'doctor', 'professor', 'expert', 'specialist', 'certified']):
            score += 15
        
        # Quantitative claims
        if re.search(r'\d+(%|percent|times|fold|\$|pounds|kg|lbs)', text_lower):
            score += 12
        
        # Health/medical terms
        if any(term in text_lower for term in ['health', 'medical', 'treatment', 'cure', 'disease', 'symptoms']):
            score += 10
        
        # Product/commercial terms
        if any(term in text_lower for term in ['product', 'supplement', 'formula', 'ingredient', 'brand']):
            score += 8
        
        # Conspiracy/misleading indicators
        if any(term in text_lower for term in ['secret', 'hidden', 'industry', 'conspiracy', 'suppressed']):
            score += 6
        
        return score
    
    def _analyze_speaker_authority(self, speaker: str) -> int:
        """Analyze speaker authority (generalized patterns)."""
        score = 0
        speaker_lower = speaker.lower()
        
        if any(term in speaker_lower for term in ['dr.', 'doctor', 'professor', 'phd']):
            score += 15
        elif any(term in speaker_lower for term in ['expert', 'specialist', 'researcher']):
            score += 12
        elif any(term in speaker_lower for term in ['host', 'presenter', 'announcer']):
            score += 8
        elif any(term in speaker_lower for term in ['testimonial', 'reviewer', 'patient']):
            score += 5
        else:
            score += 3
        
        return score
    
    def _analyze_assessment_severity(self, assessment: str) -> int:
        """Analyze assessment severity for claim importance."""
        score = 0
        assessment_lower = assessment.lower()
        
        if any(term in assessment_lower for term in ['highly exaggerated', 'false', 'fabricated', 'misleading']):
            score += 15
        elif any(term in assessment_lower for term in ['exaggerated', 'unsubstantiated', 'questionable']):
            score += 12
        elif any(term in assessment_lower for term in ['requires verification', 'needs verification', 'unverified']):
            score += 10
        elif any(term in assessment_lower for term in ['potentially', 'possibly', 'may be']):
            score += 8
        else:
            score += 5
        
        return score
    
    def _analyze_claim_complexity(self, claim_text: str) -> int:
        """Analyze claim complexity and verifiability."""
        score = 0
        
        # Length complexity
        length = len(claim_text)
        if length > 150:
            score += 10
        elif length > 100:
            score += 8
        elif length > 50:
            score += 5
        else:
            score += 2
        
        # Sentence complexity
        sentence_count = len(re.split(r'[.!?]+', claim_text))
        if sentence_count > 2:
            score += 5
        
        return score
    
    def _analyze_uniqueness_potential(self, claim_text: str) -> int:
        """Analyze potential for claim uniqueness."""
        score = 0
        text_lower = claim_text.lower()
        
        # Specific names, dates, numbers indicate uniqueness
        if re.search(r'\b\d{4}\b', text_lower):  # Year
            score += 5
        if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', claim_text):  # Proper names
            score += 5
        if re.search(r'\$\d+', text_lower):  # Money amounts
            score += 3
        
        return score
    
    def _simple_keyword_clustering(self, claims: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Fallback simple clustering based on keywords."""
        logger.info("Using simple keyword-based clustering")
        
        keyword_groups = defaultdict(list)
        
        for claim in claims:
            claim_text = claim.get('claim_text', '').lower()
            
            # Simple keyword-based grouping
            if any(word in claim_text for word in ['weight', 'fat', 'pounds', 'lose']):
                keyword_groups['weight_loss'].append(claim)
            elif any(word in claim_text for word in ['study', 'research', 'clinical']):
                keyword_groups['scientific'].append(claim)
            elif any(word in claim_text for word in ['doctor', 'expert', 'credential']):
                keyword_groups['authority'].append(claim)
            elif any(word in claim_text for word in ['product', 'supplement', 'formula']):
                keyword_groups['product'].append(claim)
            else:
                keyword_groups['general'].append(claim)
        
        return list(keyword_groups.values())
    
    def _select_best_representative(self, cluster: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best representative from a cluster."""
        if len(cluster) == 1:
            return cluster[0]
        
        # Sort by ranking score and select the highest
        cluster_sorted = sorted(cluster, key=lambda x: x['ranking_score'], reverse=True)
        return cluster_sorted[0]
    
    def _ensure_temporal_distribution(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure good temporal distribution across the video."""
        if len(claims) <= 5:
            return claims
        
        # Group claims by time quartiles
        quartile_claims = {0: [], 1: [], 2: [], 3: []}
        
        for claim in claims:
            time_seconds = self._get_time_seconds(claim.get('timestamp', '00:00'))
            time_position = time_seconds / (self.video_duration_minutes * 60)
            quartile = min(3, int(time_position * 4))
            quartile_claims[quartile].append(claim)
        
        # Ensure each quartile has at least one claim if possible
        distributed_claims = []
        remaining_slots = self.max_claims
        
        for quartile in range(4):
            if quartile_claims[quartile] and remaining_slots > 0:
                # Take at least one from each quartile
                quartile_claims[quartile].sort(key=lambda x: x['ranking_score'], reverse=True)
                distributed_claims.append(quartile_claims[quartile][0])
                remaining_slots -= 1
        
        # Fill remaining slots with highest scoring claims
        all_remaining = []
        for quartile in range(4):
            all_remaining.extend(quartile_claims[quartile][1:])  # Skip the first one we already took
        
        all_remaining.sort(key=lambda x: x['ranking_score'], reverse=True)
        distributed_claims.extend(all_remaining[:remaining_slots])
        
        return distributed_claims
    
    def _generate_ranking_analysis(self) -> Dict[str, Any]:
        """Generate analysis of ranking results."""
        if not self.ranked_claims:
            return {}
        
        scores = [c['ranking_score'] for c in self.ranked_claims]
        return {
            "total_claims": len(self.ranked_claims),
            "score_statistics": {
                "min": min(scores),
                "max": max(scores),
                "mean": np.mean(scores) if SKLEARN_AVAILABLE else sum(scores) / len(scores),
                "median": np.median(scores) if SKLEARN_AVAILABLE else sorted(scores)[len(scores) // 2]
            },
            "source_distribution": {
                source: len([c for c in self.ranked_claims if c.get('source_type') == source])
                for source in ['video_analysis', 'youtube_counter', 'press_release']
            }
        }
    
    def _generate_temporal_analysis(self) -> Dict[str, Any]:
        """Generate analysis of temporal distribution."""
        if not self.final_claims:
            return {}
        
        times = [self._get_time_seconds(c.get('timestamp', '00:00')) for c in self.final_claims]
        return {
            "total_claims": len(self.final_claims),
            "time_range_seconds": f"0-{int(self.video_duration_minutes * 60)}",
            "actual_distribution": {
                "first_quartile": len([t for t in times if t < self.video_duration_minutes * 15]),
                "second_quartile": len([t for t in times if self.video_duration_minutes * 15 <= t < self.video_duration_minutes * 30]),
                "third_quartile": len([t for t in times if self.video_duration_minutes * 30 <= t < self.video_duration_minutes * 45]),
                "fourth_quartile": len([t for t in times if t >= self.video_duration_minutes * 45])
            }
        }
    
    def _generate_cluster_analysis(self) -> Dict[str, Any]:
        """Generate analysis of clustering results."""
        if not self.clustered_claims:
            return {}
        
        return {
            "total_clusters": len(self.clustered_claims),
            "cluster_sizes": [len(cluster) for cluster in self.clustered_claims],
            "reduction_ratio": len(self.final_claims) / len(self.all_claims) if self.all_claims else 0
        }