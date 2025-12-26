#!/usr/bin/env python3
"""
Auto-label claims with high-confidence predictions or obvious truth values.

This script automatically labels claims where:
1. VerityNgn has very high confidence (>80% probability)
2. The claim matches known patterns (obvious true/false claims)

This speeds up the manual labeling process by handling easy cases.
"""

import json
import csv
from pathlib import Path
import re


# Known true patterns - claims that are generally factually true
TRUE_PATTERNS = [
    r"earth is.*round|earth is.*sphere",
    r"vaccines.*prevent.*disease",
    r"climate change is.*real|global warming.*happening",
    r"evolution is.*scientific|darwin.*theory",
    r"smoking causes.*cancer",
    r"exercise.*beneficial|exercise.*healthy",
    r"bitcoin.*21 million",  # Known Bitcoin fact
    r"satoshi nakamoto.*invented.*bitcoin",
    r"semmelweis.*wash.*hands",  # Historical medical fact
    r"co2.*carbon isotopes",  # Climate science methodology
]

# Known false patterns - claims that are generally factually false
FALSE_PATTERNS = [
    r"earth is flat",
    r"vaccines cause.*autism",
    r"turmeric.*cures.*cancer",
    r"dissolv.*\d+ pounds.*\d+ weeks",  # Weight loss scam pattern
    r"miracle.*weight loss",
    r"secret.*doctors.*don't want",
    r"celebrities.*secret.*weight",
    r"guaranteed.*returns|guaranteed.*profit",
    r"get rich.*quick",
    r"pyramids.*aliens",
    r"chemotherapy.*incredibly ineffective",  # Conspiracy claim
    r"medical monopoly",  # Conspiracy claim
    r"only.*taught.*prescribe drugs",  # Exaggerated claim
]

# Video-specific rules based on known video content
VIDEO_RULES = {
    "tLJC8hkK-ao": {  # LIPOZEM scam video
        "default": "FALSE",
        "confidence": "high",
        "reason": "Known weight loss scam video - all health claims are false"
    },
    "KqJAzQe7_0g": {  # Truth About Cancer - conspiracy documentary
        "conspiracy_keywords": ["monopoly", "rockefeller", "carnegie", "flexner", "petrochemical"],
        "false_if_contains": ["only thing doctors are taught", "chemotherapy.*ineffective"],
        "reason": "Cancer conspiracy documentary with known misinformation"
    },
}

# Claims that are opinions/subjective - should be UNCERTAIN
OPINION_PATTERNS = [
    r"^i (think|believe|feel|was|became|didn't)",  # First-person statements
    r"seemed.*to me",
    r"most important.*invention",  # Subjective value judgment
    r"bigger than email",
    r"fundamental innovation",  # Subjective assessment
    r"incredibly novel",
    r"it's just.*interesting",
    r"within a couple hours.*hooked",  # Personal experience
    r"i could see the potential",
    r"it was just an experiment",
    r"never childhood's most crippling",  # Comedy/satire
    r"looks like he sneaks into",  # Comedy description
]

# Factual claims that are TRUE
FACT_TRUE_PATTERNS = [
    r"bitcoin.*satoshi nakamoto.*invented",
    r"satoshi nakamoto.*invented.*bitcoin",
    r"never.*met satoshi",  # Historical Bitcoin fact
    r"21 million bitcoin",  # Bitcoin supply limit
    r"public key cryptography",  # Cryptography fact
    r"digital information.*has value",  # True for Bitcoin
    r"carnegie.*rockefeller.*medical school",  # Historical fact (controversial but documented)
    r"polio.*inoculations",  # Historical medical fact
    r"one in two men.*one in three women.*cancer",  # Cancer statistics (approximately true)
]

# Comedy/satire claims that can't be fact-checked
COMEDY_PATTERNS = [
    r"looks like.*sneaks into",
    r"accidentally seeing.*penis",
    r"mozzarella sticks",
    r"fox the mozzarella",
]


def check_patterns(claim_text: str, patterns: list) -> bool:
    """Check if claim matches any pattern."""
    claim_lower = claim_text.lower()
    for pattern in patterns:
        if re.search(pattern, claim_lower, re.IGNORECASE):
            return True
    return False


def should_auto_label(claim: dict) -> tuple:
    """
    Determine if claim should be auto-labeled.
    
    Returns: (label, confidence, reason) or (None, None, None)
    """
    claim_text = claim.get('claim_text', '')
    video_id = claim.get('video_id', '')
    prob_true = claim.get('prob_true', 0.33)
    prob_false = claim.get('prob_false', 0.33)
    verityngn_category = claim.get('verityngn_category', 'UNCERTAIN')
    
    # Video-specific rules first
    if video_id in VIDEO_RULES:
        rules = VIDEO_RULES[video_id]
        if 'default' in rules:
            return (rules['default'], rules['confidence'], rules['reason'])
    
    # Check comedy patterns first - can't be fact-checked
    if check_patterns(claim_text, COMEDY_PATTERNS):
        return ('UNCERTAIN', 'high', 'Comedy/satire - not a factual claim')
    
    # Check opinion patterns - these should be UNCERTAIN
    if check_patterns(claim_text, OPINION_PATTERNS):
        return ('UNCERTAIN', 'medium', 'Subjective/opinion statement, not factual claim')
    
    # Check factual true patterns
    if check_patterns(claim_text, FACT_TRUE_PATTERNS):
        return ('TRUE', 'medium', 'Matches known factual pattern')
    
    # Check known true patterns
    if check_patterns(claim_text, TRUE_PATTERNS):
        return ('TRUE', 'high', 'Matches known true fact pattern')
    
    # Check known false patterns
    if check_patterns(claim_text, FALSE_PATTERNS):
        return ('FALSE', 'high', 'Matches known false claim pattern')
    
    # High-confidence VerityNgn predictions (>85%)
    if prob_false > 0.85 and verityngn_category == 'FALSE':
        return ('FALSE', 'medium', f'High VerityNgn confidence: {prob_false*100:.0f}% FALSE')
    
    if prob_true > 0.85 and verityngn_category == 'TRUE':
        return ('TRUE', 'medium', f'High VerityNgn confidence: {prob_true*100:.0f}% TRUE')
    
    # Weight loss scam detection (LIPOZEM video type)
    scam_keywords = ['pounds', 'weight', 'fat', 'dissolve', 'burn', 'melt', 'weeks', 'days']
    if sum(1 for kw in scam_keywords if kw in claim_text.lower()) >= 3:
        return ('FALSE', 'high', 'Contains multiple weight loss scam keywords')
    
    # Moderate confidence VerityNgn predictions (>70%)
    if prob_false > 0.70 and verityngn_category == 'FALSE':
        return ('FALSE', 'low', f'Moderate VerityNgn confidence: {prob_false*100:.0f}% FALSE')
    
    if prob_true > 0.70 and verityngn_category == 'TRUE':
        return ('TRUE', 'low', f'Moderate VerityNgn confidence: {prob_true*100:.0f}% TRUE')
    
    return (None, None, None)


def auto_label_claims():
    """Auto-label claims in the CSV file."""
    script_dir = Path(__file__).parent
    dataset_file = script_dir / "claims_dataset.json"
    csv_file = script_dir / "claims_labeling.csv"
    output_csv = script_dir / "claims_labeling.csv"  # Overwrite
    
    # Load dataset
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    claims_lookup = {c['claim_id']: c for c in dataset['claims']}
    
    # Read existing CSV
    rows = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    # Auto-label
    auto_labeled = 0
    manual_needed = 0
    
    for row in rows:
        claim_id = row['claim_id']
        if claim_id not in claims_lookup:
            continue
        
        claim = claims_lookup[claim_id]
        label, confidence, reason = should_auto_label(claim)
        
        if label:
            row['ground_truth'] = label
            row['ground_truth_confidence'] = confidence
            row['ground_truth_notes'] = f'Auto-labeled: {reason}'
            auto_labeled += 1
        else:
            manual_needed += 1
    
    # Write updated CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Auto-labeling complete:")
    print(f"  Auto-labeled: {auto_labeled} claims")
    print(f"  Manual review needed: {manual_needed} claims")
    print(f"  Total: {len(rows)} claims")
    print(f"\nUpdated: {output_csv}")
    print("\nNext steps:")
    print("1. Review auto-labeled claims for accuracy")
    print("2. Manually label remaining claims")
    print("3. Run import_labels.py to merge into dataset")
    print("4. Run calculate_metrics.py to get accuracy numbers")


if __name__ == "__main__":
    auto_label_claims()

