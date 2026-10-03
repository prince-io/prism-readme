#!/usr/bin/env python3
"""Daily GitHub contributions + isometric geometry for the Contribution
Skyline banner (ported from components/Component.tsx).

    python3 tools/skyline.py cache    # refresh tools/contrib_cache.json

The banner engine (tools/banner.py) imports the pure functions below and
renders the graph; nothing is fetched at render time.
"""

import json
import math
import sys
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER = "prince-io"
API = f"https://github-contributions-api.jogruber.de/v4/{USER}?y=last"

YAW_3D = math.pi / 4
ELEV_3D = (34 * math.pi) / 180


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


def cache():
    data = json.loads(fetch(API))
    days = [
        {"date": d["date"], "count": int(d["count"])}
        for d in data.get("contributions", [])
    ]
    if not days:
        raise SystemExit("no contributions returned")
    out = {"end": days[-1]["date"], "days": days}
    target = ROOT / "tools" / "contrib_cache.json"
    target.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    print(f"wrote {target.relative_to(ROOT)} ({len(days)} days, {data.get('total')})")


# --- geometry (ported from Component.tsx) -----------------------------------

def _jsday(d):
    return (d.weekday() + 1) % 7  # 0 = Sunday


def level_of(count, busy):
    if count <= 0:
        return 0
    if busy <= 0:
        return 4
    return 1 + min(3, int((count / busy) * 4))


def build_grid(days, end, week_start=0):
    counts = {}
    for d in days:
        counts[d["date"]] = counts.get(d["date"], 0) + int(d["count"])
    end_d = date.fromisoformat(end)
    start = end_d - timedelta(days=364)
    start -= timedelta(days=(_jsday(start) - week_start) % 7)
    cells = []
    d = start
    i = 0
    while d <= end_d:
        key = d.isoformat()
        cells.append(
            {"date": key, "count": counts.get(key, 0), "level": 0,
             "week": i // 7, "day": i % 7}
        )
        d += timedelta(days=1)
        i += 1
    nz = sorted(c["count"] for c in cells if c["count"] > 0)
    busy = nz[int(0.95 * (len(nz) - 1))] if nz else 0
    for c in cells:
        c["level"] = level_of(c["count"], busy)
    weeks = cells[-1]["week"] + 1 if cells else 0
    return {"cells": cells, "weeks": weeks, "max": nz[-1] if nz else 0}


def bar_height(count, max_count, scale=1.0):
    if count > 0 and max_count > 0:
        return 0.4 + (count / max_count) ** 0.85 * 7.2 * scale
    return 0.2


def camera(e, d_yaw=0.0, d_elev=0.0):
    yaw = min(82 * math.pi / 180, max(0.0, (YAW_3D + d_yaw) * e))
    elev = (math.pi / 2) + (min(62 * math.pi / 180, max(18 * math.pi / 180, ELEV_3D + d_elev)) - math.pi / 2) * e
    return {"cs": math.cos(yaw), "sn": math.sin(yaw),
            "se": math.sin(elev), "ce": math.cos(elev)}


def project(cam, x, y, z):
    return (
        x * cam["cs"] - y * cam["sn"],
        (x * cam["sn"] + y * cam["cs"]) * cam["se"] - z * cam["ce"],
    )


def shade(hexv, k):
    h = hexv.lstrip("#")
    rgb = [min(255, round(int(h[i:i + 2], 16) * k)) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(rgb)


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "cache":
        cache()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
