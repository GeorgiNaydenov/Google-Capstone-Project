import React from "react";
import { Icon } from "./Icon.jsx";

/**
 * Button — primary action control. Flat, bordered, 6px radius.
 * Variants: primary | secondary | outline | ghost | danger.
 * Sizes: sm (36px) | md (44px).
 */
export function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconRight,
  disabled = false,
  fullWidth = false,
  style,
  ...rest
}) {
  const height = size === "sm" ? "var(--row-height-sm)" : "var(--row-height-md)";
  const pad = size === "sm" ? "0 12px" : "0 16px";

  const palettes = {
    primary: { bg: "var(--primary)", fg: "var(--on-primary)", bd: "var(--primary)" },
    secondary: { bg: "var(--secondary-container)", fg: "var(--on-secondary-fixed-variant)", bd: "var(--secondary-container)" },
    outline: { bg: "transparent", fg: "var(--primary)", bd: "var(--primary)" },
    ghost: { bg: "transparent", fg: "var(--on-surface-variant)", bd: "transparent" },
    danger: { bg: "var(--error)", fg: "var(--on-error)", bd: "var(--error)" },
  };
  const p = palettes[variant] || palettes.primary;

  return (
    <button
      disabled={disabled}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "var(--space-sm)",
        height,
        padding: pad,
        width: fullWidth ? "100%" : "auto",
        background: p.bg,
        color: p.fg,
        border: `var(--border-width) solid ${p.bd}`,
        borderRadius: "var(--radius-md)",
        fontFamily: "var(--font-sans)",
        fontSize: "var(--type-panel-title-size)",
        fontWeight: "var(--type-panel-title-weight)",
        lineHeight: "var(--type-panel-title-line)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        whiteSpace: "nowrap",
        transition: "background-color 150ms ease, border-color 150ms ease, opacity 150ms ease",
        ...style,
      }}
      {...rest}
    >
      {icon && <Icon name={icon} size={size === "sm" ? 16 : 18} />}
      {children}
      {iconRight && <Icon name={iconRight} size={size === "sm" ? 16 : 18} />}
    </button>
  );
}
