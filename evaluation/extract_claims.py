#!/usr/bin/env python3
"""
Extract claims from gallery video reports for accuracy evaluation.

This script parses all JSON reports in the gallery and extracts claims
with their VerityNgn verdicts and probability distributions to create
a dataset for ground truth labeling and accuracy measurement.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


def normalize_verdict(verdict: str) -> str:
    """Normalize verdict strings to consistent format."""
    verdict = verdict.upper().replace(" ", "_")
    # Map various formats to standard
    mappings = {
        "HIGHLY_LIKELY_TRUE": "HIGHLY_LIKELY_TRUE",
        "LIKELY_TRUE": "LIKELY_TRUE", 
        "LEANING_TRUE": "LEANING_TRUE",
        "TRUE": "LIKELY_TRUE",
        "UNCERTAIN": "UNCERTAIN",
        "LEANING_FALSE": "LEANING_FALSE",
        "LIKELY_FALSE": "LIKELY_FALSE",
        "HIGHLY_LIKELY_FALSE": "HIGHLY_LIKELY_FALSE",
        "FALSE": "LIKELY_FALSE",
    }
    return mappings.get(verdict, verdict)


def get_verdict_category(verdict: str) -> str:
    """Map detailed verdict to simple TRUE/FALSE/UNCERTAIN category."""
    verdict = normalize_verdict(verdict)
    if verdict in ["HIGHLY_LIKELY_TRUE", "LIKELY_TRUE", "LEANING_TRUE"]:
        return "TRUE"
    elif verdict in ["HIGHLY_LIKELY_FALSE", "LIKELY_FALSE", "LEANING_FALSE"]:
        return "FALSE"
    else:
        return "UNCERTAIN"


def extract_claims_from_report(report_path: Path) -> List[Dict[str, Any]]:
    """Extract claims from a single report JSON file."""
    claims = []
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        print(f"  Error loading {report_path.name}: {e}")
        return []
    
    # Get video metadata
    media_embed = report.get("media_embed", {})
    video_id = media_embed.get("video_id", report_path.stem.split("_")[0])
    video_title = media_embed.get("title", report.get("title", "Unknown"))
    
    # Extract claims
    claims_breakdown = report.get("claims_breakdown", [])
    
    for claim_data in claims_breakdown:
        claim_text = claim_data.get("claim_text", "")
        if not claim_text or len(claim_text) < 10:
            continue  # Skip empty or trivial claims
            
        # Get verification result
        verification = claim_data.get("verification_result", {})
        verdict = verification.get("result", claim_data.get("initial_assessment", "UNCERTAIN"))
        
        # Get probability distribution
        prob_dist = verification.get("probability_distribution", {})
        prob_true = prob_dist.get("TRUE", 0.33)
        prob_false = prob_dist.get("FALSE", 0.33)
        prob_uncertain = prob_dist.get("UNCERTAIN", 0.34)
        
        # Create claim record
        claim_record = {
            "claim_id": f"{video_id}_claim_{claim_data.get('claim_id', len(claims))}",
            "video_id": video_id,
            "video_title": video_title[:100],  # Truncate long titles
            "claim_text": claim_text,
            "timestamp": claim_data.get("timestamp", "Unknown"),
            "speaker": claim_data.get("speaker", "Unknown"),
            "verityngn_verdict": normalize_verdict(verdict),
            "verityngn_category": get_verdict_category(verdict),
            "prob_true": round(prob_true, 4),
            "prob_false": round(prob_false, 4),
            "prob_uncertain": round(prob_uncertain, 4),
            # Ground truth fields to be filled in manually
            "ground_truth": "",  # TRUE, FALSE, or UNCERTAIN
            "ground_truth_confidence": "",  # high, medium, low
            "ground_truth_sources": [],
            "ground_truth_notes": "",
            "labeler": ""
        }
        
        claims.append(claim_record)
    
    return claims


def extract_all_claims(gallery_dir: Path) -> Dict[str, Any]:
    """Extract claims from all reports in the gallery directory."""
    all_claims = []
    video_count = 0
    
    # Find all JSON files
    json_files = list(gallery_dir.glob("*.json"))
    print(f"Found {len(json_files)} report files in gallery")
    
    for report_path in sorted(json_files):
        print(f"Processing: {report_path.name}")
        claims = extract_claims_from_report(report_path)
        if claims:
            all_claims.extend(claims)
            video_count += 1
            print(f"  Extracted {len(claims)} claims")
    
    # Create dataset structure
    dataset = {
        "metadata": {
            "created_date": datetime.now().isoformat(),
            "source": "VerityNgn Gallery Reports",
            "total_claims": len(all_claims),
            "total_videos": video_count,
            "labeling_status": "pending",
            "version": "1.0.0"
        },
        "claims": all_claims
    }
    
    return dataset


def main():
    # Define paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    gallery_dir = project_root / "ui" / "gallery" / "approved"
    output_file = script_dir / "claims_dataset.json"
    
    print("=" * 60)
    print("VerityNgn Claims Extraction for Accuracy Evaluation")
    print("=" * 60)
    print(f"Gallery directory: {gallery_dir}")
    print(f"Output file: {output_file}")
    print()
    
    # Extract claims
    dataset = extract_all_claims(gallery_dir)
    
    # Save dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print("Extraction Complete")
    print("=" * 60)
    print(f"Total videos processed: {dataset['metadata']['total_videos']}")
    print(f"Total claims extracted: {dataset['metadata']['total_claims']}")
    print(f"Output saved to: {output_file}")
    
    # Print summary by verdict category
    categories = {}
    for claim in dataset['claims']:
        cat = claim['verityngn_category']
        categories[cat] = categories.get(cat, 0) + 1
    
    print()
    print("Claims by VerityNgn Category:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()

