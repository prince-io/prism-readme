const fs = require("fs");
const path = require("path");
const { resolveTheme } = require("../_theme");

const BANNERS = new Set([
  "header", "about", "focus-areas", "tech-stack",
  "github-stats", "skyline", "thanks",
]);

function send(res, status, headers, body) {
  res.statusCode = status;
  for (const [k, v] of Object.entries(headers)) res.setHeader(k, v);
  res.end(body);
}

module.exports = (req, res) => {
  const name = String((req.query && req.query.name) || "").toLowerCase();
  if (!BANNERS.has(name)) {
    send(res, 404, { "Content-Type": "application/json" }, JSON.stringify({ error: "unknown banner", name }));
    return;
  }

  const theme = resolveTheme(String((req.query && req.query.theme) || ""));
  const rel = `${name}-${theme}.svg`;

  let svg;
  try {
    svg = fs.readFileSync(path.join(process.cwd(), "assets", rel));
  } catch (err) {
    send(res, 500, { "Content-Type": "application/json" }, JSON.stringify({ error: "asset missing", file: rel }));
    return;
  }

  send(res, 200, {
    "Content-Type": "image/svg+xml; charset=utf-8",
    "Cache-Control": "no-store, max-age=0",
    "CDN-Cache-Control": "no-store",
    "X-Banner-Theme": theme,
    "X-Robots-Tag": "noindex",
  }, req.method === "HEAD" ? undefined : svg);
};
