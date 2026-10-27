from verityngn.schemas.claim_risk import from_disclosure, from_video_claim


def test_video_and_disclosure_share_keys():
    video = from_video_claim(
        {
            "claim_id": 7,
            "claim_text": "The product is FDA approved.",
            "initial_assessment": "CONTESTED",
            "claim_kind": "source_backed_fact",
            "evidence": [{"source_name": "FDA", "text": "No NDA found", "url": "https://example.com"}],
        }
    )
    disc = from_disclosure(
        {
            "pair_id": "msft-1",
            "hedged": "We may experience cybersecurity incidents.",
            "materialized": "We determined a cybersecurity incident was material.",
            "action": "Rewrite",
            "score": 0.81,
        }
    )
    assert set(video.model_dump()) == set(disc.model_dump())
    assert video.source_lane == "video"
    assert disc.source_lane == "disclosure"
    assert disc.verdict_or_action == "REWRITE"
    assert video.verdict_or_action == "CONTESTED"
