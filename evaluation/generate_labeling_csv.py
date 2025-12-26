#!/usr/bin/env python3
"""
Generate a CSV file for manual ground truth labeling.

This script reads the claims dataset and generates a CSV file that can be
opened in a spreadsheet application for easy manual labeling of ground truth.
"""

import json
import csv
from pathlib import Path


def generate_labeling_csv():
    """Generate CSV for labeling from claims dataset."""
    script_dir = Path(__file__).parent
    dataset_file = script_dir / "claims_dataset.json"
    output_csv = script_dir / "claims_labeling.csv"
    
    # Load dataset
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    claims = dataset['claims']
    
    # Define CSV columns
    columns = [
        'claim_id',
        'video_id',
        'video_title',
        'claim_text',
        'verityngn_verdict',
        'verityngn_category',
        'prob_true',
        'prob_false',
        'ground_truth',  # Manual: TRUE, FALSE, or UNCERTAIN
        'ground_truth_confidence',  # Manual: high, medium, low
        'ground_truth_sources',  # Manual: URLs or references
        'ground_truth_notes',  # Manual: explanation
    ]
    
    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for claim in claims:
            # Prepare row
            row = {
                'claim_id': claim['claim_id'],
                'video_id': claim['video_id'],
                'video_title': claim['video_title'][:50],  # Truncate for readability
                'claim_text': claim['claim_text'],
                'verityngn_verdict': claim['verityngn_verdict'],
                'verityngn_category': claim['verityngn_category'],
                'prob_true': claim['prob_true'],
                'prob_false': claim['prob_false'],
                'ground_truth': '',  # To be filled manually
                'ground_truth_confidence': '',  # To be filled manually
                'ground_truth_sources': '',  # To be filled manually
                'ground_truth_notes': '',  # To be filled manually
            }
            writer.writerow(row)
    
    print(f"Generated labeling CSV: {output_csv}")
    print(f"Total claims to label: {len(claims)}")
    print()
    print("Instructions:")
    print("1. Open the CSV in Excel/Google Sheets")
    print("2. For each claim, fill in:")
    print("   - ground_truth: TRUE, FALSE, or UNCERTAIN")
    print("   - ground_truth_confidence: high, medium, or low")
    print("   - ground_truth_sources: URLs or references that support your label")
    print("   - ground_truth_notes: Brief explanation of your decision")
    print("3. Save the CSV when done")
    print("4. Run import_labels.py to merge labels back into the dataset")


if __name__ == "__main__":
    generate_labeling_csv()

