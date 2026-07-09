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
