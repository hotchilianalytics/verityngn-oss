#!/usr/bin/env python3
"""
Import ground truth labels from CSV back into the claims dataset.

This script reads the labeled CSV and merges the ground truth labels
back into the JSON dataset for analysis.
"""

import json
import csv
from pathlib import Path


def import_labels():
    """Import labels from CSV into the dataset."""
    script_dir = Path(__file__).parent
    dataset_file = script_dir / "claims_dataset.json"
    labels_csv = script_dir / "claims_labeling.csv"
    output_file = script_dir / "claims_dataset_labeled.json"
    
    # Load original dataset
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # Create lookup by claim_id
    claims_lookup = {c['claim_id']: c for c in dataset['claims']}
    
    # Read labels from CSV
    labeled_count = 0
    with open(labels_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            claim_id = row['claim_id']
            if claim_id in claims_lookup:
                claim = claims_lookup[claim_id]
                
                # Update ground truth fields
                ground_truth = row.get('ground_truth', '').strip().upper()
                if ground_truth in ['TRUE', 'FALSE', 'UNCERTAIN']:
                    claim['ground_truth'] = ground_truth
                    claim['ground_truth_confidence'] = row.get('ground_truth_confidence', '').strip().lower()
                    claim['ground_truth_sources'] = row.get('ground_truth_sources', '').strip()
                    claim['ground_truth_notes'] = row.get('ground_truth_notes', '').strip()
                    claim['labeler'] = 'manual'
                    labeled_count += 1
    
    # Update metadata
    dataset['metadata']['labeling_status'] = 'partial' if labeled_count < len(dataset['claims']) else 'complete'
    dataset['metadata']['labeled_claims'] = labeled_count
    dataset['metadata']['unlabeled_claims'] = len(dataset['claims']) - labeled_count
    
    # Save labeled dataset
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"Imported {labeled_count} labels from CSV")
    print(f"Saved labeled dataset to: {output_file}")


if __name__ == "__main__":
    import_labels()

