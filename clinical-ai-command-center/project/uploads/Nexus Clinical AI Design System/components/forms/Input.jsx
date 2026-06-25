import React from "react";
import { Icon } from "../core/Icon.jsx";

/**
 * Input — text field. 1px outline, 6px radius, focus = primary border.
 * Optional leading icon. Sizes: sm (36px) | md (44px).
 */
export function Input({ size = "md", icon, invalid = false, style, ...rest }) {
  const height = size === "sm" ? "var(--row-height-sm)" : "var(--row-height-md)";
  return (
    <div style={{ position: "relative", width: "100%" }}>
      {icon && (
        <Icon
          name={icon}
          size={18}
          style={{
            position: "absolute",
            left: "var(--space-sm)",
            top: "50%",
            transform: "translateY(-50%)",
            color: "var(--on-surface-variant)",
            pointerEvents: "none",
          }}
        />
      )}
      <input
        style={{
          width: "100%",
          height,
          padding: icon ? "0 12px 0 32px" : "0 12px",
          background: "var(--surface-container-lowest)",
          color: "var(--on-surface)",
          border: `var(--border-width) solid ${invalid ? "var(--error)" : "var(--outline-variant)"}`,
          borderRadius: "var(--radius-md)",
          fontFamily: "var(--font-sans)",
          fontSize: "var(--type-body-size)",
          lineHeight: "var(--type-body-line)",
          outline: "none",
          boxSizing: "border-box",
          transition: "border-color 150ms ease",
          ...style,
        }}
        onFocus={(e) => { e.currentTarget.style.borderColor = "var(--primary)"; e.currentTarget.style.boxShadow = "inset 0 0 0 1px var(--primary)"; }}
        onBlur={(e) => { e.currentTarget.style.borderColor = invalid ? "var(--error)" : "var(--outline-variant)"; e.currentTarget.style.boxShadow = "none"; }}
        {...rest}
      />
    </div>
  );
}
