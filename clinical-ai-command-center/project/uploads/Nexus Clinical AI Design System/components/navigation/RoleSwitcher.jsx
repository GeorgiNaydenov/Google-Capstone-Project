import React from "react";

/**
 * RoleSwitcher — segmented control for toggling clinical views.
 * Active = primary fill; inactive = transparent on a container track.
 */
export function RoleSwitcher({ options = [], value, onChange, style }) {
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        background: "var(--surface-container)",
        border: "var(--border-width) solid var(--outline-variant)",
        borderRadius: "var(--radius-md)",
        padding: 2,
        gap: 2,
        ...style,
      }}
    >
      {options.map((opt) => {
        const active = opt === value;
        return (
          <button
            key={opt}
            onClick={() => onChange && onChange(opt)}
            style={{
              padding: "4px 12px",
              background: active ? "var(--primary)" : "transparent",
              color: active ? "var(--on-primary)" : "var(--on-surface-variant)",
              border: "none",
              borderRadius: "var(--radius-sm)",
              fontFamily: "var(--font-sans)",
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              cursor: "pointer",
              transition: "background-color 150ms ease, color 150ms ease",
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
