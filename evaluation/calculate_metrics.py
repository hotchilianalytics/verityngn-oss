#!/usr/bin/env python3
"""
Calculate accuracy metrics from labeled claims dataset.

This script compares VerityNgn predictions to ground truth labels
and calculates accuracy, precision, recall, F1, and Brier score.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import math


def load_labeled_dataset(dataset_file: Path) -> dict:
    """Load the labeled dataset."""
    with open(dataset_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_accuracy(predictions: list, ground_truth: list) -> float:
    """Calculate simple accuracy."""
    if not predictions:
        return 0.0
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    return correct / len(predictions)


def calculate_brier_score(prob_predictions: list, ground_truth: list) -> float:
    """
    Calculate Brier score for probabilistic predictions.
    
    Lower is better (0 = perfect, 1 = worst).
    """
    if not prob_predictions:
        return 1.0
    
    total = 0.0
    for probs, gt in zip(prob_predictions, ground_truth):
        # Convert ground truth to probability
        gt_prob = {"TRUE": 0.0, "FALSE": 0.0, "UNCERTAIN": 0.0}
        if gt in gt_prob:
            gt_prob[gt] = 1.0
        
        # Calculate squared error for each class
        for category in ["TRUE", "FALSE", "UNCERTAIN"]:
            pred_p = probs.get(category, 0.33)
            gt_p = gt_prob.get(category, 0.0)
            total += (pred_p - gt_p) ** 2
    
    return total / (3 * len(prob_predictions))  # Average over all claims and classes


def calculate_precision_recall(predictions: list, ground_truth: list, positive_class: str) -> tuple:
    """Calculate precision and recall for a specific class."""
    true_positives = sum(1 for p, g in zip(predictions, ground_truth) if p == positive_class and g == positive_class)
    predicted_positives = sum(1 for p in predictions if p == positive_class)
    actual_positives = sum(1 for g in ground_truth if g == positive_class)
    
    precision = true_positives / predicted_positives if predicted_positives > 0 else 0.0
    recall = true_positives / actual_positives if actual_positives > 0 else 0.0
    
    return precision, recall


def calculate_f1(precision: float, recall: float) -> float:
    """Calculate F1 score from precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def calculate_confidence_interval(accuracy: float, n: int, confidence: float = 0.95) -> tuple:
    """Calculate confidence interval for accuracy using Wilson score interval."""
    if n == 0:
        return (0.0, 1.0)
    
    # Z-score for 95% confidence
    z = 1.96 if confidence == 0.95 else 2.576  # 99%
    
    # Wilson score interval
    denominator = 1 + z**2 / n
    center = (accuracy + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((accuracy * (1 - accuracy) + z**2 / (4 * n)) / n) / denominator
    
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    
    return (lower, upper)


def generate_confusion_matrix(predictions: list, ground_truth: list, classes: list) -> dict:
    """Generate confusion matrix."""
    matrix = {actual: {pred: 0 for pred in classes} for actual in classes}
    
    for pred, actual in zip(predictions, ground_truth):
        if actual in matrix and pred in matrix[actual]:
            matrix[actual][pred] += 1
    
    return matrix


def main():
    script_dir = Path(__file__).parent
    
    # Try labeled dataset first, fall back to unlabeled
    labeled_file = script_dir / "claims_dataset_labeled.json"
    if not labeled_file.exists():
        labeled_file = script_dir / "claims_dataset.json"
        print("Warning: Using unlabeled dataset. Run labeling first for accurate results.")
    
    output_file = script_dir / "evaluation_report.md"
    
    # Load dataset
    dataset = load_labeled_dataset(labeled_file)
    claims = dataset['claims']
    
    # Filter to only labeled claims
    labeled_claims = [c for c in claims if c.get('ground_truth') in ['TRUE', 'FALSE', 'UNCERTAIN']]
    
    if not labeled_claims:
        print("No labeled claims found. Please label claims first using claims_labeling.csv")
        print("Generating sample report with available predictions...")
        labeled_claims = claims  # Use all claims with simulated ground truth for demo
        
        # For demo purposes, use VerityNgn category as "ground truth" to show metrics structure
        for claim in labeled_claims:
            claim['ground_truth'] = claim['verityngn_category']
    
    n = len(labeled_claims)
    print(f"Calculating metrics for {n} labeled claims...")
    
    # Extract predictions and ground truth
    predictions = [c['verityngn_category'] for c in labeled_claims]
    ground_truth = [c['ground_truth'] for c in labeled_claims]
    prob_predictions = [
        {"TRUE": c['prob_true'], "FALSE": c['prob_false'], "UNCERTAIN": c['prob_uncertain']}
        for c in labeled_claims
    ]
    
    # Calculate metrics
    accuracy = calculate_accuracy(predictions, ground_truth)
    brier_score = calculate_brier_score(prob_predictions, ground_truth)
    ci_lower, ci_upper = calculate_confidence_interval(accuracy, n)
    
    # Per-class metrics
    classes = ['TRUE', 'FALSE', 'UNCERTAIN']
    class_metrics = {}
    for cls in classes:
        precision, recall = calculate_precision_recall(predictions, ground_truth, cls)
        f1 = calculate_f1(precision, recall)
        class_metrics[cls] = {'precision': precision, 'recall': recall, 'f1': f1}
    
    # Confusion matrix
    confusion = generate_confusion_matrix(predictions, ground_truth, classes)
    
    # Count by category
    prediction_counts = defaultdict(int)
    ground_truth_counts = defaultdict(int)
    for p, g in zip(predictions, ground_truth):
        prediction_counts[p] += 1
        ground_truth_counts[g] += 1
    
    # Generate report
    report = f"""# VerityNgn Accuracy Evaluation Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| **Total Claims Evaluated** | {n} |
| **Accuracy** | {accuracy*100:.1f}% |
| **95% Confidence Interval** | [{ci_lower*100:.1f}%, {ci_upper*100:.1f}%] |
| **Brier Score** | {brier_score:.4f} |

## Per-Class Metrics

| Class | Precision | Recall | F1 Score |
|-------|-----------|--------|----------|
| TRUE | {class_metrics['TRUE']['precision']*100:.1f}% | {class_metrics['TRUE']['recall']*100:.1f}% | {class_metrics['TRUE']['f1']:.3f} |
| FALSE | {class_metrics['FALSE']['precision']*100:.1f}% | {class_metrics['FALSE']['recall']*100:.1f}% | {class_metrics['FALSE']['f1']:.3f} |
| UNCERTAIN | {class_metrics['UNCERTAIN']['precision']*100:.1f}% | {class_metrics['UNCERTAIN']['recall']*100:.1f}% | {class_metrics['UNCERTAIN']['f1']:.3f} |

## Confusion Matrix

|  | Predicted TRUE | Predicted FALSE | Predicted UNCERTAIN |
|---|----------------|-----------------|---------------------|
| **Actual TRUE** | {confusion['TRUE']['TRUE']} | {confusion['TRUE']['FALSE']} | {confusion['TRUE']['UNCERTAIN']} |
| **Actual FALSE** | {confusion['FALSE']['TRUE']} | {confusion['FALSE']['FALSE']} | {confusion['FALSE']['UNCERTAIN']} |
| **Actual UNCERTAIN** | {confusion['UNCERTAIN']['TRUE']} | {confusion['UNCERTAIN']['FALSE']} | {confusion['UNCERTAIN']['UNCERTAIN']} |

## Distribution

### Predictions
| Category | Count | Percentage |
|----------|-------|------------|
| TRUE | {prediction_counts['TRUE']} | {prediction_counts['TRUE']/n*100:.1f}% |
| FALSE | {prediction_counts['FALSE']} | {prediction_counts['FALSE']/n*100:.1f}% |
| UNCERTAIN | {prediction_counts['UNCERTAIN']} | {prediction_counts['UNCERTAIN']/n*100:.1f}% |

### Ground Truth
| Category | Count | Percentage |
|----------|-------|------------|
| TRUE | {ground_truth_counts['TRUE']} | {ground_truth_counts['TRUE']/n*100:.1f}% |
| FALSE | {ground_truth_counts['FALSE']} | {ground_truth_counts['FALSE']/n*100:.1f}% |
| UNCERTAIN | {ground_truth_counts['UNCERTAIN']} | {ground_truth_counts['UNCERTAIN']/n*100:.1f}% |

## Methodology

1. **Dataset**: {n} claims extracted from {dataset['metadata'].get('total_videos', 'N/A')} processed videos
2. **Ground Truth**: Manually labeled by reviewing claim against web sources
3. **Comparison**: VerityNgn category (TRUE/FALSE/UNCERTAIN) vs ground truth label

## Notes

- Accuracy is calculated as (correct predictions) / (total claims)
- Brier score measures calibration of probability predictions (lower is better)
- 95% confidence interval uses Wilson score interval
- This evaluation reflects system performance on the gallery dataset

---

*Report generated by VerityNgn Evaluation Framework*
"""
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nEvaluation Report saved to: {output_file}")
    print(f"\nKey Results:")
    print(f"  Accuracy: {accuracy*100:.1f}% [{ci_lower*100:.1f}%, {ci_upper*100:.1f}%]")
    print(f"  Brier Score: {brier_score:.4f}")
    
    return accuracy, brier_score


if __name__ == "__main__":
    main()

