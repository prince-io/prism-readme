#!/usr/bin/env python3
"""Fetch shields.io badges and normalize them into inline, self-contained SVG.

GitHub strips external refs and data-URI <image> logos from SVG. This tool
fetches a badge, decodes the data-URI logo, and re-emits it as an inline
<path> group, so the badge body can live inside a banner with no external
references.

Usage:
    python3 tools/badges.py cache           # refresh badges_cache.json
    python3 tools/badges.py show <url>      # print the normalized badge body
"""

import base64
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

IMAGE = re.compile(r"<image\b[^>]*?/>", re.S)
ATTR = re.compile(r'([a-zA-Z:_-]+)="([^"]*)"')
DATA_B64 = re.compile(r"data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=20).read().decode("utf-8")


def decode_data_uri(uri):
    m = DATA_B64.search(uri)
    if m:
        return base64.b64decode(m.group(1)).decode("utf-8", "replace")
    if uri.startswith("data:image/svg+xml,"):
        return urllib.parse.unquote(uri.split(",", 1)[1])
    return None


def viewbox(inner):
    m = re.search(r'viewBox="([^"]+)"', inner)
    if not m:
        return 0.0, 0.0, 24.0, 24.0
    nums = [float(n) for n in re.split(r"[ ,]+", m.group(1).strip())]
    return tuple(nums) if len(nums) == 4 else (0.0, 0.0, 24.0, 24.0)


def extract_paths(inner):
    default = None
    m = re.search(r"<svg\b[^>]*\bfill=\"([^\"]+)\"", inner)
    if m:
        default = m.group(1)
    paths = []
    for pm in re.finditer(r"<path\b([^>]*?)/?>", inner, re.S):
        attrs = pm.group(1)
        d = re.search(r'\bd="([^"]+)"', attrs)
        f = re.search(r'\bfill="([^"]+)"', attrs)
        if d:
            paths.append((d.group(1), f.group(1) if f else (default or "#ffffff")))
    return paths


def logo_group(inner, x, y, w, h):
    vx, vy, vw, vh = viewbox(inner)
    sx, sy = w / vw, h / vh
    body = "".join(f'<path d="{d}" fill="{f}"/>' for d, f in extract_paths(inner))
    return (
        f'<g transform="translate({x},{y}) scale({sx:.5f},{sy:.5f}) '
        f'translate({-vx},{-vy})">{body}</g>'
    )


def split_svg(text):
    m = re.search(r"<svg\b[^>]*>(.*)</svg>", text, re.S)
    return m.group(1) if m else text


def dimensions(text):
    w = re.search(r'\bwidth="([\d.]+)"', text)
    h = re.search(r'\bheight="([\d.]+)"', text)
    return float(w.group(1)), float(h.group(1))


def normalize(text):
    """Return (width, height, raw_body, normalized_body)."""
    w, h = dimensions(text)
    raw = split_svg(text)

    def repl(match):
        tag = match.group(0)
        a = dict(ATTR.findall(tag))
        href = a.get("href") or a.get("xlink:href") or ""
        inner = decode_data_uri(href)
        if not inner:
            return ""
        x = float(a.get("x", 0))
        y = float(a.get("y", 0))
        iw = float(a.get("width", 0))
        ih = float(a.get("height", 0))
        return logo_group(inner, x, y, iw, ih)

    norm = IMAGE.sub(repl, raw)
    return w, h, raw, norm


_BADGE = "https://img.shields.io/badge/"

# The tech-stack badges from README.md, slug -> shields.io URL.
REGISTRY = {
    "html5": _BADGE + "html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white",
    "css3": _BADGE + "css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white",
    "react": _BADGE + "react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB",
    "nextjs": _BADGE + "Next-black?style=for-the-badge&logo=next.js&logoColor=white",
    "tailwindcss": _BADGE + "tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white",
    "daisyui": _BADGE + "daisyui-5A0EF8?style=for-the-badge&logo=daisyui&logoColor=white",
    "gsap": _BADGE + "gsap-%230AE448.svg?style=for-the-badge&logo=gsap&logoColor=white",
    "nodejs": _BADGE + "node.js-6DA55F.svg?style=for-the-badge&logo=node.js&logoColor=white",
    "expressjs": _BADGE + "express.js-%23404d59.svg?style=for-the-badge&logo=express&logoColor=%2361DAFB",
    "fastapi": _BADGE + "FastAPI-005571?style=for-the-badge&logo=fastapi",
    "mongodb": _BADGE + "MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white",
    "mysql": _BADGE + "mysql-4479A1.svg?style=for-the-badge&logo=mysql&logoColor=white",
    "postgres": _BADGE + "postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white",
    "redis": _BADGE + "redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white",
    "supabase": _BADGE + "Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white",
    "tensorflow": _BADGE + "TensorFlow-%23FF6F00.svg?style=for-the-badge&logo=TensorFlow&logoColor=white",
    "pytorch": _BADGE + "PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white",
    "keras": _BADGE + "Keras-%23D00000.svg?style=for-the-badge&logo=Keras&logoColor=white",
    "scikit-learn": _BADGE + "scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white",
    "numpy": _BADGE + "numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white",
    "pandas": _BADGE + "pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white",
    "matplotlib": _BADGE + "Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black",
    "deepseek": _BADGE + "DeepSeek-%235786FE.svg?style=for-the-badge&logo=deepseek&logoColor=white",
    "langchain": _BADGE + "langchain-%231C3C3C.svg?style=for-the-badge&logo=langchain&logoColor=white",
    "huggingface": _BADGE + "huggingface-%23FFD21E.svg?style=for-the-badge&logo=huggingface&logoColor=white",
    "ollama": _BADGE + "ollama-%23000000.svg?style=for-the-badge&logo=ollama&logoColor=white",
    "yolo": _BADGE + "YOLO-%23111F68.svg?style=for-the-badge&logo=yolo&logoColor=white",
    "java": _BADGE + "java-%23ED8B00.svg?style=for-the-badge&logo=openjdk&logoColor=white",
    "javascript": _BADGE + "javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E",
    "typescript": _BADGE + "typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white",
    "python": _BADGE + "python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54",
    "c": _BADGE + "c-%2300599C.svg?style=for-the-badge&logo=c&logoColor=white",
    "cpp": _BADGE + "c++-%2300599C.svg?style=for-the-badge&logo=c%2B%2B&logoColor=white",
    "latex": _BADGE + "latex-%23008080.svg?style=for-the-badge&logo=latex&logoColor=white",
    "git": _BADGE + "git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white",
    "github": _BADGE + "github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white",
    "inkscape": _BADGE + "Inkscape-e0e0e0?style=for-the-badge&logo=inkscape&logoColor=080A13",
    "postman": _BADGE + "Postman-FF6C37?style=for-the-badge&logo=postman&logoColor=white",
    "markdown": _BADGE + "markdown-%23000000.svg?style=for-the-badge&logo=markdown&logoColor=white",
    "vercel": _BADGE + "vercel-%23000000.svg?style=for-the-badge&logo=vercel&logoColor=white",
    "docker": _BADGE + "docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white",
    "cloudflare": _BADGE + "Cloudflare-F38020?style=for-the-badge&logo=Cloudflare&logoColor=white",
    "opencode": _BADGE + "opencode-%23000000.svg?style=for-the-badge&logo=opencode&logoColor=ffffff",
    "visual-studio-code": _BADGE + "visual%20studio%20code-%230078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white",
    "linux-mint": _BADGE + "Linux%20Mint-%2387CF3E.svg?style=for-the-badge&logo=Linux%20Mint&logoColor=white",
}


def cache():
    data = {}
    for slug, url in REGISTRY.items():
        w, h, _, norm = normalize(fetch(url))
        data[slug] = {"w": w, "h": h, "body": norm.strip()}
        print(f"  {slug:14} {w}x{h}")
    target = ROOT / "tools" / "badges_cache.json"
    target.write_text(json.dumps(data, indent=1) + "\n")
    print(f"wrote {target.relative_to(ROOT)} ({len(data)} badges)")

def main():
    if sys.argv[1:2] == ["cache"]:
        cache()
    elif sys.argv[1:2] == ["show"] and len(sys.argv) > 2:
        w, h, _, norm = normalize(fetch(sys.argv[2]))
        print(f"<!-- {w}x{h} -->\n{norm.strip()}")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
