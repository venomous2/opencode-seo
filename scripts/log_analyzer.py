"""Server log analyser for the OpenCode SEO Suite.

Parses Apache/Nginx access logs (combined/common format) and reports search
engine crawler behaviour: which bots visit, what they crawl, status codes
they hit, and where crawl budget is being wasted.

Usage:
    python scripts/log_analyzer.py --file access.log [--top 25]
    type access.log | python scripts/log_analyzer.py            # stdin
    python scripts/log_analyzer.py --file access.log --bot Googlebot --pretty

Output (JSON): per-bot totals, top crawled paths, status distribution,
parameter-URL share (crawl waste signal), and a daily timeline.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Combined LogFormat: ip - - [time] "request" status bytes "referer" "ua"
LOG_RE = re.compile(
    r'^\S+ \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" '
    r'(?P<status>\d{3}) (?P<bytes>\S+) "(?P<referer>[^"]*)" "(?P<ua>[^"]*)"')

BOT_SIGNATURES = {
    "Googlebot": ["googlebot"],
    "Googlebot-Mobile": ["googlebot-mobile", "googlebot/2.1"],
    "Bingbot": ["bingbot"],
    "GPTBot": ["gptbot"],
    "OAI-SearchBot": ["oai-searchbot"],
    "ClaudeBot": ["claudebot"],
    "PerplexityBot": ["perplexitybot"],
    "Google-Extended": ["google-extended"],
    "CCBot": ["ccbot"],
    "AhrefsBot": ["ahrefsbot"],
    "SemrushBot": ["semrushbot"],
    "Bytespider": ["bytespider"],
}


def detect_bot(user_agent: str) -> str | None:
    ua = user_agent.lower()
    for bot, signatures in BOT_SIGNATURES.items():
        if any(sig in ua for sig in signatures):
            return bot
    return None


def parse_lines(lines: list[str]) -> dict[str, Any]:
    bot_hits: Counter[str] = Counter()
    bot_paths: dict[str, Counter[str]] = defaultdict(Counter)
    bot_status: dict[str, Counter[str]] = defaultdict(Counter)
    daily: Counter[str] = Counter()
    param_hits: Counter[str] = Counter()
    total = 0
    unparsed = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue
        total += 1
        match = LOG_RE.match(line)
        if not match:
            unparsed += 1
            continue
        bot = detect_bot(match.group("ua"))
        if not bot:
            continue
        request = match.group("request")
        parts = request.split()
        path = parts[1] if len(parts) >= 2 else "/"
        status = match.group("status")
        day = match.group("time")[0:11]  # 18/Jul/2026

        bot_hits[bot] += 1
        bot_paths[bot][path] += 1
        bot_status[bot][status] += 1
        daily[day] += 1
        if "?" in path:
            param_hits[bot] += 1

    result: dict[str, Any] = {
        "lines_total": total,
        "lines_unparsed": unparsed,
        "bot_requests_total": sum(bot_hits.values()),
        "bots": {},
        "daily_bot_hits": dict(sorted(daily.items())),
    }
    for bot in bot_hits:
        hits = bot_hits[bot]
        result["bots"][bot] = {
            "hits": hits,
            "share_pct": round(100 * hits / max(sum(bot_hits.values()), 1), 1),
            "status_distribution": dict(bot_status[bot].most_common()),
            "parameter_url_pct": round(100 * param_hits[bot] / hits, 1),
        }
    return result, bot_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="log_analyzer",
                                     description="Search-crawler log analyser")
    parser.add_argument("--file", help="path to access log (omit to read stdin)")
    parser.add_argument("--top", type=int, default=25,
                        help="top N crawled paths per bot")
    parser.add_argument("--bot", help="restrict output to one bot (e.g. Googlebot)")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            print(json.dumps({"error": f"File not found: {path}"}))
            return 1
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    else:
        lines = sys.stdin.read().splitlines()

    result, bot_paths = parse_lines(lines)
    if args.bot:
        result["bots"] = {args.bot: result["bots"].get(args.bot)} \
            if args.bot in result["bots"] else {}
    result["top_paths_per_bot"] = {
        bot: paths.most_common(args.top)
        for bot, paths in bot_paths.items()
        if not args.bot or bot == args.bot
    }
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
