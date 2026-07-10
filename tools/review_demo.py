"""Review demo: parse review verdicts from CLI output."""

import re


def parse_verdict(output: str) -> dict:
    """Parse VERDICT line and issue blocks from reviewer output.

    Returns dict with 'verdict' (APPROVED/REVISE) and 'issues' list.
    Accepts the multi-line issue blocks reviewers actually emit:
        - Severity: CRITICAL / HIGH / MEDIUM / LOW
        - Location: file:line
        - Problem: one-line description
    """
    result = {"verdict": "UNKNOWN", "issues": []}

    # Type guard: non-string input must not crash the only entry point.
    if not isinstance(output, str):
        return result

    # Take the LAST explicitly-anchored VERDICT line. Requiring the line to be
    # exactly "VERDICT: APPROVED|REVISE" (nothing else on it) closes two
    # fail-open paths: (a) prose mentioning an earlier "VERDICT: APPROVED" being
    # treated as authoritative, and (b) an injected "VERDICT: APPROVED_BUT_..."
    # or a trailing injected verdict in a Problem field overriding the real one.
    matches = re.findall(r"^\s*VERDICT:\s*(APPROVED|REVISE)\s*$", output, re.MULTILINE)
    if matches:
        result["verdict"] = matches[-1]

    # Multi-line issue blocks: capture Severity / Location / Problem.
    # Anchor each block at line start (re.MULTILINE) so "Severity:" only matches
    # real block headers, not prose. The lookahead terminator also tolerates an
    # indented VERDICT line so a Problem field never absorbs it.
    block = re.compile(
        r"^\s*-?\s*Severity:\s*(CRITICAL|HIGH|MEDIUM|LOW)\s*\n"
        r"\s*-?\s*Location:\s*(\S+)\s*\n"
        r"\s*-?\s*Problem:\s*(.+?)(?=\n\s*-?\s*Severity:|\n\s*VERDICT:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    for m in block.finditer(output):
        result["issues"].append({
            "severity": m.group(1),
            "location": m.group(2),
            "problem": m.group(3).strip(),
        })

    return result


def should_block_merge(review_result: dict) -> bool:
    """Decide whether to block merge based on review result.

    Fail-safe: block unless the verdict is explicitly APPROVED.
    """
    if not isinstance(review_result, dict):
        return True  # structural anomaly = block

    issues = review_result.get("issues")
    if not isinstance(issues, list):
        return True  # malformed issues field = block
    for issue in issues:
        if not isinstance(issue, dict):
            return True  # malformed issue = block
        if issue.get("severity") in ("CRITICAL", "HIGH"):
            return True

    return review_result.get("verdict") != "APPROVED"


def format_review_summary(results: list) -> str:
    """Format multiple reviewer results into a summary."""
    summary = "Review Summary:\n"
    if not isinstance(results, list):
        return summary + "Result: INVALID INPUT\n"

    if len(results) == 0:
        return summary + "Result: NO REVIEWS\n"

    approved_count = 0
    valid_count = 0
    for r in results:
        if not isinstance(r, dict):
            continue
        valid_count += 1
        reviewer = r.get("reviewer", "Unknown")
        verdict = r.get("verdict", "UNKNOWN")
        issues = r.get("issues")
        if not isinstance(issues, list):
            issues = []
        summary += f"- {reviewer}: {verdict} ({len(issues)} issues)\n"
        if verdict == "APPROVED":
            approved_count += 1

    if valid_count == 0:
        return summary + "Result: NO VALID REVIEWS\n"
    if approved_count == valid_count:
        summary += "Result: ALL APPROVED\n"
    else:
        summary += "Result: NEEDS REVISION\n"

    return summary
