const THEMES = [
  "light", "solarized-light", "paper", "mint", "lavender", "rose",
  "dracula", "nord", "tokyo-night", "neon", "forest", "volcano",
  "minecraft",
];

const WINDOW_MS = Math.max(1000, Number(process.env.THEME_WINDOW_MS) || 60000);

function pickTheme(now) {
  return THEMES[Math.floor(now / WINDOW_MS) % THEMES.length];
}

function resolveTheme(override) {
  return THEMES.includes(override) ? override : pickTheme(Date.now());
}

module.exports = { THEMES, WINDOW_MS, pickTheme, resolveTheme };
