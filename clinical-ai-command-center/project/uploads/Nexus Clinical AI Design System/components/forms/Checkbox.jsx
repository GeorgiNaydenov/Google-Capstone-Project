import React from "react";
import { Icon } from "../core/Icon.jsx";

/**
 * Checkbox — 4px-radius box, primary fill when checked. Pairs with a label.
 */
export function Checkbox({ checked = false, label, disabled = false, onChange, style, ...rest }) {
  return (
    <label
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-sm)",
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.45 : 1,
        fontFamily: "var(--font-sans)",
        fontSize: "var(--type-table-size)",
        color: "var(--on-surface)",
        ...style,
      }}
      {...rest}
    >
      <span
        style={{
          width: 16,
          height: 16,
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "var(--radius-sm)",
          border: `var(--border-width) solid ${checked ? "var(--primary)" : "var(--outline)"}`,
          background: checked ? "var(--primary)" : "var(--surface-container-lowest)",
          transition: "background-color 120ms ease, border-color 120ms ease",
          flexShrink: 0,
        }}
      >
        {checked && <Icon name="check" size={12} style={{ color: "var(--on-primary)" }} />}
      </span>
      <input
        type="checkbox"
        checked={checked}
        disabled={disabled}
        onChange={onChange}
        style={{ position: "absolute", opacity: 0, width: 0, height: 0 }}
      />
      {label && <span>{label}</span>}
    </label>
  );
}
