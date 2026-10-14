#!/usr/bin/env bash
# Bundle the project's REAL modules into one IIFE file for the explainer site.
# Usage: bundle_lab.sh <entry.js> <out.js>   (run from the project root so imports resolve)
# The entry must end with:  globalThis.Lab = { fnA, fnB, ... };
# (bun's --global-name is unreliable for iife; assigning globalThis explicitly always works.)
# Test the bundle headlessly before using it:
#   bun -e 'new Function(require("fs").readFileSync("out.js","utf8"))(); console.log(Object.keys(globalThis.Lab))'
set -euo pipefail
ENTRY="$1"; OUT="$2"
if command -v bun >/dev/null; then
  bun build "$ENTRY" --format=iife --minify --outfile="$OUT"
else
  npx --yes esbuild "$ENTRY" --bundle --format=iife --minify --outfile="$OUT"
fi
ls -la "$OUT"
