# VerityNgn Accuracy Evaluation

This directory contains the evaluation framework for measuring VerityNgn's accuracy against ground truth labels.

## Quick Start

```bash
# 1. Extract claims from gallery reports
python extract_claims.py

# 2. Generate CSV for labeling
python generate_labeling_csv.py

# 3. Label claims in claims_labeling.csv (manually or use auto_label.py)
python auto_label.py  # Auto-labels high-confidence cases

# 4. Import labels back into dataset
python import_labels.py

# 5. Calculate accuracy metrics
python calculate_metrics.py
```

## Files

| File | Description |
|------|-------------|
| `extract_claims.py` | Extracts claims from gallery JSON reports |
| `generate_labeling_csv.py` | Creates CSV for manual labeling |
| `auto_label.py` | Auto-labels obvious TRUE/FALSE cases |
| `import_labels.py` | Imports labels from CSV to JSON dataset |
| `calculate_metrics.py` | Calculates accuracy, Brier score, etc. |
| `claims_dataset.json` | Extracted claims with VerityNgn predictions |
| `claims_labeling.csv` | CSV for manual ground truth labeling |
| `claims_dataset_labeled.json` | Dataset with ground truth labels |
| `evaluation_report.md` | Final accuracy report |

## Labeling Guidelines

### Ground Truth Categories

- **TRUE**: The claim is factually accurate based on reliable sources
- **FALSE**: The claim is factually inaccurate based on reliable sources
- **UNCERTAIN**: Cannot determine truth value due to:
  - Conflicting evidence
  - Subjective/opinion claim
  - Insufficient evidence

### Confidence Levels

- **high**: Clear-cut case with authoritative sources
- **medium**: Reasonable confidence with good sources
- **low**: Best guess, limited sources available

### Source Guidelines

1. Prefer fact-checking sites (Snopes, PolitiFact, FactCheck.org)
2. Use Wikipedia for established facts
3. Use scientific journals for health/science claims
4. Use official sources for financial claims

## Metrics Calculated

- **Accuracy**: Percentage of correct predictions
- **Precision/Recall/F1**: Per-class performance
- **Brier Score**: Calibration of probability predictions
- **Confidence Interval**: 95% Wilson score interval

## Notes

- Claims are categorized as TRUE/FALSE/UNCERTAIN based on VerityNgn's probability distribution
- The evaluation compares VerityNgn's category against human ground truth labels
- For rigorous evaluation, aim for at least 100 labeled claims

