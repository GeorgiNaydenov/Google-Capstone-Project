import React from "react";

/**
 * EvidenceCitation — bordered source callout for AI-synthesized claims.
 * Superscript index, source snippet, "View Source" link.
 */
export function EvidenceCitation({ index = 1, snippet, sourceLabel = "View Source", onView, style }) {
  return (
    <div
      style={{
        position: "relative",
        paddingLeft: "var(--space-xl)",
        padding: "var(--space-sm) var(--space-sm) var(--space-sm) var(--space-xl)",
        background: "var(--surface-container-low)",
        border: "var(--border-width) solid var(--outline-variant)",
        borderRadius: "var(--radius-md)",
        ...style,
      }}
    >
      <span
        style={{
          position: "absolute",
          left: "var(--space-sm)",
          top: "var(--space-sm)",
          width: 16,
          height: 16,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "var(--radius-full)",
          background: "var(--primary-fixed)",
          color: "var(--primary)",
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          fontWeight: 700,
        }}
      >
        {index}
      </span>
      <p style={{ margin: 0, marginBottom: 4, fontFamily: "var(--font-sans)", fontSize: "12px", lineHeight: "16px", color: "var(--on-surface)" }}>
        {snippet}
      </p>
      <a
        href="#"
        onClick={(e) => { e.preventDefault(); onView && onView(); }}
        style={{ fontFamily: "var(--font-sans)", fontSize: "11px", fontWeight: 600, color: "var(--primary)", textDecoration: "none" }}
      >
        {sourceLabel} →
      </a>
    </div>
  );
}
