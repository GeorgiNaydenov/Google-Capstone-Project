import React from "react";
import { Icon } from "../core/Icon.jsx";

/**
 * Select — native dropdown styled to the system. 36px compact by default.
 */
export function Select({ size = "sm", children, style, ...rest }) {
  const height = size === "sm" ? "var(--row-height-sm)" : "var(--row-height-md)";
  return (
    <div style={{ position: "relative", width: "100%" }}>
      <select
        style={{
          width: "100%",
          height,
          padding: "0 32px 0 12px",
          background: "var(--surface-container-lowest)",
          color: "var(--on-surface)",
          border: "var(--border-width) solid var(--outline-variant)",
          borderRadius: "var(--radius-md)",
          fontFamily: "var(--font-sans)",
          fontSize: "var(--type-table-size)",
          appearance: "none",
          outline: "none",
          cursor: "pointer",
          boxSizing: "border-box",
          ...style,
        }}
        {...rest}
      >
        {children}
      </select>
      <Icon
        name="expand_more"
        size={18}
        style={{
          position: "absolute",
          right: "var(--space-sm)",
          top: "50%",
          transform: "translateY(-50%)",
          color: "var(--on-surface-variant)",
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
