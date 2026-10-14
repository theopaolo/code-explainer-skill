// Headless check of the site: screenshots + JS errors + horizontal overflow, desktop dark and phone light.
// Setup once in the work dir:  bun add playwright-core   (no browser download needed)
// Serve the page with the artifact-like skeleton: wrap the built HTML in
//   <!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>…</body></html>
// as preview.html next to its files, then `python3 -m http.server 4322` in that folder.
// Usage: bun screenshot.mjs http://localhost:4322/preview.html accueil probleme decouper ...
import { chromium } from "playwright-core";
import { existsSync, readdirSync } from "fs";
import { homedir } from "os";

function findChromium() {
  const cands = [
    process.env.CHROMIUM_PATH,
    "/Applications/Helium.app/Contents/MacOS/Helium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ];
  const cache = `${homedir()}/Library/Caches/ms-playwright`;
  if (existsSync(cache)) for (const d of readdirSync(cache).filter((d) => d.startsWith("chromium-")).sort().reverse())
    cands.push(`${cache}/${d}/chrome-mac/Chromium.app/Contents/MacOS/Chromium`, `${cache}/${d}/chrome-mac-arm64/Chromium.app/Contents/MacOS/Chromium`);
  return cands.find((p) => p && existsSync(p));
}
const [url, ...pages] = process.argv.slice(2);
const exe = findChromium();
if (!exe) { console.error("No Chromium-based browser found; set CHROMIUM_PATH."); process.exit(1); }
const b = await chromium.launch({ executablePath: exe, headless: true });
const errs = [];
for (const [name, w, h, scheme] of [["desktop-dark", 1400, 900, "dark"], ["phone-light", 400, 860, "light"]]) {
  for (const id of pages.length ? pages : ["accueil"]) {
    const p = await b.newPage({ viewport: { width: w, height: h }, colorScheme: scheme });
    p.on("pageerror", (e) => errs.push(`${name} #${id}: ${e.message}`));
    await p.goto(`${url}#${id}`); await p.waitForTimeout(800);
    await p.screenshot({ path: `shot-${name}-${id}.png`, fullPage: true });
    if (await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) errs.push(`${name} #${id}: horizontal overflow`);
    await p.close();
  }
}
console.log(errs.length ? errs.join("\n") : "no page errors, no overflow");
await b.close();
