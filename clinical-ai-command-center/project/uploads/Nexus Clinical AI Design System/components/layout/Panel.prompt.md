The fundamental work-surface container; everything in Nexus lives inside a Panel. White background, 1px outline, 8px radius, optional bordered header — never a drop shadow.

```jsx
<Panel title="Priority Patient Queue" icon="priority_high"
       actions={<Button variant="ghost" size="sm">View All</Button>}>
  …panel content…
</Panel>
```

Header is optional (omit `title` for a plain frame). `actions` render on the right of the header. Use `bodyPadding="0"` for edge-to-edge tables.
