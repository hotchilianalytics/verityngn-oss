"""Discourse derailment sleeve — Krykoniuk, Hopkin-King & Roberts (2026).

Paper: *Using LLMs to identify discourse derailment as a potential cue for
disinformation in social media posts*, Humanit Soc Sci Commun (2026).
DOI: 10.1057/s41599-026-07900-x
Companion: The Conversation, 2026-06-12 (Discourser: expected replies vs actual).

Interview mapping (CEO panel):
  interviewer question  →  original comment / expected topic
  Karp answer           →  actual reply
  LLM expected replies  →  on-topic continuations of the question

This is a **topic-shift / red-herring cue**, not a lie detector and not a
disinformation label. The paper states derailment may be malicious *or* benign
and is an early-warning signal only.

Offline fallback: 1 − Jaccard(token(Q), token(A)). Live path asks Gemini for
three expected on-topic replies and a 0–1 derailment score.
"""
from __future__ import annotations

from typing import Any, Optional
import json
import logging
import os
import re
import statistics

logger = logging.getLogger(__name__)

PAPER = {
    "title": "Using LLMs to identify discourse derailment as a potential cue for disinformation in social media posts",
    "authors": "Krykoniuk, Hopkin-King & Roberts",
    "year": 2026,
    "doi": "10.1057/s41599-026-07900-x",
    "url": "https://www.nature.com/articles/s41599-026-07900-x",
    "conversation": "https://theconversation.com/ai-is-making-disinformation-harder-to-spot-but-weve-found-a-new-way-to-catch-it-288671",
    "software": "Discourser (Zenodo 10.5281/zenodo.20592492)",
    "limits": (
        "LLM ≈ human agreement (~77%) but uses different cues; reported bias. "
        "Derailment is not deception. Interview Q&A is an adaptation of YouTube-comment Discourser."
    ),
}

_STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "are",
    "was", "were", "it", "this", "that", "with", "as", "at", "by", "be", "you",
    "we", "i", "they", "he", "she", "your", "our", "so", "but", "if", "not",
}


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOP}


def jaccard_derailment(question: str, answer: str) -> float:
    """1 − Jaccard overlap. 0 = fully on-topic (identical tokens), 1 = no overlap."""
    q, a = _tokens(question), _tokens(answer)
    if not q or not a:
        return 0.5
    inter = len(q & a)
    union = len(q | a)
    return round(1.0 - (inter / union), 4) if union else 0.5


def _is_question_style(style: str | None) -> bool:
    s = (style or "").lower()
    return any(w in s for w in ("question", "inquisitive", "probing", "clarifying", "follow-up"))


def _mid(seg: dict[str, Any]) -> float:
    return 0.5 * (float(seg.get("start_sec") or 0) + float(seg.get("end_sec") or 0))


def _nearby_text(center_sec: float, claims: list[dict[str, Any]], window_sec: float = 45.0) -> str:
    bits: list[str] = []
    for c in claims:
        t = c.get("timestamp")
        ts: float | None = None
        if isinstance(t, (int, float)):
            ts = float(t)
        elif isinstance(t, str) and ":" in t:
            parts = t.split(":")
            try:
                ts = float(parts[-2]) * 60 + float(parts[-1]) if len(parts) >= 2 else float(parts[0])
            except ValueError:
                ts = None
        if ts is not None and abs(ts - center_sec) <= window_sec:
            bits.append(str(c.get("claim_text") or ""))
    return " ".join(bits)


def _spoken_near(center_sec: float, tier_b: list[dict[str, Any]], window_sec: float = 60.0) -> str:
    bits: list[str] = []
    for b in tier_b:
        win = b.get("window") or {}
        csec = float(win.get("center_sec") or win.get("start_sec") or 0)
        if abs(csec - center_sec) <= window_sec:
            bits.append(str(b.get("spoken_content") or ""))
    return " ".join(x for x in bits if x)


def extract_qa_pairs(
    tier_a_segments: list[dict[str, Any]],
    claims: Optional[list[dict[str, Any]]] = None,
    *,
    tier_b: Optional[list[dict[str, Any]]] = None,
    max_gap_sec: float = 90.0,
) -> list[dict[str, Any]]:
    """Pair consecutive interviewer-style segments with the next answer segment."""
    claims = claims or []
    tier_b = tier_b or []
    segs = sorted(
        [s for s in tier_a_segments if isinstance(s, dict)],
        key=lambda s: float(s.get("start_sec") or 0),
    )
    pairs: list[dict[str, Any]] = []
    i = 0
    while i < len(segs) - 1:
        q = segs[i]
        if not _is_question_style(q.get("delivery_style")):
            i += 1
            continue
        a = segs[i + 1]
        gap = float(a.get("start_sec") or 0) - float(q.get("end_sec") or 0)
        if _is_question_style(a.get("delivery_style")) or gap > max_gap_sec:
            i += 1
            continue
        q_text = " ".join(
            x for x in (
                _nearby_text(_mid(q), claims, window_sec=90.0),
                _spoken_near(_mid(q), tier_b),
            ) if x
        )
        a_text = " ".join(
            x for x in (
                _nearby_text(_mid(a), claims, window_sec=90.0),
                _spoken_near(_mid(a), tier_b),
            ) if x
        )
        pairs.append(
            {
                "q_start_sec": q.get("start_sec"),
                "a_start_sec": a.get("start_sec"),
                "question_style": q.get("delivery_style"),
                "answer_style": a.get("delivery_style"),
                "question_text": q_text[:500],
                "answer_text": a_text[:800],
                "question_emotion": q.get("vocal_emotion"),
                "answer_emotion": a.get("vocal_emotion"),
            }
        )
        i += 2
    return [p for p in pairs if len(_tokens(p["question_text"])) >= 4 and len(_tokens(p["answer_text"])) >= 4]


def _offline_score_pairs(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for p in pairs:
        q, a = p.get("question_text") or "", p.get("answer_text") or ""
        qn, an = len(_tokens(q)), len(_tokens(a))
        row = dict(p)
        row["expected_replies"] = []
        if qn < 4 or an < 4:
            row["derailment"] = None
            row["source"] = "insufficient_text"
            row["cues"] = ["insufficient_text"]
            out.append(row)
            continue
        score = jaccard_derailment(q, a)
        row["derailment"] = score
        row["source"] = "jaccard_offline"
        row["cues"] = ["low_token_overlap"] if score >= 0.55 else []
        out.append(row)
    return out


def _live_score_pairs(pairs: list[dict[str, Any]]) -> Optional[list[dict[str, Any]]]:
    if os.environ.get("MULTISENSE_OFFLINE", "0") in {"1", "true", "True"}:
        return None
    try:
        from verityngn.services.fusion.gemini_multisense import _get_genai_client, _model_name
    except Exception:  # noqa: BLE001
        return None
    client = _get_genai_client()
    if client is None:
        return None
    payload = [
        {"i": i, "question": p.get("question_text"), "answer": p.get("answer_text")}
        for i, p in enumerate(pairs)
    ]
    prompt = (
        "You adapt Discourser (Krykoniuk et al. 2026): for each interviewer QUESTION, "
        "write 3 expected on-topic replies, then score how far the ACTUAL answer "
        "derails from that topic.\n"
        "derailment is 0 = fully on-topic, 1 = red herring / non sequitur / topic hijack.\n"
        "Do NOT judge truth, deception, or disinformation. Topic shift only.\n"
        "Cues if present: red_herring, non_sequitur, personal_attack, low_acknowledgement.\n"
        "Return STRICT JSON: {\"pairs\": [{\"i\": int, \"expected_replies\": [str,str,str], "
        "\"derailment\": 0..1, \"cues\": [str]}]}\n\n"
        f"PAIRS:\n{json.dumps(payload, ensure_ascii=False)[:12000]}"
    )
    try:
        resp = client.models.generate_content(model=_model_name(), contents=[prompt])
        text = getattr(resp, "text", None) or ""
        if not text and getattr(resp, "candidates", None):
            text = resp.candidates[0].content.parts[0].text
        m = re.search(r"\{.*\}", text, re.S)
        data = json.loads(m.group(0) if m else text)
        by_i = {int(r["i"]): r for r in (data.get("pairs") or []) if "i" in r}
    except Exception as exc:  # noqa: BLE001
        logger.warning("[derailment] live Gemini failed: %s", exc)
        return None
    out = []
    for i, p in enumerate(pairs):
        live = by_i.get(i) or {}
        row = dict(p)
        try:
            score = float(live.get("derailment"))
        except (TypeError, ValueError):
            score = jaccard_derailment(p.get("question_text") or "", p.get("answer_text") or "")
        row["derailment"] = round(max(0.0, min(1.0, score)), 4)
        row["expected_replies"] = (live.get("expected_replies") or [])[:3]
        row["cues"] = live.get("cues") or []
        row["source"] = "gemini_expected_vs_actual"
        out.append(row)
    return out


def score_derailment(
    tier_a_segments: list[dict[str, Any]],
    claims: Optional[list[dict[str, Any]]] = None,
    *,
    tier_b: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    pairs = extract_qa_pairs(tier_a_segments, claims, tier_b=tier_b)
    if not pairs:
        return {
            "n_pairs": 0,
            "mean_derailment": None,
            "band": "no_qa",
            "pairs": [],
            "paper": PAPER,
            "disclaimer": PAPER["limits"],
        }
    scored = _live_score_pairs(pairs) or _offline_score_pairs(pairs)
    vals = [float(p["derailment"]) for p in scored if p.get("derailment") is not None]
    if not vals:
        return {
            "n_pairs": len(scored),
            "mean_derailment": None,
            "band": "insufficient_text",
            "source": scored[0].get("source") if scored else None,
            "pairs": scored,
            "paper": PAPER,
            "disclaimer": PAPER["limits"],
        }
    mean = statistics.mean(vals)
    if mean >= 0.45:
        band = "high"
    elif mean >= 0.25:
        band = "moderate"
    else:
        band = "low"
    return {
        "n_pairs": len(scored),
        "mean_derailment": round(mean, 4),
        "max_derailment": round(max(vals), 4),
        "band": band,
        "source": scored[0].get("source"),
        "pairs": scored,
        "paper": PAPER,
        "disclaimer": PAPER["limits"],
    }
