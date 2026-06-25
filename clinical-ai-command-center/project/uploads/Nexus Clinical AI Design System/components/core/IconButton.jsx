import React from "react";
import { Icon } from "./Icon.jsx";

/**
 * IconButton — square, icon-only action. Used in app bars and panel headers.
 * Subtle tonal hover; no shadow. Sizes: sm (28px) | md (32px).
 */
export function IconButton({ icon, size = "md", label, active = false, disabled = false, style, ...rest }) {
  const dim = size === "sm" ? 28 : 32;
  return (
    <button
      aria-label={label}
      title={label}
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        width: dim,
        height: dim,
        background: active ? "var(--primary-container)" : "transparent",
        color: active ? "var(--on-primary-container)" : "var(--on-surface-variant)",
        border: "none",
        borderRadius: "var(--radius-md)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        transition: "background-color 150ms ease, color 150ms ease",
        ...style,
      }}
      onMouseEnter={(e) => { if (!active && !disabled) e.currentTarget.style.background = "var(--hover-tint)"; }}
      onMouseLeave={(e) => { if (!active && !disabled) e.currentTarget.style.background = "transparent"; }}
      {...rest}
    >
      <Icon name={icon} size={size === "sm" ? 18 : 20} />
    </button>
  );
}
