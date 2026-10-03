#!/usr/bin/env python3
"""Fetch GitHub profile stats and normalize them into tools/stats_cache.json.

Sources (build-time only):
  * github-readme-stats  -> overall counts + top languages
  * streak-stats         -> total contributions, current/longest streak

The banner engine reads the cache and renders the data in our own layout;
nothing is fetched at render time.

Usage:
    python3 tools/stats.py cache
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

USER = "prince-io"
STATS_URL = (
    f"https://github-readme-stats.vercel.app/api?username={USER}"
    "&include_all_commits=true&count_private=true"
)
LANGS_URL = (
    f"https://github-readme-stats.vercel.app/api/top-langs/?username={USER}"
    "&include_all_commits=true&count_private=true&layout=compact"
)
STREAK_URL = f"https://streak-stats.demolab.com/?user={USER}"

TEXT = re.compile(r">([^<>]{1,80})</text>")
DATE = re.compile(r"[A-Z][a-z]{2} \d+ - ([A-Z][a-z]{2} \d+|Present)")


def fetch(url, tries=3):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(2)
    raise SystemExit(f"fetch failed: {url}: {last}")


def texts(svg):
    return [t.strip() for t in TEXT.findall(svg)]


def parse_overall(svg):
    out, pending = [], None
    for t in texts(svg):
        if t.endswith(":"):
            pending = t[:-1]
        elif pending is not None:
            out.append({"label": pending, "value": t})
            pending = None
    return out


def parse_langs(svg):
    out = []
    for t in texts(svg):
        m = re.fullmatch(r"(.+?)\s+([\d.]+)%", t)
        if m:
            out.append({"label": m.group(1), "value": f"{m.group(2)}%"})
    return out


def parse_streaks(svg):
    ts = texts(svg)
    numbers = [t for t in ts if re.fullmatch(r"\d+", t)]
    dates = [t for t in ts if DATE.fullmatch(t)]
    labels = [t for t in ts if "Streak" in t or "Contributions" in t]
    order = ["Total Contributions", "Current Streak", "Longest Streak"]
    labels = sorted(set(labels), key=lambda l: order.index(l) if l in order else 99)
    out = []
    for i, label in enumerate(order):
        value = numbers[i] if i < len(numbers) else "0"
        sub = dates[i] if i < len(dates) else ""
        if i == 0:  # total contributions is a count, streaks are day counts
            out.append({"label": label, "value": value, "sub": sub})
        else:
            out.append({"label": label, "value": value, "sub": sub, "unit": "days"})
    return out


def cache():
    data = {
        "overall": parse_overall(fetch(STATS_URL)),
        "streaks": parse_streaks(fetch(STREAK_URL)),
        "languages": parse_langs(fetch(LANGS_URL)),
    }
    target = ROOT / "tools" / "stats_cache.json"
    target.write_text(json.dumps(data, indent=1) + "\n")
    for key in data:
        print(f"  {key}: {len(data[key])}")
    print(f"wrote {target.relative_to(ROOT)}")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "cache":
        cache()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
