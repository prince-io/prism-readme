const fs = require("fs");
const path = require("path");
const { resolveTheme } = require("./_theme");

module.exports = (req, res) => {
  const theme = resolveTheme(String((req.query && req.query.theme) || ""));
  const rel = `${theme}.gif`;

  let buf;
  try {
    buf = fs.readFileSync(path.join(process.cwd(), "gifs", rel));
  } catch (err) {
    res.statusCode = 500;
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify({ error: "gif missing", file: rel }));
    return;
  }

  res.statusCode = 200;
  res.setHeader("Content-Type", "image/gif");
  res.setHeader("Cache-Control", "no-store, max-age=0");
  res.setHeader("CDN-Cache-Control", "no-store");
  res.setHeader("X-Banner-Theme", theme);
  res.setHeader("X-Robots-Tag", "noindex");
  res.end(req.method === "HEAD" ? undefined : buf);
};
