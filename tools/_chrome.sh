# shellcheck shell=bash
# Sourced by renderers. If CHROME_PATH is set, point puppeteer at that browser
# instead of a downloaded one. Exposes $PUPPETEER_ARGS for mmdc.
PUPPETEER_ARGS=()
if [[ -n "${CHROME_PATH:-}" ]]; then
  _cfg="$(mktemp)"
  printf '{"executablePath":"%s","args":["--no-sandbox"]}\n' "$CHROME_PATH" > "$_cfg"
  PUPPETEER_ARGS=(-p "$_cfg")
fi
