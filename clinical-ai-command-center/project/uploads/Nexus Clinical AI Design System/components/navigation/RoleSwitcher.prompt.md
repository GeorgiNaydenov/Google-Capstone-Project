Navigation controls — a segmented `RoleSwitcher` and an underline `Tabs` bar.

```jsx
<RoleSwitcher options={["Clinician", "Admin"]} value={role} onChange={setRole} />
<Tabs tabs={["Timeline", "Sessions", "Notes", "Images"]} value={tab} onChange={setTab} />
```

`RoleSwitcher` is a compact uppercase segmented control (active = primary fill). `Tabs` uses a 2px primary underline for the active section.
