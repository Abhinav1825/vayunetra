"""Dependency-free PDF generator for enforcement notices.  Owner: Abhinav lane.

Renders the draft notice text (from ``_build_notice_text``) into a single-page
A4 PDF using only the standard library — no reportlab/fpdf, so it runs on the
Render backend without extra packages. Good enough for an officer-review draft.
"""
from __future__ import annotations

import textwrap


def _escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def notice_pdf_bytes(text: str) -> bytes:
    """Build a minimal, valid single-page A4 PDF from plain text."""
    # Wrap on explicit newlines, then soft-wrap long lines to the page width.
    lines: list[str] = []
    for raw in text.split("\n"):
        if raw.strip() == "":
            lines.append("")
        else:
            lines.extend(textwrap.wrap(raw, width=95) or [""])

    # Build the content stream: 11pt Helvetica, 14pt leading, top-left origin.
    parts = ["BT", "/F1 11 Tf", "50 800 Td", "14 TL"]
    for ln in lines:
        safe = _escape(ln.encode("latin-1", "replace").decode("latin-1"))
        parts.append(f"({safe}) Tj T*")
    parts.append("ET")
    content = "\n".join(parts).encode("latin-1", "replace")

    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]

    out = b"%PDF-1.4\n"
    offsets: list[int] = []
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(out)
    size = len(objs) + 1
    out += b"xref\n0 " + str(size).encode() + b"\n"
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += ("%010d 00000 n \n" % off).encode()
    out += (
        b"trailer\n<< /Size " + str(size).encode() + b" /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_pos).encode() + b"\n%%EOF"
    )
    return out
