import React from "react";

/**
 * Icon — Material Symbols Outlined glyph.
 * Pass the symbol ligature name as `name` (e.g. "dashboard", "warning").
 */
export function Icon({ name, size = 20, fill = 0, weight = 400, grade = 0, style, className = "", ...rest }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`}
      aria-hidden="true"
      style={{
        fontSize: size,
        fontVariationSettings: `'FILL' ${fill}, 'wght' ${weight}, 'GRAD' ${grade}, 'opsz' ${size}`,
        lineHeight: 1,
        userSelect: "none",
        ...style,
      }}
      {...rest}
    >
      {name}
    </span>
  );
}
