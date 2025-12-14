#!/usr/bin/env python3
"""
Lightweight secret scanner for CI.

Goals:
- Catch obvious credential leaks (API keys, private keys) in tracked files
- Avoid false positives from placeholder examples by using length-aware regexes

This is not a replacement for dedicated scanners (gitleaks/trufflehog),
but it is fast, offline, and good enough to block accidental commits.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES: List[Rule] = [
    Rule(
        "Google API key (AIzaSy...)",
        re.compile(r"AIzaSy[0-9A-Za-z\-_]{30,}"),
    ),
    Rule(
        "OpenAI key (sk-...)",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    ),
    Rule(
        "Anthropic key (sk-ant-...)",
        re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{20,}\b"),
    ),
    Rule(
        "Private key block",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.IGNORECASE,
        ),
    ),
]


IGNORE_PATHS_PREFIXES = (
    ".git/",
    "outputs/",
    "outputs_debug/",
    "downloads/",
    "test_results/",
    "logs/",
)

IGNORE_FILENAMES = {
    "cookies.txt",
}


def _git_tracked_files() -> List[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def _should_ignore(path: str) -> bool:
    if path.startswith(IGNORE_PATHS_PREFIXES):
        return True
    if Path(path).name in IGNORE_FILENAMES:
        return True
    return False


def _iter_text_files(paths: Iterable[str]) -> Iterable[Tuple[str, str]]:
    for p in paths:
        if _should_ignore(p):
            continue
        path = Path(p)
        try:
            data = path.read_bytes()
        except Exception:
            continue

        # Skip binary-ish files
        if b"\x00" in data[:4096]:
            continue

        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            continue

        yield p, text


def main() -> int:
    files = _git_tracked_files()
    findings: List[Tuple[str, str, str]] = []  # (file, rule, snippet)

    for file_path, text in _iter_text_files(files):
        for rule in RULES:
            m = rule.pattern.search(text)
            if m:
                start = max(m.start() - 40, 0)
                end = min(m.end() + 40, len(text))
                snippet = text[start:end].replace("\n", "\\n")
                findings.append((file_path, rule.name, snippet))

    if findings:
        print("🚨 Potential secrets detected:\n")
        for fp, rule_name, snippet in findings:
            print(f"- {fp}: {rule_name}")
            print(f"  snippet: {snippet}")
        print("\nFix: remove the secret, rotate it, and use env vars / Streamlit secrets.")
        return 1

    print("✅ Secret scan passed (no obvious secrets found).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


