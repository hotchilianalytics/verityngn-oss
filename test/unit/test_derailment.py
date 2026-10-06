from verityngn.services.fusion.derailment import (
    extract_qa_pairs,
    jaccard_derailment,
    score_derailment,
)


def test_jaccard_on_topic_low_derailment():
    q = "How is Palantir using NVIDIA models for government customers?"
    a = "Palantir and NVIDIA models let government customers keep their data."
    assert jaccard_derailment(q, a) < 0.7


def test_jaccard_red_herring_high_derailment():
    q = "What is Palantir revenue guidance this quarter?"
    a = "The little tyrant bans his opposition and immigration is the real issue."
    assert jaccard_derailment(q, a) > 0.7


def test_extract_qa_pairs_and_offline_score(monkeypatch):
    monkeypatch.setenv("MULTISENSE_OFFLINE", "1")
    segs = [
        {"start_sec": 10, "end_sec": 25, "delivery_style": "probing question", "vocal_emotion": "neutral"},
        {"start_sec": 26, "end_sec": 50, "delivery_style": "prepared confident", "vocal_emotion": "anger"},
    ]
    claims = [
        {"timestamp": 18, "claim_text": "How will the Nvidia partnership work for agencies?"},
        {"timestamp": 35, "claim_text": "We keep the data on the ontology so tokens cannot steal IP."},
    ]
    pairs = extract_qa_pairs(segs, claims)
    assert len(pairs) == 1
    out = score_derailment(segs, claims)
    assert out["n_pairs"] == 1
    assert out["mean_derailment"] is not None
    assert out["source"] == "jaccard_offline"
    assert "not deception" in (out["disclaimer"] or "").lower()
