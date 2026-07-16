"use client";
// Inline citation component — renders a superscript link that shows the source on hover/click.
// Usage in chapter prose: <Cite id="C002" lang={lang} /> after the relevant claim.

import { CLAIMS, SOURCES } from "../data/claims.mjs";

export default function Cite({ id, lang }) {
  const claim = CLAIMS.find((c) => c.id === id);
  if (!claim) return null;
  const src = SOURCES.find((s) => s.id === claim.source_id);
  if (!src) return null;
  const vi = lang === "vi";
  const tooltipText = vi
    ? `${claim.claim}\n\nNguồn: ${src.title} — ${src.organization} (${src.source_type}).\nĐộ tin cậy: ${claim.confidence}.`
    : `${claim.claim}\n\nSource: ${src.title} — ${src.organization} (${src.source_type}).\nConfidence: ${claim.confidence}.`;
  return (
    <a
      href={`/claims#${id}`}
      className="cite"
      title={tooltipText}
      data-source={tooltipText}
      style={{
        fontSize: "0.7em",
        verticalAlign: "super",
        color: "var(--accent)",
        textDecoration: "none",
        marginLeft: 2,
        fontWeight: 600,
      }}
    >
      [{id}]
    </a>
  );
}
