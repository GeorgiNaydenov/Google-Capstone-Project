import React from "react";

/**
 * SQLPreview — transparency block for AI-generated SQL.
 * Mono font, container background, optional copy affordance.
 * Pass `html` for pre-highlighted markup, or `code` for plain text.
 */
export function SQLPreview({ code, html, label = "Generated SQL", onCopy, style }) {
  return (
    <div style={{ ...style }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--space-xs)" }}>
        <span style={{ fontFamily: "var(--font-sans)", fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--on-surface-variant)" }}>
          {label}
        </span>
        <button
          onClick={onCopy}
          style={{ display: "inline-flex", alignItems: "center", gap: 4, background: "none", border: "none", cursor: "pointer", color: "var(--primary)", fontFamily: "var(--font-sans)", fontSize: "11px", fontWeight: 600 }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: 14 }}>content_copy</span> Copy
        </button>
      </div>
      <pre
        style={{
          margin: 0,
          padding: "var(--space-sm)",
          background: "var(--surface-container-highest)",
          border: "var(--border-width) solid var(--outline-variant)",
          borderRadius: "var(--radius-md)",
          overflowX: "auto",
          fontFamily: "var(--font-mono)",
          fontSize: "12px",
          lineHeight: 1.5,
          color: "var(--on-surface)",
        }}
        {...(html ? { dangerouslySetInnerHTML: { __html: html } } : {})}
      >
        {html ? undefined : code}
      </pre>
    </div>
  );
}
