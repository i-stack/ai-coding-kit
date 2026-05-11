#!/usr/bin/env python3
"""Detect whether the just-ended Claude Code turn looks like an iOS
engineering task and whether its last assistant text message contains a
<usage-audit>...</usage-audit> block.

Reads the Stop-hook JSON payload on stdin, prints a single decision line
on stdout. The bash wrapper consumes that line.

Output schema:
  OK|pos=<n>|neg=<n>|is_ios=<0|1>|has_audit=<0|1>|session=<id>|hash=<12hex>
  SKIP|<reason>

Always exits 0.
"""

import hashlib
import json
import os
import re
import sys


def emit(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.exit(0)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        emit(f"SKIP|bad-payload:{type(e).__name__}")

    transcript_path = payload.get("transcript_path") or ""
    session_id = (payload.get("session_id") or "").strip()

    if not transcript_path or not os.path.isfile(transcript_path):
        emit("SKIP|no-transcript")

    last_text = ""
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if obj.get("type") != "assistant":
                    continue
                msg = obj.get("message") or {}
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content")
                parts = []
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "text":
                            t = c.get("text") or ""
                            if t:
                                parts.append(t)
                joined = "\n".join(parts).strip()
                if joined:
                    last_text = joined
    except Exception as e:
        emit(f"SKIP|read-error:{type(e).__name__}")

    if not last_text:
        emit("SKIP|no-assistant-text")

    # Positive triggers: concrete iOS-engineering signals.
    ios_pos = [
        (r"```swift\b", 2),
        (r"\bSwiftUI\b", 1),
        (r"\bUIKit\b", 1),
        (r"\bUIViewController\b", 1),
        (r"\bUIView\b", 1),
        (r"\bxcodebuild\b", 1),
        (r"\bXcode\b", 1),
        (r"\bPodfile\b", 1),
        (r"\.xcworkspace\b", 1),
        (r"\.xcodeproj\b", 1),
        (r"\.xcconfig\b", 1),
        (r"@MainActor\b", 1),
        (r"@State\b", 1),
        (r"@Observable\b", 1),
        (r"@Published\b", 1),
        (r"\bCombine\b", 1),
        (r"\.swift\b", 1),
        (r"\bIPHONEOS_DEPLOYMENT_TARGET\b", 1),
        (r"\bSWIFT_VERSION\b", 1),
    ]

    # Negative triggers: SkillOps / meta-engineering signals. Per CLAUDE.md
    # these tasks must NOT emit the audit block, so they can't be flagged.
    meta_neg = [
        (r"\bSKILL\.md\b", 2),
        (r"\bCLAUDE\.md\b", 2),
        (r"\bIR-\d", 1),
        (r"\bSYM-\d", 1),
        (r"\bROUTE-\d", 1),
        (r"\bOUT-\d", 1),
        (r"\bMEMORY\.md\b", 1),
        (r"\bsettings\.json\b", 2),
        (r"\busage-audit\b", 2),
        (r"\busage_ledger\b", 2),
        (r"\bledger\b", 1),
        (r"\bself[- ]evolution\b", 1),
        (r"\bSkillOps\b", 2),
        (r"\bproposal\b", 1),
        (r"\bStop hook\b", 2),
        (r"\bPostToolUse\b", 1),
        (r"\bhooks?\.sh\b", 2),
    ]

    def tally(patterns):
        return sum(len(re.findall(p, last_text)) * w for p, w in patterns)

    pos = tally(ios_pos)
    neg = tally(meta_neg)

    # Conservative rule: prefer false negatives over false positives in V1.
    is_ios = pos >= 2 and pos > neg
    has_audit = bool(re.search(r"<usage-audit>.*?</usage-audit>", last_text, re.DOTALL))

    body_hash = hashlib.sha256(last_text.encode("utf-8", errors="replace")).hexdigest()[:12]
    emit(
        f"OK|pos={pos}|neg={neg}|is_ios={int(is_ios)}"
        f"|has_audit={int(has_audit)}|session={session_id}|hash={body_hash}"
    )


if __name__ == "__main__":
    main()
