import React from "react";

/**
 * DataTable — the core dense table. Sticky header, zebra striping,
 * 36px rows, 12px horizontal cell padding, hairline dividers.
 *
 * columns: [{ key, header, align?, mono?, width?, render?(row) }]
 * rows: array of objects keyed by column.key
 */
export function DataTable({ columns = [], rows = [], zebra = true, onRowClick, style }) {
  return (
    <div style={{ overflow: "auto", ...style }}>
      <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", whiteSpace: "nowrap" }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                style={{
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
                  textAlign: c.align || "left",
                }}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.id || i}
              onClick={() => onRowClick && onRowClick(row)}
              style={{
                height: "var(--row-height-sm)",
                background: zebra && i % 2 === 1 ? "var(--surface-container-low)" : "var(--surface-container-lowest)",
                borderBottom: "var(--border-width) solid color-mix(in srgb, var(--outline-variant) 50%, transparent)",
                cursor: onRowClick ? "pointer" : "default",
                transition: "background-color 120ms ease",
              }}
              onMouseEnter={(e) => { e.currentTarget.style.background = "var(--surface-container-high)"; }}
              onMouseLeave={(e) => { e.currentTarget.style.background = zebra && i % 2 === 1 ? "var(--surface-container-low)" : "var(--surface-container-lowest)"; }}
            >
              {columns.map((c) => (
                <td
                  key={c.key}
                  style={{
                    padding: "0 12px",
                    fontFamily: c.mono ? "var(--font-mono)" : "var(--font-sans)",
                    fontSize: c.mono ? "12px" : "13px",
                    color: "var(--on-surface)",
                    textAlign: c.align || "left",
                  }}
                >
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
