// Shared display formatters (Indian numbering). Used by the E7 impact/ROI cards.

/** Compact Indian-rupee formatting: ₹35,000 · ₹4.2 L · ₹88,426 cr · ₹3.67 lakh cr. */
export function inr(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  const a = Math.abs(n);
  if (a >= 1e12) return `₹${(n / 1e12).toFixed(2)} lakh cr`;
  if (a >= 1e7) {
    const cr = n / 1e7;
    return `₹${cr >= 100 ? Math.round(cr).toLocaleString("en-IN") : cr.toFixed(1)} cr`;
  }
  if (a >= 1e5) return `₹${(n / 1e5).toFixed(1)} L`;
  return `₹${Math.round(n).toLocaleString("en-IN")}`;
}

/** Integer with Indian thousands separators, or an em dash when missing. */
export function intfmt(n: number | null | undefined, dash = "—"): string {
  if (n == null || !Number.isFinite(n)) return dash;
  return Math.round(n).toLocaleString("en-IN");
}

/** Fixed-decimal number, or an em dash when missing. */
export function num(n: number | null | undefined, digits = 1, dash = "—"): string {
  if (n == null || !Number.isFinite(n)) return dash;
  return n.toFixed(digits);
}

const ACRONYMS = ["GRAP", "CPCB", "CAQM", "SWM", "NCAP", "PUC", "CTO", "OCEMS", "AQI", "PM2.5", "PM10"];

/** Turn a SHOUTING kb-chunk title into a readable rule name, keeping known acronyms. */
export function prettyRule(raw: string): string {
  let s = raw.replace(/\s*[—–-]\s*full text\.?\s*$/i, "").trim();
  if (s.length > 6 && s === s.toUpperCase()) {
    s = s.toLowerCase().replace(/\b[a-z]/g, (c) => c.toUpperCase());
    for (const a of ACRONYMS) {
      s = s.replace(new RegExp(`\\b${a[0]}${a.slice(1).toLowerCase()}\\b`, "g"), a);
    }
  }
  return s;
}

/**
 * Clean a stored enforcement rationale for display: the "Regulatory basis:"
 * tail is built from kb-chunk titles, which can repeat (two chunks of the same
 * document) and arrive in ALL CAPS with "— FULL TEXT" suffixes.
 */
export function cleanRationale(text: string): string {
  const m = text.match(/^([\s\S]*?)\s*Regulatory basis:\s*([\s\S]+?)\.?\s*$/);
  if (!m) return text;
  const rules: string[] = [];
  const seen = new Set<string>();
  for (const part of m[2].split(";")) {
    const rule = prettyRule(part);
    const key = rule.toLowerCase();
    if (rule && !seen.has(key)) {
      seen.add(key);
      rules.push(rule);
    }
  }
  return rules.length ? `${m[1].trim()} Regulatory basis: ${rules.join("; ")}.` : m[1].trim();
}
