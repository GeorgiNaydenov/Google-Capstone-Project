# Clinician AI KIT — Design System

A design system for **Clinician AI KIT**, a multi-agent clinical intelligence command center. Clinicians and medical researchers use it to synthesize fragmented patient data, extract evidence from unstructured records (notes, pathology, imaging), and act on AI-generated insights inside a dense, high-trust workspace.

The product was originally prototyped as "Nexus Clinical AI / Clinical Command" and has been rebranded to **Clinician AI KIT**. The application surface in this system carries the new name and logo; the underlying visual language is unchanged.

> Personality: authoritative, precise, evidence-driven. The UI prioritizes utility over decoration and uses a "compact-first" philosophy to maximize the information visible on screen.

## Sources

This system was built from an attached codebase of product screens (Google Stitch export):

- **Codebase:** `stitch_clinical_intelligence_command_center/` (also mirrored under `uploads/Design scope and approach/uploads/...`). Each subfolder holds a `code.html` (Tailwind + Material Symbols) and a `screen.png`.
- **Design spec:** `stitch_clinical_intelligence_command_center/nexus_clinical_ai/DESIGN.md` — the source of truth for colors, type scale, spacing, radii, and component descriptions. All token values here are taken verbatim from it.
- **Screens reviewed:** clinician dashboard, database intelligence agent, multimodal patient Q&A agent, session image extraction agent, patient profile, patient queue, clinical inbox, public demo landing, admin dashboard, agent configuration, users & roles, data & storage management.
- **Logo:** provided by the user (`assets/clinician-ai-kit-logo.png`, cropped mark `assets/clinician-ai-kit-mark.png`): a blue ECG/heartbeat line flowing into a neural-network node graph.

No font binaries were provided. Inter, JetBrains Mono, and Material Symbols Outlined load from Google Fonts CDN (see Caveats).

---

## CONTENT FUNDAMENTALS

How copy is written in Clinician AI KIT:

- **Voice:** clinical, factual, and confident. The system states findings plainly ("High risk classifications rose steadily over the past 30 days") rather than hedging or selling.
- **Person:** addresses the clinician directly and warmly at the top level ("Good morning, Dr. Miller", "You have 7 high risk patients"). Within data and agent output it is impersonal and descriptive ("The agent processed 14,203 records").
- **Casing:** Title-case page titles ("Database Intelligence"). Sentence case for body, descriptions, table reasons, and button labels ("Run query", "Synthesize answer", "View all"). UPPERCASE only for small metadata labels (`AI FLAG REASON`, `EXTRACTED VARIABLES`) using the `label-caps` style with letter-spacing.
- **Numbers & units:** spelled out in prose ("72 percent confidence", "1.2 cm to roughly 1.5 cm", "200 mg IV every 3 weeks"). Raw numerals stay in tables, metrics, and mono fields ("98%", "PT-8829", "0.8924").
- **No arrows.** Do not use arrow glyphs (→, ←) in copy or as decoration. Use plain link text ("View all", "View source", "View full study"). Architecture and pipeline relationships are shown by ordering and layout, not arrow connectors.
- **No em dashes.** Use periods, commas, or restructure the sentence. Use the middot ("·") only inside dense metadata strings, never as a sentence dash.
- **Well-defined, complete copy.** Avoid vague fragments. Every alert states what was found and what the clinician should do ("Clinician verification is required before the report is finalized").
- **Emoji:** never. The brand uses Material Symbols icons, not emoji.
- **Examples of good copy:**
  - Empty/automated states: "Routine AI summary generated with no acute flags."
  - Alerts: "Elevated troponin found in the most recent lab extraction."
  - Recommendations: "The previous text extraction scored 72 percent confidence. Re-processing with high resolution OCR is recommended."

---

## VISUAL FOUNDATIONS

- **Color:** rooted in "Clinical Blue" (`--primary #004ac6`) for trust and action. Slate secondary (`#515f74`) grounds structure; burnt-amber tertiary (`#943700`) marks AI/attention; critical red (`#ba1a1a`), warning amber, stable blue, and verified green carry data semantics. AI and vector features use blue and amber accents. Palette is a Material-3 tonal system; see the Colors cards.
- **Type:** Inter for all UI, JetBrains Mono for code, IDs, numbers, and timestamps. A tight, dense scale: page-title 26/600 (tracking -0.02em), section-title 18/600, panel-title 15/600, body 14/400, table 13/400, label-caps 11/700 (tracking 0.05em, uppercase), mono 12/400.
- **Spacing & density:** 4px base unit (4 / 8 / 12 / 16 / 24 / 32). Whitespace defines groups, not breathability. Standardized control and row heights: 36px compact, 44px default. Fixed structural widths: sidebar 240px, side panels 280–320px, fluid work-surface between.
- **Backgrounds:** flat tonal surfaces only. App shell sits on `--background #faf8ff`; work panels are white (`--surface-container-lowest`). No gradients, no photographic hero imagery, no textures or patterns. The only "dark" surfaces are image/scan viewers (near-black) and the agent event stream (inverse surface).
- **Elevation:** depth is communicated by **tonal layering and 1px low-contrast outlines**, not shadows. Panels and cards are a flat white fill with a `--outline-variant #c3c6d7` hairline border. Shadows exist only as tokens for transient floating UI (menus, dialogs).
- **Corner radii (Soft-Geometric):** 4px for chips, tags, checkboxes and in-table elements; 6px (default) for buttons and inputs; 8px for container panels and modals; full for pills and avatars.
- **Cards/panels:** white fill, 1px hairline border, 8px radius, optional tonal header bar (`--surface-container-low`) with an icon + panel-title and trailing actions. No shadow, no colored left-border accent (except a single 3px critical-red rule on alert KPI tiles).
- **Borders:** 1px hairlines everywhere. Active focus is a 2px primary-blue border, never an outer glow.
- **Hover states:** subtle tonal background shift (`--surface-container-high/highest`); links do not underline by default. Buttons darken slightly.
- **Press/active states:** color shift, not scale. Active nav items get a slate-container fill and a 3px primary left border.
- **Transparency & blur:** used sparingly. `color-mix` produces 10–25% tints for chip backgrounds, status fills, and zebra dividers. No backdrop blur.
- **Animation:** restrained, functional. 120–300ms ease transitions on background, border, width (confidence meters). No bounces, no infinite decorative loops.
- **Imagery vibe:** clinical scans render on near-black backgrounds; the only brand imagery is the blue logo mark. No warm/lifestyle photography.
- **Layout rules:** fixed sidebar + top bar; fluid scrolling work-surface. Tables get sticky headers, zebra striping (`--surface-container-low` on alternate rows), 36px rows, 12px horizontal cell padding.

---

## ICONOGRAPHY

- **System:** [Material Symbols Outlined](https://fonts.google.com/icons) (Google), loaded from CDN. This is the codebase's native icon set (`<span class="material-symbols-outlined">name</span>`), reproduced faithfully.
- **Style:** outlined, weight 400, optical size matched to pixel size. Active/selected nav and emphasis icons use `FILL 1`. Default neutral color is `--on-surface-variant`; semantic icons inherit status colors (primary, tertiary, error, success).
- **The `Icon` component** wraps Material Symbols with `name`, `size`, `fill`, `weight`, `grade` props. Prefer it in React; the raw `.material-symbols-outlined` class works in plain HTML cards.
- **No emoji. No unicode glyph icons.** No hand-drawn SVG icons. The only custom SVG-like asset is the PNG logo mark.
- **Common glyphs:** dashboard, inbox, groups, biotech, neurology, database, policy, monitor_heart, smart_toy, auto_awesome, account_tree, warning, priority_high, verified, fact_check, terminal, show_chart, insights, history, sync, settings, lightbulb, medication, radiology. See the "Iconography" card.
- **Substitution flag:** none. The icon set is used directly from its official CDN, matching the source.

---

## Index / Manifest

Root files:
- `styles.css` — global entry point (import manifest only). Consumers link this.
- `tokens/` — `fonts.css`, `colors.css`, `typography.css`, `spacing.css`, `elevation.css`.
- `assets/` — `clinician-ai-kit-logo.png` (full lockup, transparent bg), `clinician-ai-kit-mark.png` (cropped mark).
- `SKILL.md` — Agent Skills entry point.

Components (`components/<group>/`, mounted from `window.NexusClinicalAIDesignSystem_29a409`):
- `core/` — Button, IconButton, Icon
- `forms/` — Input, Textarea, Select, Checkbox
- `feedback/` — StatusChip, ConfidenceMeter, EvidenceCitation
- `data/` — DataTable, SQLPreview
- `navigation/` — RoleSwitcher, Tabs
- `layout/` — Panel

Foundation cards (`guidelines/`): Colors (primary, secondary/tertiary, surfaces, semantic), Type (titles, body, mono), Spacing (scale, radii, heights), Brand (logo/wordmark, iconography).

UI kit (`ui_kits/clinician_ai_kit/`): interactive application — `index.html` plus `AppShell`, `Dashboard`, `Inbox`, `ImageExtraction`, `MultimodalQA`, `DbIntelligence`, `PatientProfile` screens.

## Caveats

- **Fonts load from Google Fonts CDN.** No self-hosted binaries were provided. For offline or production use, supply Inter, JetBrains Mono, and Material Symbols `.woff2` files and replace the `@import` lines in `tokens/fonts.css` with `@font-face` rules.
- **Logo** had a white (non-transparent) background; a transparent version and a cropped mark were generated programmatically. A vector (SVG) logo would be sharper at large sizes if available.
