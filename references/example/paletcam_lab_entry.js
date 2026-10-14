import { ColorCutQuantizer } from "/Users/theogoedert/Documents/Webworks/5-ludique-dev/1-creative-coding/paletcam/src/modules/color-cut-quantizer.js";
import { selectPaletteCandidates } from "/Users/theogoedert/Documents/Webworks/5-ludique-dev/1-creative-coding/paletcam/src/modules/hybrid-selector.js";
import { packImageDataToArgb8888, computePixelStride } from "/Users/theogoedert/Documents/Webworks/5-ludique-dev/1-creative-coding/paletcam/src/modules/palette-pixel-pack.js";
import { rgbToOklab, oklabToRgb } from "/Users/theogoedert/Documents/Webworks/5-ludique-dev/1-creative-coding/paletcam/src/modules/color-space-oklch.js";
import { findClosestRAL } from "/Users/theogoedert/Documents/Webworks/5-ludique-dev/1-creative-coding/paletcam/src/modules/color-matching-ral.js";

const toRgb = (argb) => ({ r: (argb >>> 16) & 0xff, g: (argb >>> 8) & 0xff, b: argb & 0xff });

// Mirrors buildCandidates in hybrid-selector.js (not exported there).
export function buildCandidates(swatches) {
  return swatches.filter((s) => s && typeof s.rgb === "number").map((s) => {
    const meanRgb = toRgb(s.rgb);
    const vividRgb = toRgb(s.vividRgb ?? s.rgb);
    const m = rgbToOklab(meanRgb.r, meanRgb.g, meanRgb.b);
    const v = rgbToOklab(vividRgb.r, vividRgb.g, vividRgb.b);
    return { meanRgb, vividRgb, L: m.L, a: m.a, b: m.b, c: Math.hypot(m.a, m.b), vividLab: v, vividC: Math.hypot(v.a, v.b), mass: s.population ?? 0 };
  });
}

// Same steps as selectPaletteHybrid, with every stage kept for display.
export function runPipeline(data, w, h, count, params = {}) {
  const maxPixels = params.maxQuantizerPixels ?? 46000;
  const stride = computePixelStride(w, h, maxPixels);
  const packed = packImageDataToArgb8888(data, w, h, { maxPixels });
  const sampleCount = packed.length;
  const pool = Math.max(count, params.quantizedPoolSize ?? 55);
  const q = new ColorCutQuantizer(packed, pool, { centroidSpace: "oklab" });
  const swatches = q.getQuantizedColors?.() ?? [];
  const candidates = buildCandidates(swatches);
  const result = selectPaletteCandidates(candidates, count, params);
  return { stride, sampleCount, candidates, ...result, allCandidates: candidates };
}

globalThis.PaletLab = { runPipeline, buildCandidates, rgbToOklab, oklabToRgb, findClosestRAL };
