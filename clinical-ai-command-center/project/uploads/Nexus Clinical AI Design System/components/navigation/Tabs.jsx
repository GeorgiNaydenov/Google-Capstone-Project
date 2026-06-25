import React from "react";

/**
 * Tabs — underline-style tab bar for work-surface sections.
 * Active tab: primary text + 2px primary underline.
 */
export function Tabs({ tabs = [], value, onChange, style }) {
  return (
    <div style={{ display: "flex", gap: "var(--space-md)", borderBottom: "var(--border-width) solid var(--outline-variant)", ...style }}>
      {tabs.map((tab) => {
        const active = tab === value;
        return (
          <button
            key={tab}
            onClick={() => onChange && onChange(tab)}
            style={{
              padding: "8px 16px",
              background: "transparent",
              color: active ? "var(--primary)" : "var(--on-surface-variant)",
              border: "none",
              borderBottom: `2px solid ${active ? "var(--primary)" : "transparent"}`,
              marginBottom: -1,
              fontFamily: "var(--font-sans)",
              fontSize: "var(--type-panel-title-size)",
              fontWeight: 600,
              cursor: "pointer",
              transition: "color 150ms ease, border-color 150ms ease",
            }}
          >
            {tab}
          </button>
        );
      })}
    </div>
  );
}
