import React from "react";
import { Icon } from "../core/Icon.jsx";

/**
 * Panel — the core work-surface container. White bg, 1px border, 8px radius.
 * Optional bordered header (title + icon + trailing actions). No shadow.
 */
export function Panel({ title, icon, iconColor = "var(--on-surface-variant)", actions, children, bodyPadding = "var(--space-md)", style, bodyStyle }) {
  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        background: "var(--surface-container-lowest)",
        border: "var(--border-width) solid var(--outline-variant)",
        borderRadius: "var(--radius-lg)",
        overflow: "hidden",
        ...style,
      }}
    >
      {title && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "var(--space-sm) var(--space-md)",
            background: "var(--surface-container-low)",
            borderBottom: "var(--border-width) solid var(--outline-variant)",
          }}
        >
          <h2 style={{ margin: 0, display: "flex", alignItems: "center", gap: "var(--space-sm)", fontFamily: "var(--font-sans)", fontSize: "var(--type-panel-title-size)", fontWeight: 600, color: "var(--on-surface)" }}>
            {icon && <Icon name={icon} size={18} style={{ color: iconColor }} />}
            {title}
          </h2>
          {actions && <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>{actions}</div>}
        </div>
      )}
      <div style={{ padding: bodyPadding, ...bodyStyle }}>{children}</div>
    </section>
  );
}
