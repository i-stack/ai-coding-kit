#!/usr/bin/env python3
"""Load execution settings for an explicitly authorized auto-code-review run.

Merge order, from low to high priority:
  1. env/review.json
  2. .auto-review-config.json
  3. AUTO_REVIEW_* environment variables

By default this prints JSON. Use --shell to emit shell exports for the
The resulting settings never grant request-scoped review or write permission.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG: dict[str, Any] = {
    # Capability availability only. A true value never replaces an explicit
    # user request to start auto-code-review.
    "enabled": True,
    "reviewers": [],
    "maxRounds": 3,
    "allowSelfReview": False,
}


class ConfigError(Exception):
    """Raised when an existing config file cannot be parsed safely."""


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


def parse_reviewers(value: Any) -> list[str] | None:
    if isinstance(value, list):
        reviewers = [str(item).strip() for item in value if str(item).strip()]
        return reviewers
    if isinstance(value, str):
        reviewers = [item.strip() for item in value.split(",") if item.strip()]
        return reviewers
    return None


def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}

    if "enabled" in raw:
        enabled = parse_bool(raw["enabled"])
        if enabled is None:
            raise ValueError("enabled must be a boolean")
        normalized["enabled"] = enabled

    reviewers_source = raw.get("reviewers", raw.get("reviewer"))
    reviewers = parse_reviewers(reviewers_source)
    if reviewers_source is not None:
        if reviewers is None:
            raise ValueError("reviewers must be a list or comma-separated string")
        normalized["reviewers"] = reviewers

    max_rounds_source = raw.get("maxRounds", raw.get("max_rounds"))
    if max_rounds_source is not None:
        try:
            max_rounds = int(max_rounds_source)
            if max_rounds <= 0:
                raise ValueError("maxRounds must be greater than zero")
            normalized["maxRounds"] = max_rounds
        except (TypeError, ValueError) as exc:
            raise ValueError("maxRounds must be a positive integer") from exc

    allow_self_source = raw.get("allowSelfReview", raw.get("allow_self_review"))
    if allow_self_source is not None:
        allow_self_review = parse_bool(allow_self_source)
        if allow_self_review is None:
            raise ValueError("allowSelfReview must be a boolean")
        normalized["allowSelfReview"] = allow_self_review

    return normalized


def load_json_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if not isinstance(loaded, dict):
            raise ValueError("must contain a JSON object")
        return normalize_config(loaded)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ConfigError(f"invalid {path}: {exc}") from exc


def env_overrides(env: dict[str, str]) -> dict[str, Any]:
    raw: dict[str, Any] = {}

    if "AUTO_REVIEW_ENABLED" in env:
        raw["enabled"] = env["AUTO_REVIEW_ENABLED"]
    if "AUTO_REVIEW_REVIEWERS" in env:
        raw["reviewers"] = env["AUTO_REVIEW_REVIEWERS"]
    elif "AUTO_REVIEW_REVIEWER" in env:
        raw["reviewers"] = env["AUTO_REVIEW_REVIEWER"]
    if "AUTO_REVIEW_MAX_ROUNDS" in env:
        raw["maxRounds"] = env["AUTO_REVIEW_MAX_ROUNDS"]
    if "AUTO_REVIEW_ALLOW_SELF_REVIEW" in env:
        raw["allowSelfReview"] = env["AUTO_REVIEW_ALLOW_SELF_REVIEW"]

    return normalize_config(raw)


def load_config(root: Path, env: dict[str, str]) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config.update(load_json_config(root / "env" / "review.json"))
    config.update(load_json_config(root / ".auto-review-config.json"))
    config.update(env_overrides(env))
    return config


def emit_shell(config: dict[str, Any]) -> str:
    reviewers = ",".join(config["reviewers"])
    reviewer = config["reviewers"][0] if len(config["reviewers"]) == 1 else ""
    values = {
        "AUTO_REVIEW_ENABLED": "true" if config["enabled"] else "false",
        "AUTO_REVIEW_REVIEWER": reviewer,
        "AUTO_REVIEW_REVIEWERS": reviewers,
        "AUTO_REVIEW_MAX_ROUNDS": str(config["maxRounds"]),
        "AUTO_REVIEW_ALLOW_SELF_REVIEW": "true" if config["allowSelfReview"] else "false",
    }
    return "\n".join(f"export {key}={shlex.quote(value)}" for key, value in values.items())


def main() -> int:
    parser = argparse.ArgumentParser(description="Load auto-code-review config")
    parser.add_argument("--root", default=".", help="Project root containing env/review.json")
    parser.add_argument("--shell", action="store_true", help="Emit shell exports instead of JSON")
    args = parser.parse_args()

    try:
        config = load_config(Path(args.root).resolve(), dict(os.environ))
    except (ConfigError, ValueError) as exc:
        print(f"[auto-review-config] {exc}", file=sys.stderr)
        return 2
    if args.shell:
        print(emit_shell(config))
    else:
        print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
