import React from "react";

/**
 * ConfidenceMeter — linear gauge for AI confidence / completeness.
 * Thin 4px track, colored fill keyed to value, numeric readout.
 * Auto-colors: >=90 success, >=70 primary, >=50 warning, else critical.
 */
export function ConfidenceMeter({ value = 0, label, width = 96, showValue = true, color, style }) {
  const v = Math.max(0, Math.min(100, value));
  const fill = color || (v >= 90 ? "var(--success)" : v >= 70 ? "var(--primary)" : v >= 50 ? "var(--tertiary)" : "var(--error)");
  const numColor = color || (v >= 90 ? "var(--on-success-container)" : v >= 70 ? "var(--primary)" : v >= 50 ? "var(--tertiary)" : "var(--error)");
  return (
    <div style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-sm)", ...style }}>
      {label && (
        <span style={{ fontFamily: "var(--font-sans)", fontSize: "11px", fontWeight: 600, color: "var(--on-surface-variant)" }}>
          {label}
        </span>
      )}
      <div style={{ width, height: 4, background: "var(--surface-variant)", borderRadius: "var(--radius-full)", overflow: "hidden" }}>
        <div style={{ width: `${v}%`, height: "100%", background: fill, transition: "width 300ms ease" }} />
      </div>
      {showValue && (
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "11px", fontWeight: 700, color: numColor }}>{v}%</span>
      )}
    </div>
  );
}
