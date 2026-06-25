# clinical-ai-command-center — Design System & Visual Prototype

The **Nexus Clinical AI Design System** and interactive visual prototype that serves as the design reference for the clinician-facing application. Originally exported from Claude Design as a handoff bundle.

---

## Purpose

This directory contains the design assets and static prototype that define the visual language, interaction patterns, and feature scope for the clinical product. It is the **design reference** — the production implementation lives in `frontend/` and `clinical_app/`.

The main design file is `project/Clinician AI KIT.dc.html` — this is the primary prototype the production frontend was built from.

---

## Structure

```
project/
├── Clinician AI KIT.dc.html         # Main prototype entry point
├── assets/
│   ├── logo.png                     # Application logo
│   └── mark.png                     # Application mark/icon
├── support.js                       # Prototype runtime support
└── uploads/
    └── Nexus Clinical AI Design System/
        ├── readme.md                # Design system documentation
        ├── styles.css               # Global design system styles
        ├── tokens/                  # Design tokens
        │   ├── colors.css           # Color palette (primary, secondary, semantic)
        │   ├── elevation.css        # Shadow and depth tokens
        │   ├── fonts.css            # Font family definitions
        │   ├── spacing.css          # Spacing scale
        │   └── typography.css       # Typography scale
        ├── components/              # React component library
        │   ├── core/                # Button, Icon, IconButton
        │   ├── data/                # DataTable, SQLPreview
        │   ├── feedback/            # ConfidenceMeter, EvidenceCitation, StatusChip
        │   ├── forms/               # Input, Select, Textarea, Checkbox
        │   ├── layout/              # Panel
        │   └── navigation/          # RoleSwitcher, Tabs
        ├── guidelines/              # Visual design guidelines
        │   ├── brand-*.card.html    # Brand identity cards
        │   ├── colors-*.card.html   # Color system cards
        │   ├── spacing-*.card.html  # Spacing system cards
        │   └── type-*.card.html     # Typography cards
        └── ui_kits/
            └── clinician_ai_kit/    # 16-screen prototype
                ├── index.html       # Kit entry point
                ├── AppShell.jsx     # Application shell
                ├── DashboardScreen.jsx
                ├── DbIntelligenceScreen.jsx
                ├── ImageExtractionScreen.jsx
                ├── InboxScreen.jsx
                ├── MultimodalQAScreen.jsx
                └── PatientProfileScreen.jsx
```

---

## Design System Components

### Core
- **Button** — Primary, secondary, and ghost variants with clinical severity theming
- **Icon** — Clinical icon set with consistent sizing
- **IconButton** — Compact icon-only button for toolbars

### Data Display
- **DataTable** — Sortable, filterable clinical data tables
- **SQLPreview** — SQL query preview with syntax highlighting

### Feedback
- **ConfidenceMeter** — Visual confidence indicator (0-100%) with threshold markers
- **EvidenceCitation** — Clickable evidence citations with source attribution
- **StatusChip** — Status indicators (queued, running, review, completed, failed)

### Forms
- **Input** — Text input with validation states
- **Select** — Dropdown with clinical option formatting
- **Textarea** — Multi-line input for clinical notes
- **Checkbox** — Approval and consent checkboxes

### Layout
- **Panel** — Content container with header, actions, and collapsibility

### Navigation
- **RoleSwitcher** — Clinician/admin role toggle
- **Tabs** — Content tab navigation

---

## Design Tokens

The design system uses CSS custom properties organized into five categories:

- **Colors** — Clinical palette with primary (blue), secondary (teal), semantic (success/warning/danger/info), and surface colors
- **Typography** — Title, body, and monospace scales
- **Spacing** — 4px-based spacing scale
- **Elevation** — Shadow depth tokens for layered UI
- **Fonts** — System font stack with monospace fallback for clinical data

---

## Relationship to Production

| Aspect | Design System (here) | Production (frontend/) |
|--------|---------------------|----------------------|
| Purpose | Visual reference and component specs | Running application |
| Technology | Static HTML/JSX prototypes | React + Vite + TypeScript |
| Data | Hardcoded examples | API-driven from clinical_app |
| Interactivity | Click-through prototype | Full agent-connected workflows |
