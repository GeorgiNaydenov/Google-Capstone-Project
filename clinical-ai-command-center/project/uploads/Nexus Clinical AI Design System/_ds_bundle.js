/* @ds-bundle: {"format":3,"namespace":"NexusClinicalAIDesignSystem_29a409","components":[{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Icon","sourcePath":"components/core/Icon.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"DataTable","sourcePath":"components/data/DataTable.jsx"},{"name":"SQLPreview","sourcePath":"components/data/SQLPreview.jsx"},{"name":"ConfidenceMeter","sourcePath":"components/feedback/ConfidenceMeter.jsx"},{"name":"EvidenceCitation","sourcePath":"components/feedback/EvidenceCitation.jsx"},{"name":"StatusChip","sourcePath":"components/feedback/StatusChip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Textarea","sourcePath":"components/forms/Textarea.jsx"},{"name":"Panel","sourcePath":"components/layout/Panel.jsx"},{"name":"RoleSwitcher","sourcePath":"components/navigation/RoleSwitcher.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Button.jsx":"129c467912c2","components/core/Icon.jsx":"9261ab03c8c1","components/core/IconButton.jsx":"83d285438ece","components/data/DataTable.jsx":"0f051da7c2a1","components/data/SQLPreview.jsx":"8dbbf15ee71c","components/feedback/ConfidenceMeter.jsx":"54b0da51ebdf","components/feedback/EvidenceCitation.jsx":"fbaa07b2b70c","components/feedback/StatusChip.jsx":"394eaa760876","components/forms/Checkbox.jsx":"c3c616516b65","components/forms/Input.jsx":"07636aaac211","components/forms/Select.jsx":"7f73ad4f9dd9","components/forms/Textarea.jsx":"251b509b12f1","components/layout/Panel.jsx":"7cc6f4a62241","components/navigation/RoleSwitcher.jsx":"3d21b22568f7","components/navigation/Tabs.jsx":"4d1dbdc64686","ui_kits/clinician_ai_kit/AppShell.jsx":"453c4564dba7","ui_kits/clinician_ai_kit/DashboardScreen.jsx":"124f7a9700bc","ui_kits/clinician_ai_kit/DbIntelligenceScreen.jsx":"bdc1c7250d4c","ui_kits/clinician_ai_kit/ImageExtractionScreen.jsx":"74877a21cb04","ui_kits/clinician_ai_kit/InboxScreen.jsx":"ce529518145d","ui_kits/clinician_ai_kit/MultimodalQAScreen.jsx":"a630a6904c5f","ui_kits/clinician_ai_kit/PatientProfileScreen.jsx":"03b7d08a8178"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.NexusClinicalAIDesignSystem_29a409 = window.NexusClinicalAIDesignSystem_29a409 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Icon.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Icon — Material Symbols Outlined glyph.
 * Pass the symbol ligature name as `name` (e.g. "dashboard", "warning").
 */
function Icon({
  name,
  size = 20,
  fill = 0,
  weight = 400,
  grade = 0,
  style,
  className = "",
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({
    className: `material-symbols-outlined ${className}`,
    "aria-hidden": "true",
    style: {
      fontSize: size,
      fontVariationSettings: `'FILL' ${fill}, 'wght' ${weight}, 'GRAD' ${grade}, 'opsz' ${size}`,
      lineHeight: 1,
      userSelect: "none",
      ...style
    }
  }, rest), name);
}
Object.assign(__ds_scope, { Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Icon.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Button — primary action control. Flat, bordered, 6px radius.
 * Variants: primary | secondary | outline | ghost | danger.
 * Sizes: sm (36px) | md (44px).
 */
function Button({
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
    primary: {
      bg: "var(--primary)",
      fg: "var(--on-primary)",
      bd: "var(--primary)"
    },
    secondary: {
      bg: "var(--secondary-container)",
      fg: "var(--on-secondary-fixed-variant)",
      bd: "var(--secondary-container)"
    },
    outline: {
      bg: "transparent",
      fg: "var(--primary)",
      bd: "var(--primary)"
    },
    ghost: {
      bg: "transparent",
      fg: "var(--on-surface-variant)",
      bd: "transparent"
    },
    danger: {
      bg: "var(--error)",
      fg: "var(--on-error)",
      bd: "var(--error)"
    }
  };
  const p = palettes[variant] || palettes.primary;
  return /*#__PURE__*/React.createElement("button", _extends({
    disabled: disabled,
    style: {
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
      ...style
    }
  }, rest), icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: size === "sm" ? 16 : 18
  }), children, iconRight && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: iconRight,
    size: size === "sm" ? 16 : 18
  }));
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * IconButton — square, icon-only action. Used in app bars and panel headers.
 * Subtle tonal hover; no shadow. Sizes: sm (28px) | md (32px).
 */
function IconButton({
  icon,
  size = "md",
  label,
  active = false,
  disabled = false,
  style,
  ...rest
}) {
  const dim = size === "sm" ? 28 : 32;
  return /*#__PURE__*/React.createElement("button", _extends({
    "aria-label": label,
    title: label,
    disabled: disabled,
    style: {
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
      ...style
    },
    onMouseEnter: e => {
      if (!active && !disabled) e.currentTarget.style.background = "var(--hover-tint)";
    },
    onMouseLeave: e => {
      if (!active && !disabled) e.currentTarget.style.background = "transparent";
    }
  }, rest), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: size === "sm" ? 18 : 20
  }));
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/data/DataTable.jsx
try { (() => {
/**
 * DataTable — the core dense table. Sticky header, zebra striping,
 * 36px rows, 12px horizontal cell padding, hairline dividers.
 *
 * columns: [{ key, header, align?, mono?, width?, render?(row) }]
 * rows: array of objects keyed by column.key
 */
function DataTable({
  columns = [],
  rows = [],
  zebra = true,
  onRowClick,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      overflow: "auto",
      ...style
    }
  }, /*#__PURE__*/React.createElement("table", {
    style: {
      width: "100%",
      borderCollapse: "collapse",
      textAlign: "left",
      whiteSpace: "nowrap"
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, columns.map(c => /*#__PURE__*/React.createElement("th", {
    key: c.key,
    style: {
      position: "sticky",
      top: 0,
      zIndex: 1,
      padding: "8px 12px",
      background: "var(--surface-container)",
      borderBottom: "var(--border-width) solid var(--outline-variant)",
      fontFamily: "var(--font-sans)",
      fontSize: "11px",
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      textAlign: c.align || "left"
    }
  }, c.header)))), /*#__PURE__*/React.createElement("tbody", null, rows.map((row, i) => /*#__PURE__*/React.createElement("tr", {
    key: row.id || i,
    onClick: () => onRowClick && onRowClick(row),
    style: {
      height: "var(--row-height-sm)",
      background: zebra && i % 2 === 1 ? "var(--surface-container-low)" : "var(--surface-container-lowest)",
      borderBottom: "var(--border-width) solid color-mix(in srgb, var(--outline-variant) 50%, transparent)",
      cursor: onRowClick ? "pointer" : "default",
      transition: "background-color 120ms ease"
    },
    onMouseEnter: e => {
      e.currentTarget.style.background = "var(--surface-container-high)";
    },
    onMouseLeave: e => {
      e.currentTarget.style.background = zebra && i % 2 === 1 ? "var(--surface-container-low)" : "var(--surface-container-lowest)";
    }
  }, columns.map(c => /*#__PURE__*/React.createElement("td", {
    key: c.key,
    style: {
      padding: "0 12px",
      fontFamily: c.mono ? "var(--font-mono)" : "var(--font-sans)",
      fontSize: c.mono ? "12px" : "13px",
      color: "var(--on-surface)",
      textAlign: c.align || "left"
    }
  }, c.render ? c.render(row) : row[c.key])))))));
}
Object.assign(__ds_scope, { DataTable });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/DataTable.jsx", error: String((e && e.message) || e) }); }

// components/data/SQLPreview.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * SQLPreview — transparency block for AI-generated SQL.
 * Mono font, container background, optional copy affordance.
 * Pass `html` for pre-highlighted markup, or `code` for plain text.
 */
function SQLPreview({
  code,
  html,
  label = "Generated SQL",
  onCopy,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: "11px",
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)"
    }
  }, label), /*#__PURE__*/React.createElement("button", {
    onClick: onCopy,
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      background: "none",
      border: "none",
      cursor: "pointer",
      color: "var(--primary)",
      fontFamily: "var(--font-sans)",
      fontSize: "11px",
      fontWeight: 600
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 14
    }
  }, "content_copy"), " Copy")), /*#__PURE__*/React.createElement("pre", _extends({
    style: {
      margin: 0,
      padding: "var(--space-sm)",
      background: "var(--surface-container-highest)",
      border: "var(--border-width) solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      overflowX: "auto",
      fontFamily: "var(--font-mono)",
      fontSize: "12px",
      lineHeight: 1.5,
      color: "var(--on-surface)"
    }
  }, html ? {
    dangerouslySetInnerHTML: {
      __html: html
    }
  } : {}), html ? undefined : code));
}
Object.assign(__ds_scope, { SQLPreview });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/data/SQLPreview.jsx", error: String((e && e.message) || e) }); }

// components/feedback/ConfidenceMeter.jsx
try { (() => {
/**
 * ConfidenceMeter — linear gauge for AI confidence / completeness.
 * Thin 4px track, colored fill keyed to value, numeric readout.
 * Auto-colors: >=90 success, >=70 primary, >=50 warning, else critical.
 */
function ConfidenceMeter({
  value = 0,
  label,
  width = 96,
  showValue = true,
  color,
  style
}) {
  const v = Math.max(0, Math.min(100, value));
  const fill = color || (v >= 90 ? "var(--success)" : v >= 70 ? "var(--primary)" : v >= 50 ? "var(--tertiary)" : "var(--error)");
  const numColor = color || (v >= 90 ? "var(--on-success-container)" : v >= 70 ? "var(--primary)" : v >= 50 ? "var(--tertiary)" : "var(--error)");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      ...style
    }
  }, label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: "11px",
      fontWeight: 600,
      color: "var(--on-surface-variant)"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      width,
      height: 4,
      background: "var(--surface-variant)",
      borderRadius: "var(--radius-full)",
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: `${v}%`,
      height: "100%",
      background: fill,
      transition: "width 300ms ease"
    }
  })), showValue && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "11px",
      fontWeight: 700,
      color: numColor
    }
  }, v, "%"));
}
Object.assign(__ds_scope, { ConfidenceMeter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/ConfidenceMeter.jsx", error: String((e && e.message) || e) }); }

// components/feedback/EvidenceCitation.jsx
try { (() => {
/**
 * EvidenceCitation — bordered source callout for AI-synthesized claims.
 * Superscript index, source snippet, "View Source" link.
 */
function EvidenceCitation({
  index = 1,
  snippet,
  sourceLabel = "View Source",
  onView,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      paddingLeft: "var(--space-xl)",
      padding: "var(--space-sm) var(--space-sm) var(--space-sm) var(--space-xl)",
      background: "var(--surface-container-low)",
      border: "var(--border-width) solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: "var(--space-sm)",
      top: "var(--space-sm)",
      width: 16,
      height: 16,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      borderRadius: "var(--radius-full)",
      background: "var(--primary-fixed)",
      color: "var(--primary)",
      fontFamily: "var(--font-mono)",
      fontSize: "10px",
      fontWeight: 700
    }
  }, index), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      marginBottom: 4,
      fontFamily: "var(--font-sans)",
      fontSize: "12px",
      lineHeight: "16px",
      color: "var(--on-surface)"
    }
  }, snippet), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => {
      e.preventDefault();
      onView && onView();
    },
    style: {
      fontFamily: "var(--font-sans)",
      fontSize: "11px",
      fontWeight: 600,
      color: "var(--primary)",
      textDecoration: "none"
    }
  }, sourceLabel, " \u2192"));
}
Object.assign(__ds_scope, { EvidenceCitation });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/EvidenceCitation.jsx", error: String((e && e.message) || e) }); }

// components/feedback/StatusChip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const TONES = {
  critical: {
    fg: "var(--error)",
    bg: "var(--error-container)",
    bd: "var(--error)"
  },
  warning: {
    fg: "var(--tertiary)",
    bg: "var(--tertiary-fixed)",
    bd: "var(--tertiary)"
  },
  stable: {
    fg: "var(--primary)",
    bg: "var(--primary-fixed)",
    bd: "var(--primary)"
  },
  verified: {
    fg: "var(--on-success-container)",
    bg: "var(--success-container)",
    bd: "var(--success)"
  },
  info: {
    fg: "var(--on-secondary-fixed-variant)",
    bg: "var(--secondary-fixed)",
    bd: "var(--secondary)"
  },
  neutral: {
    fg: "var(--on-surface-variant)",
    bg: "var(--surface-variant)",
    bd: "var(--outline-variant)"
  }
};

/**
 * StatusChip — compact status indicator. Tonal bg, solid text, hairline border.
 * Tones: critical | warning | stable | verified | info | neutral.
 */
function StatusChip({
  children,
  tone = "neutral",
  icon,
  style,
  ...rest
}) {
  const t = TONES[tone] || TONES.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({
    style: {
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
      ...style
    }
  }, rest), icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 14
  }), children);
}
Object.assign(__ds_scope, { StatusChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/StatusChip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Checkbox — 4px-radius box, primary fill when checked. Pairs with a label.
 */
function Checkbox({
  checked = false,
  label,
  disabled = false,
  onChange,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("label", _extends({
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.45 : 1,
      fontFamily: "var(--font-sans)",
      fontSize: "var(--type-table-size)",
      color: "var(--on-surface)",
      ...style
    }
  }, rest), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 16,
      height: 16,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      borderRadius: "var(--radius-sm)",
      border: `var(--border-width) solid ${checked ? "var(--primary)" : "var(--outline)"}`,
      background: checked ? "var(--primary)" : "var(--surface-container-lowest)",
      transition: "background-color 120ms ease, border-color 120ms ease",
      flexShrink: 0
    }
  }, checked && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "check",
    size: 12,
    style: {
      color: "var(--on-primary)"
    }
  })), /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: checked,
    disabled: disabled,
    onChange: onChange,
    style: {
      position: "absolute",
      opacity: 0,
      width: 0,
      height: 0
    }
  }), label && /*#__PURE__*/React.createElement("span", null, label));
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Input — text field. 1px outline, 6px radius, focus = primary border.
 * Optional leading icon. Sizes: sm (36px) | md (44px).
 */
function Input({
  size = "md",
  icon,
  invalid = false,
  style,
  ...rest
}) {
  const height = size === "sm" ? "var(--row-height-sm)" : "var(--row-height-md)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      width: "100%"
    }
  }, icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 18,
    style: {
      position: "absolute",
      left: "var(--space-sm)",
      top: "50%",
      transform: "translateY(-50%)",
      color: "var(--on-surface-variant)",
      pointerEvents: "none"
    }
  }), /*#__PURE__*/React.createElement("input", _extends({
    style: {
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
      ...style
    },
    onFocus: e => {
      e.currentTarget.style.borderColor = "var(--primary)";
      e.currentTarget.style.boxShadow = "inset 0 0 0 1px var(--primary)";
    },
    onBlur: e => {
      e.currentTarget.style.borderColor = invalid ? "var(--error)" : "var(--outline-variant)";
      e.currentTarget.style.boxShadow = "none";
    }
  }, rest)));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Select — native dropdown styled to the system. 36px compact by default.
 */
function Select({
  size = "sm",
  children,
  style,
  ...rest
}) {
  const height = size === "sm" ? "var(--row-height-sm)" : "var(--row-height-md)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      width: "100%"
    }
  }, /*#__PURE__*/React.createElement("select", _extends({
    style: {
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
      ...style
    }
  }, rest), children), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "expand_more",
    size: 18,
    style: {
      position: "absolute",
      right: "var(--space-sm)",
      top: "50%",
      transform: "translateY(-50%)",
      color: "var(--on-surface-variant)",
      pointerEvents: "none"
    }
  }));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Textarea.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Textarea — multi-line natural-language input (agent queries, notes).
 */
function Textarea({
  rows = 4,
  invalid = false,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("textarea", _extends({
    rows: rows,
    style: {
      width: "100%",
      padding: "var(--space-sm)",
      background: "var(--surface-container-lowest)",
      color: "var(--on-surface)",
      border: `var(--border-width) solid ${invalid ? "var(--error)" : "var(--outline-variant)"}`,
      borderRadius: "var(--radius-md)",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--type-body-size)",
      lineHeight: "var(--type-body-line)",
      outline: "none",
      resize: "vertical",
      boxSizing: "border-box",
      transition: "border-color 150ms ease",
      ...style
    },
    onFocus: e => {
      e.currentTarget.style.borderColor = "var(--primary)";
    },
    onBlur: e => {
      e.currentTarget.style.borderColor = invalid ? "var(--error)" : "var(--outline-variant)";
    }
  }, rest));
}
Object.assign(__ds_scope, { Textarea });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Textarea.jsx", error: String((e && e.message) || e) }); }

// components/layout/Panel.jsx
try { (() => {
/**
 * Panel — the core work-surface container. White bg, 1px border, 8px radius.
 * Optional bordered header (title + icon + trailing actions). No shadow.
 */
function Panel({
  title,
  icon,
  iconColor = "var(--on-surface-variant)",
  actions,
  children,
  bodyPadding = "var(--space-md)",
  style,
  bodyStyle
}) {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      display: "flex",
      flexDirection: "column",
      background: "var(--surface-container-lowest)",
      border: "var(--border-width) solid var(--outline-variant)",
      borderRadius: "var(--radius-lg)",
      overflow: "hidden",
      ...style
    }
  }, title && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "var(--space-sm) var(--space-md)",
      background: "var(--surface-container-low)",
      borderBottom: "var(--border-width) solid var(--outline-variant)"
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      fontFamily: "var(--font-sans)",
      fontSize: "var(--type-panel-title-size)",
      fontWeight: 600,
      color: "var(--on-surface)"
    }
  }, icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: icon,
    size: 18,
    style: {
      color: iconColor
    }
  }), title), actions && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)"
    }
  }, actions)), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: bodyPadding,
      ...bodyStyle
    }
  }, children));
}
Object.assign(__ds_scope, { Panel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/layout/Panel.jsx", error: String((e && e.message) || e) }); }

// components/navigation/RoleSwitcher.jsx
try { (() => {
/**
 * RoleSwitcher — segmented control for toggling clinical views.
 * Active = primary fill; inactive = transparent on a container track.
 */
function RoleSwitcher({
  options = [],
  value,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      background: "var(--surface-container)",
      border: "var(--border-width) solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: 2,
      gap: 2,
      ...style
    }
  }, options.map(opt => {
    const active = opt === value;
    return /*#__PURE__*/React.createElement("button", {
      key: opt,
      onClick: () => onChange && onChange(opt),
      style: {
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
        transition: "background-color 150ms ease, color 150ms ease"
      }
    }, opt);
  }));
}
Object.assign(__ds_scope, { RoleSwitcher });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/RoleSwitcher.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
/**
 * Tabs — underline-style tab bar for work-surface sections.
 * Active tab: primary text + 2px primary underline.
 */
function Tabs({
  tabs = [],
  value,
  onChange,
  style
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-md)",
      borderBottom: "var(--border-width) solid var(--outline-variant)",
      ...style
    }
  }, tabs.map(tab => {
    const active = tab === value;
    return /*#__PURE__*/React.createElement("button", {
      key: tab,
      onClick: () => onChange && onChange(tab),
      style: {
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
        transition: "color 150ms ease, border-color 150ms ease"
      }
    }, tab);
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/AppShell.jsx
try { (() => {
// AppShell — chrome for Clinician AI KIT: grouped sidebar nav + top bar.
const NDS_shell = window.NexusClinicalAIDesignSystem_29a409;

// Grouped navigation keeps the dense product calm: three short sections
// instead of one long flat list.
const NAV_GROUPS = [{
  label: "Workspace",
  items: [{
    id: "dashboard",
    icon: "dashboard",
    label: "Dashboard"
  }, {
    id: "inbox",
    icon: "inbox",
    label: "Clinical Inbox",
    badge: 6
  }, {
    id: "patient",
    icon: "groups",
    label: "Patients"
  }]
}, {
  label: "AI Agents",
  items: [{
    id: "extraction",
    icon: "biotech",
    label: "Image Extraction"
  }, {
    id: "qa",
    icon: "neurology",
    label: "Multimodal Q and A"
  }, {
    id: "db",
    icon: "database",
    label: "Database Intelligence"
  }]
}, {
  label: "Governance",
  items: [{
    id: "audit",
    icon: "policy",
    label: "Audit Trail"
  }]
}];
function NavItem({
  item,
  active,
  onNavigate
}) {
  return /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => {
      e.preventDefault();
      onNavigate(item.id);
    },
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)",
      height: 36,
      padding: "0 var(--space-md)",
      borderRadius: active ? "0 var(--radius-md) var(--radius-md) 0" : "var(--radius-md)",
      background: active ? "var(--secondary-container)" : "transparent",
      color: active ? "var(--on-secondary-container)" : "var(--on-surface-variant)",
      borderLeft: active ? "3px solid var(--primary)" : "3px solid transparent",
      fontSize: 13,
      fontWeight: active ? 600 : 500,
      textDecoration: "none",
      transition: "background-color 150ms ease"
    },
    onMouseEnter: e => {
      if (!active) e.currentTarget.style.background = "var(--surface-container-high)";
    },
    onMouseLeave: e => {
      if (!active) e.currentTarget.style.background = "transparent";
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 20,
      fontVariationSettings: active ? "'FILL' 1" : "'FILL' 0"
    }
  }, item.icon), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }, item.label), item.badge ? /*#__PURE__*/React.createElement("span", {
    style: {
      minWidth: 18,
      height: 18,
      padding: "0 5px",
      borderRadius: "var(--radius-full)",
      background: "var(--error)",
      color: "var(--on-error)",
      fontSize: 10,
      fontWeight: 700,
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, item.badge) : null);
}
function SideNav({
  current,
  onNavigate
}) {
  return /*#__PURE__*/React.createElement("nav", {
    style: {
      width: "var(--sidebar-width)",
      flexShrink: 0,
      height: "100%",
      background: "var(--surface-container-low)",
      borderRight: "1px solid var(--outline-variant)",
      display: "flex",
      flexDirection: "column",
      padding: "var(--space-md) 0"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 var(--space-lg)",
      marginBottom: "var(--space-lg)",
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/clinician-ai-kit-mark.png",
    alt: "Clinician AI KIT",
    style: {
      height: 26,
      width: "auto"
    }
  }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 700,
      color: "var(--on-surface)",
      letterSpacing: "-0.01em"
    }
  }, "Clinician AI KIT"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "var(--on-surface-variant)"
    }
  }, "Clinical Command v2.4"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 var(--space-sm)",
      marginBottom: "var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement(NDS_shell.Button, {
    variant: "primary",
    icon: "add",
    fullWidth: true,
    size: "sm"
  }, "New session")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: "auto",
      padding: "0 var(--space-sm)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-lg)"
    }
  }, NAV_GROUPS.map(group => /*#__PURE__*/React.createElement("div", {
    key: group.label,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 2
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "0 var(--space-md)",
      marginBottom: 4,
      fontSize: 10,
      fontWeight: 700,
      letterSpacing: "0.06em",
      textTransform: "uppercase",
      color: "var(--outline)"
    }
  }, group.label), group.items.map(item => /*#__PURE__*/React.createElement(NavItem, {
    key: item.id,
    item: item,
    active: current === item.id,
    onNavigate: onNavigate
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "auto",
      padding: "var(--space-md) var(--space-lg) 0",
      borderTop: "1px solid var(--outline-variant)",
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: "var(--radius-full)",
      background: "var(--primary-container)",
      color: "var(--on-primary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 12,
      fontWeight: 700
    }
  }, "SM"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: "var(--on-surface)"
    }
  }, "Dr. Sarah Miller"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 10,
      color: "var(--on-surface-variant)"
    }
  }, "Oncologist")), /*#__PURE__*/React.createElement(NDS_shell.IconButton, {
    icon: "more_vert",
    label: "Account menu",
    size: "sm"
  })));
}
function TopBar({
  role,
  onRole,
  title
}) {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      height: "var(--row-height-md)",
      flexShrink: 0,
      background: "var(--surface)",
      borderBottom: "1px solid var(--outline-variant)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 var(--space-lg)",
      zIndex: 10
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 15,
      fontWeight: 600,
      color: "var(--on-surface)"
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      width: 1,
      height: 20,
      background: "var(--outline-variant)"
    }
  }), /*#__PURE__*/React.createElement(NDS_shell.RoleSwitcher, {
    options: ["Clinician", "Admin"],
    value: role,
    onChange: onRole
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 260
    }
  }, /*#__PURE__*/React.createElement(NDS_shell.Input, {
    size: "sm",
    icon: "search",
    placeholder: "Search patients, sessions, or IDs"
  })), /*#__PURE__*/React.createElement(NDS_shell.IconButton, {
    icon: "sync",
    label: "Sync data"
  }), /*#__PURE__*/React.createElement(NDS_shell.IconButton, {
    icon: "notifications",
    label: "Notifications"
  }), /*#__PURE__*/React.createElement(NDS_shell.IconButton, {
    icon: "settings",
    label: "Settings"
  })));
}
function AppShell({
  current,
  onNavigate,
  title,
  children
}) {
  const [role, setRole] = React.useState("Clinician");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      height: "100%",
      background: "var(--background)",
      color: "var(--on-surface)",
      fontFamily: "var(--font-sans)"
    }
  }, /*#__PURE__*/React.createElement(SideNav, {
    current: current,
    onNavigate: onNavigate
  }), /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      display: "flex",
      flexDirection: "column",
      overflow: "hidden",
      background: "var(--surface-container-low)"
    }
  }, /*#__PURE__*/React.createElement(TopBar, {
    role: role,
    onRole: setRole,
    title: title
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: "auto"
    }
  }, children)));
}
Object.assign(window, {
  AppShell
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/AppShell.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/DashboardScreen.jsx
try { (() => {
// DashboardScreen — clinician home: priority work, AI guidance, today's plan.
const NDS_dash = window.NexusClinicalAIDesignSystem_29a409;
function KpiCard({
  label,
  value,
  sub,
  icon,
  iconColor,
  iconBg,
  critical
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-lowest)",
      border: "1px solid var(--outline-variant)",
      borderLeft: critical ? "3px solid var(--error)" : "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-md)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)"
    }
  }, label), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 24,
      fontWeight: 600,
      marginTop: 4,
      color: critical ? "var(--error)" : "var(--on-surface)"
    }
  }, value), sub ? /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, sub) : null), /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 22,
      color: iconColor,
      background: iconBg,
      padding: 8,
      borderRadius: "var(--radius-md)"
    }
  }, icon));
}
function RecommendationCard({
  icon,
  iconColor,
  title,
  body,
  action,
  onAct
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)",
      background: "var(--surface-container-lowest)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-sm)",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 18,
      color: iconColor,
      marginTop: 1
    }
  }, icon), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: "var(--on-surface)"
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--on-surface-variant)",
      marginTop: 2,
      lineHeight: "16px"
    }
  }, body))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "flex-end",
      marginTop: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(NDS_dash.Button, {
    variant: "outline",
    size: "sm",
    onClick: onAct
  }, action)));
}
function TimelineEvent({
  color,
  title,
  meta,
  danger
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      paddingLeft: "var(--space-xl)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: -5,
      top: 4,
      width: 10,
      height: 10,
      borderRadius: "var(--radius-full)",
      background: color,
      border: "2px solid var(--surface-container-lowest)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: danger ? "var(--error)" : "var(--on-surface)"
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, meta));
}
function DashboardScreen({
  onOpenPatient
}) {
  const {
    Panel,
    Button,
    DataTable,
    StatusChip
  } = NDS_dash;
  const queue = [{
    id: "PT-8829",
    name: "Jonathan Doe",
    risk: "High risk",
    tone: "critical",
    reason: "Elevated troponin found in the most recent lab extraction."
  }, {
    id: "PT-1044",
    name: "Sarah Smith",
    risk: "Needs review",
    tone: "warning",
    reason: "Medication history conflicts across three clinical notes."
  }, {
    id: "PT-5510",
    name: "Wei Chen",
    risk: "Stable",
    tone: "stable",
    reason: "Routine AI summary generated with no acute flags."
  }, {
    id: "PT-9921",
    name: "Maria Garcia",
    risk: "Needs review",
    tone: "warning",
    reason: "Imaging report missing for the recent MRI study."
  }];
  const cols = [{
    key: "id",
    header: "Patient ID",
    mono: true
  }, {
    key: "name",
    header: "Name",
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 500
      }
    }, r.name)
  }, {
    key: "risk",
    header: "Risk status",
    render: r => /*#__PURE__*/React.createElement(StatusChip, {
      tone: r.tone
    }, r.risk)
  }, {
    key: "reason",
    header: "Reason flagged",
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--on-surface-variant)",
        display: "inline-block",
        maxWidth: 240,
        overflow: "hidden",
        textOverflow: "ellipsis"
      }
    }, r.reason)
  }, {
    key: "action",
    header: "Action",
    align: "right",
    render: r => /*#__PURE__*/React.createElement("a", {
      href: "#",
      onClick: e => {
        e.preventDefault();
        onOpenPatient && onOpenPatient();
      },
      style: {
        color: "var(--primary)",
        fontWeight: 500,
        textDecoration: "none"
      }
    }, r.tone === "stable" ? "View" : "Review")
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: 26,
      fontWeight: 600,
      letterSpacing: "-0.02em"
    }
  }, "Good morning, Dr. Miller"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "4px 0 0",
      fontSize: 13,
      color: "var(--on-surface-variant)"
    }
  }, "You have 7 high risk patients and 12 items waiting in your clinical inbox.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(KpiCard, {
    label: "Total patients",
    value: "1,248",
    sub: "Assigned to your panel",
    icon: "groups",
    iconColor: "var(--primary)",
    iconBg: "var(--primary-fixed)"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    label: "Pending extractions",
    value: "34",
    sub: "Awaiting AI processing",
    icon: "pending_actions",
    iconColor: "var(--tertiary)",
    iconBg: "var(--tertiary-fixed)"
  }), /*#__PURE__*/React.createElement(KpiCard, {
    label: "High risk alerts",
    value: "7",
    sub: "Need clinical attention",
    icon: "warning",
    iconColor: "var(--error)",
    iconBg: "var(--error-container)",
    critical: true
  }), /*#__PURE__*/React.createElement(KpiCard, {
    label: "Clinical inbox",
    value: "12",
    sub: "Items to review",
    icon: "inbox",
    iconColor: "var(--secondary)",
    iconBg: "var(--secondary-fixed)"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "2fr 1fr",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Priority patient queue",
    icon: "priority_high",
    bodyPadding: "0",
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "ghost",
      size: "sm"
    }, "View all")
  }, /*#__PURE__*/React.createElement(DataTable, {
    columns: cols,
    rows: queue,
    onRowClick: () => onOpenPatient && onOpenPatient()
  })), /*#__PURE__*/React.createElement(Panel, {
    title: "Recent agent activity",
    icon: "history"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      borderLeft: "1px solid var(--outline-variant)",
      marginLeft: "var(--space-sm)",
      paddingTop: 4
    }
  }, /*#__PURE__*/React.createElement(TimelineEvent, {
    color: "var(--primary)",
    title: "Extraction complete for MRI Brain, PT-8829",
    meta: "2 minutes ago. Confidence 94 percent."
  }), /*#__PURE__*/React.createElement(TimelineEvent, {
    color: "var(--outline)",
    title: "EHR database sync finished",
    meta: "15 minutes ago. Processed 42 new records."
  }), /*#__PURE__*/React.createElement(TimelineEvent, {
    color: "var(--error)",
    danger: true,
    title: "Alert generated for troponin elevation",
    meta: "1 hour ago. Raised by the monitoring agent."
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "AI recommendations",
    icon: "lightbulb",
    iconColor: "var(--primary)",
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "ghost",
      size: "sm"
    }, "View all")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(RecommendationCard, {
    icon: "refresh",
    iconColor: "var(--tertiary)",
    title: "Re-run extraction for PT-8829",
    body: "The previous text extraction scored 72 percent confidence. Re-processing with high resolution OCR is recommended.",
    action: "Run extraction"
  }), /*#__PURE__*/React.createElement(RecommendationCard, {
    icon: "assignment",
    iconColor: "var(--primary)",
    title: "Review the updated treatment plan",
    body: "New lab results for PT-1044 conflict with the current medication. The agent suggests an alternative dose.",
    action: "Open draft"
  }))), /*#__PURE__*/React.createElement(Panel, {
    title: "Today's sessions",
    icon: "event",
    bodyPadding: "var(--space-sm)"
  }, [{
    time: "10:00 AM",
    label: "Tumor board preparation",
    status: "In progress",
    live: true
  }, {
    time: "01:30 PM",
    label: "PT-8829 consult",
    status: "Scheduled"
  }, {
    time: "03:00 PM",
    label: "Data sync review",
    status: "Scheduled"
  }].map((s, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      height: 36,
      padding: "0 var(--space-sm)",
      borderBottom: i < 2 ? "1px solid color-mix(in srgb, var(--outline-variant) 50%, transparent)" : "none"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      fontWeight: 500,
      color: s.live ? "var(--on-surface)" : "var(--on-surface-variant)",
      width: 72
    }
  }, s.time), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      fontSize: 13,
      color: "var(--on-surface)"
    }
  }, s.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 600,
      color: s.live ? "var(--primary)" : "var(--on-surface-variant)"
    }
  }, s.status)))))));
}
Object.assign(window, {
  DashboardScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/DashboardScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/DbIntelligenceScreen.jsx
try { (() => {
// DbIntelligenceScreen — natural-language querying over clinical data.
const NDS_db = window.NexusClinicalAIDesignSystem_29a409;
function SchemaTable({
  name,
  icon,
  iconColor,
  open,
  fields
}) {
  const [expanded, setExpanded] = React.useState(open);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => setExpanded(!expanded),
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      padding: "4px 6px",
      borderRadius: "var(--radius-sm)",
      cursor: "pointer",
      fontSize: 13,
      fontWeight: 600,
      color: "var(--on-surface)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 16,
      color: "var(--on-surface-variant)"
    }
  }, expanded ? "keyboard_arrow_down" : "chevron_right"), /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 16,
      color: iconColor
    }
  }, icon), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 12
    }
  }, name)), expanded && fields ? /*#__PURE__*/React.createElement("div", {
    style: {
      paddingLeft: 28,
      marginTop: 2,
      display: "flex",
      flexDirection: "column",
      gap: 2
    }
  }, fields.map(f => /*#__PURE__*/React.createElement("div", {
    key: f.name,
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--on-surface-variant)",
      padding: "1px 6px"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 4
    }
  }, f.key ? /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 12,
      color: "var(--tertiary)"
    }
  }, "key") : /*#__PURE__*/React.createElement("span", {
    style: {
      width: 12
    }
  }), f.name), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--outline)"
    }
  }, f.type)))) : null);
}
function MiniChart() {
  const bars = [40, 45, 35, 60, 55, 70, 65];
  const flagged = [false, false, false, true, false, true, false];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height: 150,
      display: "flex",
      alignItems: "flex-end",
      gap: 8,
      padding: "8px 4px 0",
      borderLeft: "1px solid var(--outline)",
      borderBottom: "1px solid var(--outline)"
    }
  }, bars.map((h, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      height: `${h}%`,
      background: flagged[i] ? "color-mix(in srgb, var(--error) 22%, transparent)" : "color-mix(in srgb, var(--primary) 22%, transparent)",
      borderTop: `2px solid ${flagged[i] ? "var(--error)" : "var(--primary)"}`,
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: -5,
      left: "50%",
      transform: "translateX(-50%)",
      width: 7,
      height: 7,
      borderRadius: "var(--radius-full)",
      background: flagged[i] ? "var(--error)" : "var(--primary)"
    }
  }))));
}
function DbIntelligenceScreen() {
  const {
    Panel,
    Button,
    Input,
    SQLPreview,
    DataTable,
    ConfidenceMeter,
    EvidenceCitation
  } = NDS_db;
  const resultCols = [{
    key: "date",
    header: "trend_date",
    mono: true,
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--on-surface-variant)"
      }
    }, r.date)
  }, {
    key: "count",
    header: "high_risk_count",
    mono: true,
    align: "right",
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 600
      }
    }, r.count)
  }, {
    key: "delta",
    header: "Change",
    align: "center",
    render: r => {
      const up = r.delta.startsWith("+");
      const flat = r.delta === "0";
      const bg = flat ? "var(--surface-variant)" : up ? "var(--error-container)" : "var(--success-container)";
      const fg = flat ? "var(--on-surface-variant)" : up ? "var(--error)" : "var(--on-success-container)";
      return /*#__PURE__*/React.createElement("span", {
        style: {
          display: "inline-block",
          padding: "2px 8px",
          borderRadius: "var(--radius-sm)",
          background: bg,
          color: fg,
          fontSize: 10,
          fontWeight: 700
        }
      }, flat ? "No change" : r.delta);
    }
  }];
  const rows = [{
    date: "2023-10-01",
    count: 42,
    delta: "0"
  }, {
    date: "2023-10-02",
    count: 45,
    delta: "+3"
  }, {
    date: "2023-10-03",
    count: 39,
    delta: "-6"
  }, {
    date: "2023-10-04",
    count: 51,
    delta: "+12"
  }];
  const sqlHtml = `<span style="color:var(--primary);font-weight:600">SELECT</span>\n    DATE_TRUNC(<span style="color:var(--tertiary)">'day'</span>, admission_date) <span style="color:var(--primary);font-weight:600">AS</span> trend_date,\n    <span style="color:var(--primary);font-weight:600">COUNT</span>(*) <span style="color:var(--primary);font-weight:600">AS</span> high_risk_count\n<span style="color:var(--primary);font-weight:600">FROM</span> patients_core\n<span style="color:var(--primary);font-weight:600">WHERE</span> risk_score &gt;= <span style="color:var(--tertiary)">0.8</span>\n    <span style="color:var(--primary);font-weight:600">AND</span> admission_date &gt;= CURRENT_DATE - <span style="color:var(--primary);font-weight:600">INTERVAL</span> <span style="color:var(--tertiary)">'30 days'</span>\n<span style="color:var(--primary);font-weight:600">GROUP BY</span> <span style="color:var(--tertiary)">1</span>\n<span style="color:var(--primary);font-weight:600">ORDER BY</span> trend_date <span style="color:var(--primary);font-weight:600">ASC</span>;`;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      height: "100%",
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    bodyPadding: "var(--space-md)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 40,
      height: 40,
      borderRadius: "var(--radius-full)",
      background: "var(--primary-container)",
      color: "var(--on-primary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined"
  }, "smart_toy")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "md",
    defaultValue: "Show the trend of high risk patients over the last month"
  })), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    icon: "bolt"
  }, "Run query"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "240px 1fr 320px",
      gap: "var(--space-md)",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Schema explorer",
    icon: "account_tree",
    iconColor: "var(--primary)",
    bodyStyle: {
      overflowY: "auto"
    },
    style: {
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(SchemaTable, {
    name: "patients_core",
    icon: "table_chart",
    iconColor: "var(--secondary)",
    open: true,
    fields: [{
      name: "patient_id",
      type: "VARCHAR",
      key: true
    }, {
      name: "risk_score",
      type: "FLOAT"
    }, {
      name: "admission_date",
      type: "DATE"
    }, {
      name: "status",
      type: "VARCHAR"
    }]
  }), /*#__PURE__*/React.createElement(SchemaTable, {
    name: "clinical_notes_vec",
    icon: "scatter_plot",
    iconColor: "var(--tertiary)"
  }), /*#__PURE__*/React.createElement(SchemaTable, {
    name: "lab_results",
    icon: "table_chart",
    iconColor: "var(--secondary)"
  })), /*#__PURE__*/React.createElement(Panel, {
    title: "Query workbench",
    icon: "terminal",
    iconColor: "var(--primary)",
    bodyPadding: "0",
    style: {
      minHeight: 0
    },
    actions: /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: 6
      }
    }, /*#__PURE__*/React.createElement(StatusBadge, null, "SQL generator"), /*#__PURE__*/React.createElement(StatusBadge, null, "Validator"))
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      overflowY: "auto",
      maxHeight: "100%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      borderBottom: "1px solid var(--outline-variant)",
      display: "flex",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      color: "var(--primary)",
      fontSize: 20,
      marginTop: 1
    }
  }, "auto_awesome"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, "Agent summary"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: 13,
      color: "var(--on-surface-variant)",
      lineHeight: "18px"
    }
  }, "High risk classifications rose steadily over the past 30 days and peaked in the middle of the month. The agent processed 14,203 records across two schemas."))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      borderBottom: "1px solid var(--outline-variant)",
      background: "var(--surface-container-lowest)"
    }
  }, /*#__PURE__*/React.createElement(SQLPreview, {
    html: sqlHtml
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(ConfidenceMeter, {
    value: 98,
    label: "Execution confidence",
    width: 160
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-sm) var(--space-md)",
      background: "var(--surface-container-low)",
      borderBottom: "1px solid var(--outline-variant)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)"
    }
  }, "Result set, 30 rows"), /*#__PURE__*/React.createElement(Button, {
    variant: "ghost",
    size: "sm",
    icon: "download"
  }, "Export CSV")), /*#__PURE__*/React.createElement(DataTable, {
    columns: resultCols,
    rows: rows
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Visualization",
    icon: "show_chart",
    iconColor: "var(--tertiary)",
    style: {
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(MiniChart, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontFamily: "var(--font-mono)",
      fontSize: 9,
      color: "var(--outline)",
      marginTop: 4
    }
  }, /*#__PURE__*/React.createElement("span", null, "10/01"), /*#__PURE__*/React.createElement("span", null, "10/15"), /*#__PURE__*/React.createElement("span", null, "10/30"))), /*#__PURE__*/React.createElement(Panel, {
    title: "Clinical insight",
    icon: "insights",
    iconColor: "var(--secondary)"
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "0 0 var(--space-sm)",
      fontSize: 13,
      color: "var(--on-surface-variant)",
      lineHeight: "18px"
    }
  }, "High risk admissions show a statistically significant variance around October 12 to 15."), /*#__PURE__*/React.createElement(EvidenceCitation, {
    index: 1,
    snippet: "Correlates with the Facility C admitting protocol change implemented on October 10.",
    sourceLabel: "View source audit"
  })))));
}
function StatusBadge({
  children
}) {
  return /*#__PURE__*/React.createElement("span", {
    style: {
      padding: "2px 8px",
      borderRadius: "var(--radius-sm)",
      background: "var(--primary-fixed)",
      color: "var(--on-primary-fixed-variant)",
      fontSize: 10,
      fontWeight: 700,
      border: "1px solid var(--primary-fixed-dim)"
    }
  }, children);
}
Object.assign(window, {
  DbIntelligenceScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/DbIntelligenceScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/ImageExtractionScreen.jsx
try { (() => {
// ImageExtractionScreen — multi-agent pipeline turning a scan into structured fields.
const NDS_ext = window.NexusClinicalAIDesignSystem_29a409;
function PipelineStep({
  state,
  title,
  body,
  detail
}) {
  const done = state === "done",
    active = state === "active";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-sm)",
      padding: "var(--space-sm)",
      borderRadius: "var(--radius-md)",
      background: active ? "var(--primary-fixed)" : "transparent",
      border: active ? "1px solid var(--primary-fixed-dim)" : "1px solid transparent"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 20,
      color: done ? "var(--success)" : active ? "var(--primary)" : "var(--outline-variant)",
      fontVariationSettings: done || active ? "'FILL' 1" : "'FILL' 0",
      marginTop: 1
    }
  }, done ? "check_circle" : active ? "radio_button_checked" : "radio_button_unchecked"), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: state === "pending" ? "var(--on-surface-variant)" : "var(--on-surface)"
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--on-surface-variant)",
      marginTop: 1,
      lineHeight: "16px"
    }
  }, body), detail ? /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 6,
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      background: "var(--surface-container-highest)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-sm)",
      padding: "4px 6px",
      color: "var(--on-surface)"
    }
  }, detail) : null));
}
function ImageExtractionScreen() {
  const {
    Panel,
    Button,
    ConfidenceMeter,
    Checkbox,
    StatusChip
  } = NDS_ext;
  const [review, setReview] = React.useState({
    a: false,
    b: false,
    c: false
  });
  const fields = [{
    f: "Modality",
    v: "CR, computed radiography",
    c: 99
  }, {
    f: "Laterality",
    v: "Unspecified",
    c: 95
  }, {
    f: "Primary finding",
    v: "Consolidation",
    c: 78
  }, {
    f: "Location",
    v: "Ambiguous, lower lobe",
    c: 42,
    flag: true
  }, {
    f: "Secondary finding",
    v: "None observed",
    c: 91
  }, {
    f: "Hardware",
    v: "Endotracheal tube",
    c: 88
  }];
  const logs = [["10:42:01.102", "Orchestrator", "Initialized multi-agent workflow id 8A-9F2-C1", "var(--primary)"], ["10:42:01.450", "QualityAgent", "Evaluating DICOM headers. Pass.", "var(--success)"], ["10:42:02.015", "VisionAgent", "Running segmentation model v4.2", "var(--secondary)"], ["10:42:03.882", "VisionAgent", "Found 3 regions. Confidence 0.98, 0.94, 0.82.", "var(--secondary)"], ["10:42:04.100", "OCRAgent", "Extracting text overlays. 4 strings found.", "var(--secondary)"], ["10:42:04.550", "StructAgent", "Low confidence mapping on finding 3 to standard ontology.", "var(--error)"]];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: 26,
      fontWeight: 600,
      letterSpacing: "-0.02em"
    }
  }, "Image extraction"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "4px 0 0",
      fontSize: 13,
      color: "var(--on-surface-variant)"
    }
  }, "Session 8A-9F2-C1. Nine specialist agents run in sequence to structure the scan.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "md",
    icon: "restart_alt"
  }, "Reset"), /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "md",
    icon: "done_all"
  }, "Approve output"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr 360px",
      gap: "var(--space-md)",
      alignItems: "start"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Session image",
    icon: "imagesmode",
    bodyPadding: "0"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#0b0d12",
      padding: "var(--space-lg)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      minHeight: 320,
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 64,
      color: "var(--outline)"
    }
  }, "radiology"), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: 80,
      left: "50%",
      transform: "translateX(-30%)",
      border: "2px solid var(--primary-fixed-dim)",
      borderRadius: 2,
      width: 90,
      height: 70
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: -18,
      left: 0,
      background: "var(--primary)",
      color: "var(--on-primary)",
      fontSize: 9,
      fontWeight: 700,
      padding: "1px 4px",
      borderRadius: 2
    }
  }, "LOWER LOBE"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-sm) var(--space-md)",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--on-surface-variant)"
    }
  }, "IMG-2231.dcm"), /*#__PURE__*/React.createElement(StatusChip, {
    tone: "verified"
  }, "Loaded"))), /*#__PURE__*/React.createElement(Panel, {
    title: "Agent pipeline",
    icon: "lan",
    iconColor: "var(--primary)",
    bodyStyle: {
      display: "flex",
      flexDirection: "column",
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(PipelineStep, {
    state: "done",
    title: "Quality assessor",
    body: "Resolution 4K, contrast optimal, no artifacts detected."
  }), /*#__PURE__*/React.createElement(PipelineStep, {
    state: "done",
    title: "Vision analyzer",
    body: "Radiograph, AP view. Three key regions identified."
  }), /*#__PURE__*/React.createElement(PipelineStep, {
    state: "done",
    title: "OCR engine",
    body: "Extracted burned-in metadata and timestamp details."
  }), /*#__PURE__*/React.createElement(PipelineStep, {
    state: "active",
    title: "Semantic structuring",
    body: "Mapping visual findings to the SNOMED CT ontology.",
    detail: "MATCH (f:Finding {type:'opacity'})\nLINK TO (r:Region {name:'L-lobe'})"
  }), /*#__PURE__*/React.createElement(PipelineStep, {
    state: "pending",
    title: "Validation gate",
    body: "Waiting on structuring to finish before final confidence scoring."
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Extracted variables",
    icon: "data_object",
    bodyPadding: "0",
    actions: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: "var(--on-surface-variant)"
      }
    }, "12 found")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-xs) 0"
    }
  }, fields.map((row, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      padding: "6px var(--space-md)",
      borderBottom: i < fields.length - 1 ? "1px solid color-mix(in srgb, var(--outline-variant) 50%, transparent)" : "none"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 110,
      fontSize: 12,
      color: "var(--on-surface-variant)",
      display: "flex",
      alignItems: "center",
      gap: 4
    }
  }, row.flag ? /*#__PURE__*/React.createElement("span", {
    style: {
      width: 6,
      height: 6,
      borderRadius: "50%",
      background: "var(--error)"
    }
  }) : null, row.f), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1,
      fontSize: 13,
      fontWeight: 500,
      color: row.flag ? "var(--error)" : "var(--on-surface)"
    }
  }, row.v), /*#__PURE__*/React.createElement(ConfidenceMeter, {
    value: row.c,
    width: 56
  }))))), /*#__PURE__*/React.createElement(Panel, {
    title: "Required human review",
    icon: "rule",
    iconColor: "var(--error)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Checkbox, {
    checked: review.a,
    onChange: () => setReview({
      ...review,
      a: !review.a
    }),
    label: "Verify the ambiguous location, lower lobe versus lingula"
  }), /*#__PURE__*/React.createElement(Checkbox, {
    checked: review.b,
    onChange: () => setReview({
      ...review,
      b: !review.b
    }),
    label: "Confirm the primary finding of consolidation, confidence below 80 percent"
  }), /*#__PURE__*/React.createElement(Checkbox, {
    checked: review.c,
    onChange: () => setReview({
      ...review,
      c: !review.c
    }),
    label: "Acknowledge the missing laterality specification"
  }))))), /*#__PURE__*/React.createElement(Panel, {
    title: "Agent event stream",
    icon: "terminal",
    bodyPadding: "0",
    actions: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: "var(--on-surface-variant)"
      }
    }, "Auto scroll on")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--inverse-surface)",
      padding: "var(--space-md)",
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      lineHeight: "20px"
    }
  }, logs.map((l, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      color: "var(--inverse-on-surface)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--outline)"
    }
  }, l[0]), " ", /*#__PURE__*/React.createElement("span", {
    style: {
      color: l[3]
    }
  }, "[", l[1], "]"), " ", /*#__PURE__*/React.createElement("span", null, l[2]))))));
}
Object.assign(window, {
  ImageExtractionScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/ImageExtractionScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/InboxScreen.jsx
try { (() => {
// InboxScreen — triage of AI-raised items needing clinician action.
const NDS_inbox = window.NexusClinicalAIDesignSystem_29a409;
function InboxScreen() {
  const {
    Panel,
    Button,
    Tabs,
    StatusChip,
    ConfidenceMeter,
    SQLPreview
  } = NDS_inbox;
  const [tab, setTab] = React.useState("Action required");
  const [selected, setSelected] = React.useState(0);
  const items = [{
    tone: "critical",
    tag: "High risk",
    id: "PT-1145",
    time: "10 minutes ago",
    title: "Verify the AI-detected pulmonary anomalies",
    body: "Automated extraction flags a high probability of incidental nodules in the recent CT scan. Clinician verification is required before the report is finalized."
  }, {
    tone: "info",
    tag: "Missing data",
    id: "SESS-2231",
    time: "1 hour ago",
    title: "Missing image evidence for extraction",
    body: "The multimodal analysis agent could not locate the referenced MRI sequence in the linked PACS study. Manual linking is requested."
  }, {
    tone: "neutral",
    tag: "Review",
    id: "AUDIT-99",
    time: "4 hours ago",
    title: "Review batch extraction confidence anomalies",
    body: "The system detected a 15 percent drop in agent confidence across the last 50 oncology notes processed. Review the sample set for prompt tuning."
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "var(--space-md)",
      padding: "var(--space-md)",
      height: "100%",
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Clinical inbox",
    icon: "inbox",
    bodyPadding: "0",
    style: {
      minHeight: 0
    },
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "ghost",
      size: "sm",
      icon: "filter_list"
    }, "Filter")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-sm) var(--space-md) 0"
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    tabs: ["Action required", "Pending reviews", "System messages"],
    value: tab,
    onChange: setTab
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-sm)"
    }
  }, items.map((it, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    onClick: () => setSelected(i),
    style: {
      border: `1px solid ${selected === i ? "var(--primary)" : "var(--outline-variant)"}`,
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)",
      cursor: "pointer",
      background: selected === i ? "var(--surface-container-low)" : "var(--surface-container-lowest)",
      transition: "border-color 150ms ease"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(StatusChip, {
    tone: it.tone
  }, it.tag), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 12,
      color: "var(--on-surface-variant)"
    }
  }, it.id)), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)"
    }
  }, it.time)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600,
      color: "var(--on-surface)",
      marginBottom: 4
    }
  }, it.title), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: 13,
      color: "var(--on-surface-variant)",
      lineHeight: "18px"
    }
  }, it.body))))), /*#__PURE__*/React.createElement(Panel, {
    title: "PT-1145 context",
    icon: "description",
    bodyStyle: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      overflowY: "auto",
      maxHeight: "100%"
    },
    style: {
      minHeight: 0
    },
    actions: /*#__PURE__*/React.createElement(Button, {
      variant: "outline",
      size: "sm",
      icon: "open_in_new"
    }, "Open full session")
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 14,
      fontWeight: 600
    }
  }, "AI finding summary"), /*#__PURE__*/React.createElement(StatusChip, {
    tone: "critical"
  }, "Action required")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "0 0 var(--space-md)",
      fontSize: 14,
      lineHeight: "20px",
      color: "var(--on-surface)"
    }
  }, "The vision language model identified structural irregularities consistent with early stage pulmonary nodules in the right lower lobe. This finding was not explicitly mentioned in the original radiology dictation."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    size: "sm",
    icon: "check"
  }, "Verify finding"), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm",
    icon: "close"
  }, "Reject"))), /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      marginBottom: 8
    }
  }, "Agent confidence"), /*#__PURE__*/React.createElement(ConfidenceMeter, {
    value: 82,
    width: 220
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "var(--space-sm) 0 0",
      fontSize: 12,
      color: "var(--on-surface-variant)",
      lineHeight: "16px"
    }
  }, "Model Vision v3. Confidence was reduced by poor image contrast in slices 44 to 48.")), /*#__PURE__*/React.createElement("div", {
    style: {
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      marginBottom: 8
    }
  }, "Source evidence"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 96,
      height: 72,
      borderRadius: "var(--radius-sm)",
      background: "#0b0d12",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 28,
      color: "var(--outline)"
    }
  }, "radiology")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: 13,
      color: "var(--on-surface)",
      lineHeight: "18px"
    }
  }, "Excerpt from sequence 3, slice 46. Hyperdensity noted at coordinates x 142, y 88."), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => e.preventDefault(),
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: "var(--primary)",
      textDecoration: "none",
      marginTop: 6,
      display: "inline-block"
    }
  }, "View full study")))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      marginBottom: 8
    }
  }, "Extraction query trace"), /*#__PURE__*/React.createElement(SQLPreview, {
    label: "Query",
    html: `<span style="color:var(--primary);font-weight:600">SELECT</span> patient_id, scan_date, modality\n<span style="color:var(--primary);font-weight:600">FROM</span> pacs_metadata\n<span style="color:var(--primary);font-weight:600">WHERE</span> study_id = <span style="color:var(--tertiary)">'S-1145-CT'</span>\n    <span style="color:var(--primary);font-weight:600">AND</span> has_findings = <span style="color:var(--tertiary)">TRUE</span>;`
  }))));
}
Object.assign(window, {
  InboxScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/InboxScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/MultimodalQAScreen.jsx
try { (() => {
// MultimodalQAScreen — ask questions across a patient's records; cited answers.
const NDS_qa = window.NexusClinicalAIDesignSystem_29a409;
function CitationMark({
  n
}) {
  return /*#__PURE__*/React.createElement("sup", null, /*#__PURE__*/React.createElement("button", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: 16,
      height: 16,
      borderRadius: "var(--radius-sm)",
      background: "var(--secondary-container)",
      color: "var(--on-secondary-container)",
      border: "1px solid var(--outline-variant)",
      fontFamily: "var(--font-mono)",
      fontSize: 10,
      cursor: "pointer",
      verticalAlign: "super"
    }
  }, n));
}
function MultimodalQAScreen() {
  const {
    Panel,
    Button,
    Textarea,
    Select,
    Checkbox,
    ConfidenceMeter,
    DataTable
  } = NDS_qa;
  const [sources, setSources] = React.useState({
    notes: true,
    imaging: true,
    labs: true
  });
  const ctxCols = [{
    key: "ref",
    header: "Ref",
    mono: true,
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--primary)",
        fontWeight: 600
      }
    }, "[", r.ref, "]")
  }, {
    key: "type",
    header: "Type",
    render: r => /*#__PURE__*/React.createElement("span", {
      style: {
        display: "inline-block",
        padding: "1px 6px",
        borderRadius: "var(--radius-sm)",
        fontSize: 10,
        fontWeight: 600,
        background: r.type === "Image" ? "var(--tertiary-fixed)" : r.type === "Text" ? "var(--secondary-fixed)" : "var(--surface-variant)",
        color: "var(--on-surface-variant)"
      }
    }, r.type)
  }, {
    key: "date",
    header: "Date",
    mono: true
  }, {
    key: "rel",
    header: "Relevance",
    render: r => /*#__PURE__*/React.createElement("div", {
      style: {
        width: 120
      }
    }, /*#__PURE__*/React.createElement(ConfidenceMeter, {
      value: r.rel,
      width: 80,
      showValue: false,
      color: "var(--primary)"
    }))
  }, {
    key: "name",
    header: "Source document"
  }];
  const ctx = [{
    ref: 1,
    type: "Image",
    date: "2024-01-05",
    rel: 89,
    name: "MRI Abdomen without contrast, Series 4"
  }, {
    ref: 2,
    type: "Text",
    date: "2023-10-12",
    rel: 76,
    name: "Radiology report, previous MRI findings"
  }, {
    ref: 3,
    type: "Text",
    date: "2024-01-08",
    rel: 62,
    name: "Oncology clinic note, Dr. Vance"
  }, {
    ref: 4,
    type: "Struct",
    date: "2024-01-04",
    rel: 45,
    name: "Comprehensive metabolic panel"
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      height: "100%",
      boxSizing: "border-box"
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    bodyPadding: "var(--space-sm) var(--space-md)"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: "var(--radius-full)",
      background: "var(--surface-container-highest)",
      border: "1px solid var(--outline-variant)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 20,
      color: "var(--on-surface-variant)"
    }
  }, "person")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 15,
      fontWeight: 600
    }
  }, "Sarah Jenkins"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: "var(--on-surface-variant)"
    }
  }, "MRN-99824-A. Date of birth 04/12/1965, age 58."))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement(NDS_qa.StatusChip, {
    tone: "critical",
    icon: "warning"
  }, "High risk"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)"
    }
  }, "Agents active: Retrieval, Context, Citation")))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "280px 1fr 320px",
      gap: "var(--space-md)",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(Panel, {
    title: "Intelligence query",
    icon: "search",
    bodyStyle: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      height: "100%",
      boxSizing: "border-box"
    },
    style: {
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      display: "block",
      marginBottom: 6
    }
  }, "Natural language question"), /*#__PURE__*/React.createElement(Textarea, {
    rows: 4,
    defaultValue: "Has there been any progression in the secondary hepatic lesions since the last scan in October?"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: "1px solid var(--outline-variant)",
      paddingTop: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      display: "block",
      marginBottom: 6
    }
  }, "Date range"), /*#__PURE__*/React.createElement(Select, {
    defaultValue: "Last 6 months"
  }, /*#__PURE__*/React.createElement("option", null, "Last 6 months"), /*#__PURE__*/React.createElement("option", null, "Last 12 months"), /*#__PURE__*/React.createElement("option", null, "All time"))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      display: "block",
      marginBottom: 8
    }
  }, "Source types"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Checkbox, {
    checked: sources.notes,
    onChange: () => setSources({
      ...sources,
      notes: !sources.notes
    }),
    label: "Clinical notes (text)"
  }), /*#__PURE__*/React.createElement(Checkbox, {
    checked: sources.imaging,
    onChange: () => setSources({
      ...sources,
      imaging: !sources.imaging
    }),
    label: "Imaging reports (vector)"
  }), /*#__PURE__*/React.createElement(Checkbox, {
    checked: sources.labs,
    onChange: () => setSources({
      ...sources,
      labs: !sources.labs
    }),
    label: "Lab results (structured)"
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "auto"
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "primary",
    icon: "auto_awesome",
    fullWidth: true
  }, "Synthesize answer"))), /*#__PURE__*/React.createElement(Panel, {
    title: "Agent synthesis",
    icon: "forum",
    bodyStyle: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-lg)",
      overflowY: "auto",
      maxHeight: "100%"
    },
    style: {
      minHeight: 0
    },
    actions: /*#__PURE__*/React.createElement(ConfidenceMeter, {
      value: 92,
      label: "Synthesis confidence",
      width: 90
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      alignSelf: "flex-end",
      maxWidth: "85%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-lg) var(--radius-lg) 0 var(--radius-lg)",
      padding: "var(--space-md)",
      fontSize: 14,
      color: "var(--on-surface)"
    }
  }, "Has there been any progression in the secondary hepatic lesions since the last scan in October?"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      textAlign: "right",
      marginTop: 4
    }
  }, "10:42 AM")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-md)",
      maxWidth: "92%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: "var(--radius-full)",
      background: "var(--primary-fixed)",
      border: "1px solid var(--primary-fixed-dim)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
      marginTop: 4
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 18,
      color: "var(--primary)"
    }
  }, "neurology")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-lowest)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-lg) var(--radius-lg) var(--radius-lg) 0",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "0 0 var(--space-md)",
      fontSize: 14,
      lineHeight: "20px",
      color: "var(--on-surface)"
    }
  }, "Comparing the abdominal MRI from October 12 with the recent scan on January 5, there is evidence of slight progression."), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "0 0 var(--space-md)",
      fontSize: 14,
      lineHeight: "20px",
      color: "var(--on-surface)"
    }
  }, "The largest secondary lesion in segment VI increased from 1.2 cm to roughly 1.5 cm.", /*#__PURE__*/React.createElement(CitationMark, {
    n: 1
  }), " Smaller adjacent satellite nodules appear stable, and no new definitive lesions were identified in the remaining hepatic segments.", /*#__PURE__*/React.createElement(CitationMark, {
    n: 2
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      borderTop: "1px solid var(--outline-variant)",
      paddingTop: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      marginBottom: 6
    }
  }, "Primary evidence"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      background: "var(--surface-container)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 13,
      color: "var(--on-surface)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: 11,
      background: "color-mix(in srgb, var(--outline-variant) 40%, transparent)",
      padding: "1px 5px",
      borderRadius: 3,
      marginRight: 6
    }
  }, "[1]"), "MRI Abdomen without contrast, January 5"), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => e.preventDefault(),
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: "var(--primary)",
      textDecoration: "none"
    }
  }, "View source")))), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 4
    }
  }, "Context agent. 10:42 AM")))), /*#__PURE__*/React.createElement(Panel, {
    title: "Source viewer",
    icon: "image",
    bodyPadding: "0",
    style: {
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "#0b0d12",
      padding: "var(--space-md)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      height: 150
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 40,
      color: "var(--outline)"
    }
  }, "radiology")), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)",
      marginBottom: 6
    }
  }, "Extracted finding"), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)",
      fontSize: 13,
      color: "var(--on-surface)",
      lineHeight: "18px"
    }
  }, "Lesion in segment VI measuring 1.5 by 1.4 cm, increased from a prior 1.2 cm. Margins remain well defined."), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-md)",
      display: "flex",
      flexDirection: "column",
      gap: 6
    }
  }, [["Study date", "2024-01-05"], ["Modality", "MRI without contrast"], ["Vector similarity", "0.8924"], ["Agent", "Vision Extractor v3"]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--on-surface-variant)"
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--on-surface)"
    }
  }, v))))))), /*#__PURE__*/React.createElement(Panel, {
    title: "Retrieved context sources",
    icon: "library_books",
    bodyPadding: "0",
    actions: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 11,
        color: "var(--on-surface-variant)"
      }
    }, "Top 4 vectorized matches")
  }, /*#__PURE__*/React.createElement(DataTable, {
    columns: ctxCols,
    rows: ctx
  })));
}
Object.assign(window, {
  MultimodalQAScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/MultimodalQAScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/clinician_ai_kit/PatientProfileScreen.jsx
try { (() => {
// PatientProfileScreen — unified patient record with timeline and AI copilot.
const NDS_pt = window.NexusClinicalAIDesignSystem_29a409;
function ProfileSection({
  title,
  action,
  children
}) {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      marginBottom: "var(--space-xl)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)"
    }
  }, title), action), children);
}
function PatientProfileScreen({
  onBack
}) {
  const {
    Panel,
    Button,
    Tabs,
    StatusChip,
    ConfidenceMeter,
    Input
  } = NDS_pt;
  const [tab, setTab] = React.useState("Timeline");
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      height: "100%"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderBottom: "1px solid var(--outline-variant)",
      padding: "var(--space-md) var(--space-lg)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xl)"
    }
  }, onBack ? /*#__PURE__*/React.createElement(NDS_pt.Button, {
    variant: "ghost",
    size: "sm",
    icon: "list",
    onClick: onBack
  }, "Back to queue") : null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: 22,
      fontWeight: 600,
      letterSpacing: "-0.02em"
    }
  }, "Jonathan Doe"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, "PT-8829. Male, 62 years.")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(StatusChip, {
    tone: "critical",
    icon: "warning"
  }, "High risk"), /*#__PURE__*/React.createElement(StatusChip, {
    tone: "info"
  }, "Oncology"), /*#__PURE__*/React.createElement(StatusChip, {
    tone: "info"
  }, "NSCLC"))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xl)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "right"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      color: "var(--on-surface-variant)"
    }
  }, "Data completeness"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 4
    }
  }, /*#__PURE__*/React.createElement(ConfidenceMeter, {
    value: 88,
    width: 96,
    color: "var(--primary)"
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "280px 1fr 340px",
      flex: 1,
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderRight: "1px solid var(--outline-variant)",
      padding: "var(--space-lg)",
      overflowY: "auto"
    }
  }, /*#__PURE__*/React.createElement(ProfileSection, {
    title: "Demographics"
  }, [["Date of birth", "05/12/1961"], ["Weight", "82 kg"], ["Height", "178 cm"], ["Blood type", "O positive"]].map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: 13,
      padding: "3px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--on-surface-variant)"
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--on-surface)"
    }
  }, v)))), /*#__PURE__*/React.createElement(ProfileSection, {
    title: "Active diagnoses",
    action: /*#__PURE__*/React.createElement(NDS_pt.IconButton, {
      icon: "edit",
      label: "Edit diagnoses",
      size: "sm"
    })
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-low)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, "Non-small cell lung cancer"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, "Stage IIIa. Diagnosed 2022.")), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-low)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600
    }
  }, "Hypertension"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, "Primary. Managed.")))), /*#__PURE__*/React.createElement(ProfileSection, {
    title: "Current medications"
  }, [["Pembrolizumab", "200 mg IV every 3 weeks"], ["Lisinopril", "10 mg by mouth daily"]].map(([m, d]) => /*#__PURE__*/React.createElement("div", {
    key: m,
    style: {
      display: "flex",
      gap: "var(--space-sm)",
      padding: "4px 0"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 16,
      color: "var(--secondary)",
      marginTop: 1
    }
  }, "medication"), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: "var(--on-surface)"
    }
  }, m), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)"
    }
  }, d))))), /*#__PURE__*/React.createElement(ProfileSection, {
    title: "Allergies"
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--error-container)",
      border: "1px solid color-mix(in srgb, var(--error) 30%, transparent)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      fontWeight: 600,
      color: "var(--on-error-container)"
    }
  }, "Penicillin"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-error-container)",
      marginTop: 2
    }
  }, "Reaction: hives, anaphylaxis risk.")))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-low)",
      display: "flex",
      flexDirection: "column",
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderBottom: "1px solid var(--outline-variant)",
      padding: "var(--space-sm) var(--space-lg) 0"
    }
  }, /*#__PURE__*/React.createElement(Tabs, {
    tabs: ["Timeline", "Sessions", "Notes", "Images", "Metrics"],
    value: tab,
    onChange: setTab
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: "auto",
      padding: "var(--space-xl)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      borderLeft: "1px solid var(--outline-variant)",
      marginLeft: 12,
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xl)",
      paddingLeft: "var(--space-xl)"
    }
  }, /*#__PURE__*/React.createElement(TimelineCard, {
    icon: "description",
    title: "Oncology review note extracted",
    meta: "Dr. Sarah Chen. Today, 09:42 AM",
    verified: true,
    body: "Patient reports mild fatigue after infusion. No new respiratory symptoms. Tumor markers remain stable. Continue the current immunotherapy regimen."
  }), /*#__PURE__*/React.createElement(TimelineCard, {
    icon: "imagesmode",
    title: "CT thorax with contrast uploaded",
    meta: "System auto ingest. Oct 24, 2023, 2:15 PM",
    findings: ["Primary lesion in the right upper lobe measures 3.2 cm, down from 3.4 cm.", "No new lymphadenopathy.", "Mild pleural effusion noted at the right base."],
    conf: 94
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface)",
      borderLeft: "1px solid var(--outline-variant)",
      display: "flex",
      flexDirection: "column",
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md) var(--space-lg)",
      borderBottom: "1px solid var(--outline-variant)",
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 20,
      color: "var(--primary)",
      fontVariationSettings: "'FILL' 1"
    }
  }, "smart_toy"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 15,
      fontWeight: 600
    }
  }, "AI copilot")), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflowY: "auto",
      padding: "var(--space-lg)",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--primary-fixed)",
      border: "1px solid var(--primary-fixed-dim)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6,
      marginBottom: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 16,
      color: "var(--primary)"
    }
  }, "lightbulb"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 700,
      color: "var(--on-primary-fixed-variant)"
    }
  }, "Clinical insight")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: 13,
      lineHeight: "18px",
      color: "var(--on-surface)"
    }
  }, "Recent CT volumetrics and clinical notes suggest a partial response to pembrolizumab. Pneumonitis risk stays elevated given the prior radiation history."), /*#__PURE__*/React.createElement("a", {
    href: "#",
    onClick: e => e.preventDefault(),
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: "var(--primary)",
      textDecoration: "none",
      marginTop: 8,
      display: "inline-block"
    }
  }, "View source guideline")), /*#__PURE__*/React.createElement("div", {
    style: {
      alignSelf: "flex-end",
      maxWidth: "85%",
      background: "var(--surface-container)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-sm) var(--space-md)",
      fontSize: 13
    }
  }, "Summarize the last three creatinine results."), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-lowest)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)",
      fontSize: 13
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 8
    }
  }, "Recent creatinine trend:"), /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      paddingLeft: 18,
      color: "var(--on-surface)"
    }
  }, /*#__PURE__*/React.createElement("li", null, "Oct 24: 1.1 mg/dL"), /*#__PURE__*/React.createElement("li", null, "Sep 12: 1.0 mg/dL"), /*#__PURE__*/React.createElement("li", null, "Aug 05: 1.2 mg/dL")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "8px 0 0",
      fontSize: 12,
      color: "var(--on-surface-variant)"
    }
  }, "Values stay within the normal range of 0.7 to 1.3 mg/dL."))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: "var(--space-md) var(--space-lg)",
      borderTop: "1px solid var(--outline-variant)"
    }
  }, /*#__PURE__*/React.createElement(Input, {
    size: "md",
    icon: "chat",
    placeholder: "Ask the copilot about this patient"
  })))));
}
function TimelineCard({
  icon,
  title,
  meta,
  body,
  findings,
  verified,
  conf
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      left: "calc(-1 * var(--space-xl) - 12px)",
      top: 0,
      width: 24,
      height: 24,
      borderRadius: "var(--radius-full)",
      background: "var(--surface)",
      border: "1px solid var(--outline-variant)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "material-symbols-outlined",
    style: {
      fontSize: 14,
      color: "var(--secondary)"
    }
  }, icon)), /*#__PURE__*/React.createElement("div", {
    style: {
      background: "var(--surface-container-lowest)",
      border: "1px solid var(--outline-variant)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "flex-start"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      fontWeight: 600
    }
  }, title), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      color: "var(--on-surface-variant)",
      marginTop: 2
    }
  }, meta)), verified ? /*#__PURE__*/React.createElement(NDS_pt.StatusChip, {
    tone: "verified",
    icon: "verified"
  }, "Verified") : null), body ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "var(--space-sm) 0 0",
      fontSize: 13,
      lineHeight: "18px",
      color: "var(--on-surface)"
    }
  }, body) : null, findings ? /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11,
      fontWeight: 700,
      color: "var(--on-surface-variant)",
      marginBottom: 4
    }
  }, "AI findings"), /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      paddingLeft: 18,
      fontSize: 13,
      color: "var(--on-surface)",
      lineHeight: "20px"
    }
  }, findings.map((f, i) => /*#__PURE__*/React.createElement("li", {
    key: i
  }, f))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement(NDS_pt.ConfidenceMeter, {
    value: conf,
    label: "AI confidence",
    width: 120
  }))) : null));
}
Object.assign(window, {
  PatientProfileScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/clinician_ai_kit/PatientProfileScreen.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.DataTable = __ds_scope.DataTable;

__ds_ns.SQLPreview = __ds_scope.SQLPreview;

__ds_ns.ConfidenceMeter = __ds_scope.ConfidenceMeter;

__ds_ns.EvidenceCitation = __ds_scope.EvidenceCitation;

__ds_ns.StatusChip = __ds_scope.StatusChip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Textarea = __ds_scope.Textarea;

__ds_ns.Panel = __ds_scope.Panel;

__ds_ns.RoleSwitcher = __ds_scope.RoleSwitcher;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
