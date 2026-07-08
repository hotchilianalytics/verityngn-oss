"""Unit tests for citation URL safety filter."""
import pytest

from verityngn.services.reputation.url_safety import (
    filter_safe_evidence,
    filter_safe_urls,
    is_safe_url,
    sanitize_url_list_in_text,
)

# --- Malicious signatures from production incident (tLS6t3FVOTI) ---

OJS_POISONED = (
    "https://www.ncl.ecu.edu/plugins/generic/pdfJsViewer/pdf.js/web/viewer.html"
    "?file=%2Findex.php%2Findex%2Flogin%2FsignOut%3Fsource%3D%2Esu7u%2Eshop%2Fmale%2F&id=1brEWY"
)

KRPANO_POISONED = (
    "https://www2.beaufortccc.edu/tours/?xml=data:image/gif;imagebase64;base64,"
    "PGtycGFubyBvbnN0YXJ0PSJsb2FkcGFubygnL1wvdmlkZW9zLWd0YWcueHl6L3dwLWpzb24vdnIva2V0by9sZXRzLWtldG8td2hlcmUtdG8tYnV5LWFuZC13aGF0LXRvLWtub3cnKTsiPjwva3JwYW5vPg=="
)

MALICIOUS_URLS = [
    OJS_POISONED,
    KRPANO_POISONED,
    "https://inni.hon-yu.com/7knswdj0o8hln6bme262/",
    "https://mattioli1885journals.com/plugins/generic/pdfJsViewer/pdf.js/web/viewer.html"
    "?file=%2Findex.php%2Findex%2Flogin%2FsignOut%3Fsource%3D%2Efeelcools%2Ecom%2F"
    "&ai=m_male-extra-overview-male-extra-review-2024",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
]

LEGIT_URLS = [
    "https://www.nytimes.com/2024/11/10/opinion/wellness-bro-science.html",
    "https://www.hubermanlab.com/newsletter/using-light-for-health",
    "https://www.mcgill.ca/oss/article/critical-thinking-health-and-nutrition/andrew-huberman-has-bad-case-supplement-brain",
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC123456/",
    "https://www.opss.org/article/tongkat-ali-uses-and-safety-dietary-supplements",
    "https://www.examine.com/supplements/tongkat-ali/",
    "https://www.theguardian.com/us-news/2024/mar/28/podcaster-andrew-huberman-goop-for-bros",
    "https://www.ahajournals.org/doi/10.1161/cir.0000000000000625",
]

FUZZY_MALICIOUS = [
    "https://feelcoolz.com/male/",
    "https://video-gtag.xyz/page",
    "https://hon-yu.co/redirect",
]

FUZZY_LEGIT = [
    "https://www.nytimes.com/page",
    "https://hubermanlab.com/news",
]


@pytest.mark.parametrize("url", MALICIOUS_URLS)
def test_malicious_urls_blocked(url: str):
    assert is_safe_url(url) is False


@pytest.mark.parametrize("url", LEGIT_URLS)
def test_legit_urls_allowed(url: str):
    assert is_safe_url(url) is True


def test_empty_and_whitespace_blocked():
    assert is_safe_url("") is False
    assert is_safe_url("   ") is False


def test_filter_safe_urls_dedupes():
    urls = [LEGIT_URLS[0], LEGIT_URLS[0], MALICIOUS_URLS[0]]
    out = filter_safe_urls(urls)
    assert out == [LEGIT_URLS[0]]


def test_filter_safe_evidence():
    items = [
        {"url": LEGIT_URLS[0], "title": "ok"},
        {"url": MALICIOUS_URLS[0], "title": "bad"},
        {"title": "no url"},
    ]
    out = filter_safe_evidence(items)
    assert len(out) == 2
    assert out[0]["url"] == LEGIT_URLS[0]


def test_sanitize_url_list_in_text():
    text = f"See {LEGIT_URLS[0]} and {MALICIOUS_URLS[0]} for more."
    cleaned = sanitize_url_list_in_text(text)
    assert LEGIT_URLS[0] in cleaned
    assert MALICIOUS_URLS[0] not in cleaned


@pytest.mark.parametrize("url", FUZZY_MALICIOUS)
def test_fuzzy_scam_hosts_blocked(url: str):
    assert is_safe_url(url) is False


@pytest.mark.parametrize("url", FUZZY_LEGIT)
def test_fuzzy_legit_hosts_allowed(url: str):
    assert is_safe_url(url) is True
