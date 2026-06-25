import React from "react";

/**
 * Textarea — multi-line natural-language input (agent queries, notes).
 */
export function Textarea({ rows = 4, invalid = false, style, ...rest }) {
  return (
    <textarea
      rows={rows}
      style={{
        width: "100%",
        padding: "var(--space-sm)",
        background: "var(--surface-container-lowest)",
        color: "var(--on-surface)",
        border: `var(--border-width) solid ${invalid ? "var(--error)" : "var(--outline-variant)"}`,
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--type-body-size)",
        lineHeight: "var(--type-body-line)",
        outline: "none",
        resize: "vertical",
        boxSizing: "border-box",
        transition: "border-color 150ms ease",
        ...style,
      }}
      onFocus={(e) => { e.currentTarget.style.borderColor = "var(--primary)"; }}
      onBlur={(e) => { e.currentTarget.style.borderColor = invalid ? "var(--error)" : "var(--outline-variant)"; }}
      {...rest}
    />
  );
}
