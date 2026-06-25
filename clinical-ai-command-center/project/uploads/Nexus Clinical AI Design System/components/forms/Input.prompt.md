Form controls — text input, multi-line textarea, native select, and checkbox — all system-styled with 1px outlines and primary-blue focus.

```jsx
<Input icon="search" placeholder="Search Patients or IDs..." />
<Textarea rows={4} placeholder="Summarize recent MRI findings..." />
<Select><option>Last 6 Months</option><option>All Time</option></Select>
<Checkbox checked label="Clinical Notes (Text)" onChange={fn} />
```

Inputs/selects come in `sm` (36px) and `md` (44px). Pass `invalid` for error state, `icon` for a leading glyph.
