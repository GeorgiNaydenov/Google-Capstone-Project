import React from "react";
import { Icon } from "../core/Icon.jsx";

const TONES = {
  critical: { fg: "var(--error)", bg: "var(--error-container)", bd: "var(--error)" },
  warning: { fg: "var(--tertiary)", bg: "var(--tertiary-fixed)", bd: "var(--tertiary)" },
  stable: { fg: "var(--primary)", bg: "var(--primary-fixed)", bd: "var(--primary)" },
  verified: { fg: "var(--on-success-container)", bg: "var(--success-container)", bd: "var(--success)" },
  info: { fg: "var(--on-secondary-fixed-variant)", bg: "var(--secondary-fixed)", bd: "var(--secondary)" },
  neutral: { fg: "var(--on-surface-variant)", bg: "var(--surface-variant)", bd: "var(--outline-variant)" },
};

/**
 * StatusChip — compact status indicator. Tonal bg, solid text, hairline border.
 * Tones: critical | warning | stable | verified | info | neutral.
 */
export function StatusChip({ children, tone = "neutral", icon, style, ...rest }) {
  const t = TONES[tone] || TONES.neutral;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-xs)",
        padding: "2px 8px",
        background: t.bg,
        color: t.fg,
        border: `var(--border-width) solid color-mix(in srgb, ${t.bd} 25%, transparent)`,
        borderRadius: "var(--radius-sm)",
        fontFamily: "var(--font-sans)",
        fontSize: "10px",
        fontWeight: "var(--weight-bold)",
        lineHeight: "16px",
        letterSpacing: "0.05em",
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        ...style,
      }}
      {...rest}
    >
      {icon && <Icon name={icon} size={14} />}
      {children}
    </span>
  );
}
