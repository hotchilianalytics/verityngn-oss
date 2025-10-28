"""
Claim Corpus Analysis Module

Analyzes historical claims data to identify patterns, extract best practices,
and generate insights for improving claim extraction quality.
"""

import json
import logging
from typing import List, Dict, Any
from collections import defaultdict, Counter
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class ClaimCorpusAnalyzer:
    """Analyzes corpus of claims from multiple runs to extract quality patterns."""

    def __init__(self, corpus_file: str):
        """
        Initialize analyzer with claims corpus file.

        Args:
            corpus_file: Path to JSON file containing all runs' claims data
        """
        self.corpus_file = Path(corpus_file)
        self.all_runs = []
        self.unique_claims = []
        self.claims_by_result = defaultdict(list)
        self.claims_by_type = defaultdict(list)

    def load_corpus(self) -> None:
        """Load and parse the claims corpus."""
        logger.info(f"Loading claims corpus from {self.corpus_file}")

        with open(self.corpus_file, "r") as f:
            self.all_runs = json.load(f)

        # Extract all unique claims
        seen_texts = set()
        for run in self.all_runs:
            if "data" in run and "claims" in run["data"]:
                for claim in run["data"]["claims"]:
                    claim_text = claim.get("claim_text", "")
                    if claim_text and claim_text not in seen_texts:
                        seen_texts.add(claim_text)
                        self.unique_claims.append(claim)
                        result = claim.get("result", "UNKNOWN")
                        self.claims_by_result[result].append(claim)

        logger.info(
            f"Loaded {len(self.all_runs)} runs with {len(self.unique_claims)} unique claims"
        )
        logger.info(
            f"Result distribution: {dict(Counter([c.get('result') for c in self.unique_claims]))}"
        )

    def analyze_best_claims(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Identify and analyze the best claims (verified as TRUE).

        Args:
            top_n: Number of top claims to analyze

        Returns:
            List of best claims with analysis
        """
        logger.info("Analyzing best claims...")

        best_claims = []
        for claim in self.claims_by_result.get("HIGHLY_LIKELY_TRUE", []):
            analysis = self._analyze_claim_quality(claim)
            best_claims.append({"claim": claim, "quality_analysis": analysis})

        logger.info(f"Found {len(best_claims)} HIGHLY_LIKELY_TRUE claims")
        return best_claims[:top_n]

    def analyze_worst_claims(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Identify and analyze the worst claims (UNCERTAIN with poor verification).

        Args:
            top_n: Number of worst claims to analyze

        Returns:
            List of worst claims with analysis
        """
        logger.info("Analyzing worst claims...")

        worst_claims = []
        for claim in self.claims_by_result.get("UNCERTAIN", [])[:top_n]:
            analysis = self._analyze_claim_quality(claim)
            worst_claims.append({"claim": claim, "quality_analysis": analysis})

        logger.info(f"Analyzed {len(worst_claims)} UNCERTAIN claims")
        return worst_claims

    def _analyze_claim_quality(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze quality characteristics of a claim.

        Args:
            claim: Claim dictionary

        Returns:
            Quality analysis dictionary
        """
        claim_text = claim.get("claim_text", "")

        # Calculate specificity indicators
        has_numbers = bool(re.search(r"\d+", claim_text))
        has_dates = bool(re.search(r"\b(19|20)\d{2}\b", claim_text))
        has_percentages = bool(re.search(r"\d+%", claim_text))
        has_proper_nouns = bool(
            re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", claim_text)
        )

        # Detect vague language
        vague_terms = [
            "a study",
            "experts",
            "researchers",
            "some",
            "many",
            "often",
            "recently",
        ]
        vagueness_count = sum(
            1 for term in vague_terms if term.lower() in claim_text.lower()
        )

        # Detect specific attributions
        specific_sources = [
            "Journal",
            "University",
            "Institute",
            "Magazine",
            "Hospital",
        ]
        has_specific_source = any(source in claim_text for source in specific_sources)

        return {
            "has_numbers": has_numbers,
            "has_dates": has_dates,
            "has_percentages": has_percentages,
            "has_proper_nouns": has_proper_nouns,
            "vagueness_count": vagueness_count,
            "has_specific_source": has_specific_source,
            "claim_length": len(claim_text),
            "word_count": len(claim_text.split()),
        }

    def categorize_claims(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize claims by type using pattern matching.

        Returns:
            Dictionary mapping category names to lists of claims
        """
        logger.info("Categorizing claims by type...")

        categories = {
            "credential": [],
            "publication": [],
            "study": [],
            "efficacy": [],
            "celebrity": [],
            "conspiracy": [],
            "other": [],
        }

        for claim in self.unique_claims:
            claim_text = claim.get("claim_text", "").lower()

            if any(
                term in claim_text
                for term in [
                    "dr.",
                    "doctor",
                    "phd",
                    "md",
                    "professor",
                    "credentials",
                    "license",
                    "board certified",
                ]
            ):
                categories["credential"].append(claim)
            elif any(
                term in claim_text
                for term in [
                    "magazine",
                    "publication",
                    "published",
                    "journal",
                    "article",
                    "dubbed",
                    "named",
                    "awarded",
                ]
            ):
                categories["publication"].append(claim)
            elif any(
                term in claim_text
                for term in [
                    "study",
                    "research",
                    "clinical trial",
                    "volunteers",
                    "participants",
                    "peer-reviewed",
                ]
            ):
                categories["study"].append(claim)
            elif any(
                term in claim_text
                for term in [
                    "lost",
                    "pounds",
                    "weight",
                    "efficacy",
                    "effective",
                    "results",
                    "improved",
                ]
            ):
                categories["efficacy"].append(claim)
            elif any(
                term in claim_text
                for term in [
                    "celebrity",
                    "hollywood",
                    "stars",
                    "famous",
                    "secret weapon",
                ]
            ):
                categories["celebrity"].append(claim)
            elif any(
                term in claim_text
                for term in [
                    "conspiracy",
                    "threatened",
                    "pharma",
                    "suppressed",
                    "hidden",
                    "secret",
                ]
            ):
                categories["conspiracy"].append(claim)
            else:
                categories["other"].append(claim)

        # Log distribution
        distribution = {cat: len(claims) for cat, claims in categories.items()}
        logger.info(f"Claim category distribution: {distribution}")

        return categories

    def generate_quality_report(self, output_file: str) -> None:
        """
        Generate comprehensive quality analysis report.

        Args:
            output_file: Path to save report JSON
        """
        logger.info("Generating quality analysis report...")

        # Analyze best and worst claims
        best_claims = self.analyze_best_claims(top_n=10)
        worst_claims = self.analyze_worst_claims(top_n=10)

        # Categorize all claims
        categories = self.categorize_claims()

        # Calculate aggregate statistics
        all_analyses = [
            self._analyze_claim_quality(claim) for claim in self.unique_claims
        ]

        report = {
            "corpus_summary": {
                "total_runs": len(self.all_runs),
                "total_unique_claims": len(self.unique_claims),
                "result_distribution": {
                    result: len(claims)
                    for result, claims in self.claims_by_result.items()
                },
                "category_distribution": {
                    cat: len(claims) for cat, claims in categories.items()
                },
            },
            "best_claims": best_claims,
            "worst_claims": worst_claims,
            "aggregate_statistics": {
                "avg_claim_length": sum(a["claim_length"] for a in all_analyses)
                / len(all_analyses),
                "avg_word_count": sum(a["word_count"] for a in all_analyses)
                / len(all_analyses),
                "pct_with_numbers": sum(1 for a in all_analyses if a["has_numbers"])
                / len(all_analyses)
                * 100,
                "pct_with_dates": sum(1 for a in all_analyses if a["has_dates"])
                / len(all_analyses)
                * 100,
                "pct_with_specific_sources": sum(
                    1 for a in all_analyses if a["has_specific_source"]
                )
                / len(all_analyses)
                * 100,
                "avg_vagueness_score": sum(a["vagueness_count"] for a in all_analyses)
                / len(all_analyses),
            },
            "insights": self._generate_insights(best_claims, worst_claims, categories),
        }

        # Save report
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Quality report saved to {output_file}")

    def _generate_insights(
        self,
        best_claims: List[Dict],
        worst_claims: List[Dict],
        categories: Dict[str, List],
    ) -> Dict[str, Any]:
        """Generate insights by comparing best vs worst claims."""

        # Compare best vs worst characteristics
        if best_claims:
            best_analyses = [c["quality_analysis"] for c in best_claims]
            avg_best_vagueness = sum(a["vagueness_count"] for a in best_analyses) / len(
                best_analyses
            )
            pct_best_with_dates = (
                sum(1 for a in best_analyses if a["has_dates"])
                / len(best_analyses)
                * 100
            )
            pct_best_with_sources = (
                sum(1 for a in best_analyses if a["has_specific_source"])
                / len(best_analyses)
                * 100
            )
        else:
            avg_best_vagueness = 0
            pct_best_with_dates = 0
            pct_best_with_sources = 0

        if worst_claims:
            worst_analyses = [c["quality_analysis"] for c in worst_claims]
            avg_worst_vagueness = sum(
                a["vagueness_count"] for a in worst_analyses
            ) / len(worst_analyses)
            pct_worst_with_dates = (
                sum(1 for a in worst_analyses if a["has_dates"])
                / len(worst_analyses)
                * 100
            )
            pct_worst_with_sources = (
                sum(1 for a in worst_analyses if a["has_specific_source"])
                / len(worst_analyses)
                * 100
            )
        else:
            avg_worst_vagueness = 0
            pct_worst_with_dates = 0
            pct_worst_with_sources = 0

        return {
            "best_vs_worst_comparison": {
                "avg_vagueness_difference": avg_worst_vagueness - avg_best_vagueness,
                "dates_difference": pct_best_with_dates - pct_worst_with_dates,
                "sources_difference": pct_best_with_sources - pct_worst_with_sources,
            },
            "recommendations": [
                "Prioritize claims with specific dates and sources",
                "Avoid vague terms like 'a study' or 'experts say'",
                f"Focus on {max(categories, key=lambda k: len(categories[k]))} category claims (most common)",
                "Extract absence claims about missing credentials",
            ],
        }


def main():
    """Main entry point for corpus analysis."""
    logging.basicConfig(level=logging.INFO)

    # Initialize analyzer with consolidated data
    analyzer = ClaimCorpusAnalyzer("/tmp/tLJC8hkK-ao_all_runs_analysis.json")

    # Load and analyze corpus
    analyzer.load_corpus()

    # Generate quality report
    analyzer.generate_quality_report("/tmp/tLJC8hkK-ao_claim_quality_analysis.json")

    logger.info("Corpus analysis complete!")


if __name__ == "__main__":
    main()
