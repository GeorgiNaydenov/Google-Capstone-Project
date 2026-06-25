Data-display primitives — the dense clinical `DataTable` and the `SQLPreview` transparency block.

```jsx
<DataTable
  columns={[
    { key: "id", header: "Patient ID", mono: true },
    { key: "name", header: "Name" },
    { key: "risk", header: "Risk Status", render: r => <StatusChip tone={r.tone}>{r.risk}</StatusChip> },
  ]}
  rows={patients}
  onRowClick={open}
/>

<SQLPreview code={"SELECT * FROM patients_core\nWHERE risk_score >= 0.8;"} onCopy={copy} />
```

`DataTable` gives sticky headers, zebra striping, 36px rows and 12px cell padding; columns support `mono`, `align`, and custom `render`. `SQLPreview` renders mono code on a tonal block; pass pre-highlighted `html` for syntax coloring.
