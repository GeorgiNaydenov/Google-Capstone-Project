---
name: Nexus Clinical AI
colors:
  surface: '#faf8ff'
  surface-dim: '#d9d9e5'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3fe'
  surface-container: '#ededf9'
  surface-container-high: '#e7e7f3'
  surface-container-highest: '#e1e2ed'
  on-surface: '#191b23'
  on-surface-variant: '#434655'
  inverse-surface: '#2e3039'
  inverse-on-surface: '#f0f0fb'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#515f74'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3fc'
  on-secondary-container: '#57657a'
  tertiary: '#943700'
  on-tertiary: '#ffffff'
  tertiary-container: '#bc4800'
  on-tertiary-container: '#ffede6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#d5e3fc'
  secondary-fixed-dim: '#b9c7df'
  on-secondary-fixed: '#0d1c2e'
  on-secondary-fixed-variant: '#3a485b'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#7d2d00'
  background: '#faf8ff'
  on-background: '#191b23'
  surface-variant: '#e1e2ed'
typography:
  page-title:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.02em
  section-title:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  panel-title:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 20px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  table-text:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-code:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  row-height-sm: 36px
  row-height-md: 44px
---

## Brand & Style

This design system is engineered for high-stakes clinical environments where data density and cognitive clarity are paramount. The brand personality is authoritative, precise, and evidence-driven, designed to support clinicians and medical researchers in navigating complex AI-synthesized datasets.

The visual style follows a **Modern Corporate** approach with a heavy emphasis on **Structured Information Design**. It prioritizes utility over decoration, utilizing a "Compact-First" philosophy to maximize the visible information on screen. By favoring crisp borders and clear compartmentalization over shadows or gradients, the UI ensures that AI-generated insights and clinical evidence remain the focal point. The emotional response is one of controlled efficiency, reliability, and technical rigor.

## Colors

The palette is rooted in "Clinical Blue" to establish immediate trust and professional alignment with healthcare standards. 

- **Primary & Secondary:** Used for core navigation, primary actions, and structural grounding.
- **Backgrounds:** A distinct separation between the application shell (`#F8FAFC`) and work-panels (`#FFFFFF`) helps define the workspace hierarchy without relying on shadows.
- **Semantic Palette:** Highly critical for this design system. These colors are used for data validation states, risk assessments, and status indicators.
- **AI & Vector Accents:** Blue-Cyan and Purple are reserved specifically for AI-augmented features, vector-search results, and non-deterministic logic previews.

## Typography

The typography system uses **Inter** for its exceptional legibility at small sizes and high-density layouts. 

- **Hierarchy:** Distinct steps are used to differentiate the application layers. Page titles are bold and slightly condensed in tracking.
- **Tables:** A specialized 13px size is defined for data tables to allow for more rows per viewport while maintaining accessibility.
- **Monospacing:** For SQL previews and technical data blocks, a monospaced font is introduced to ensure character alignment and readability of logic.
- **Labeling:** Small caps are used for metadata headers within panels to distinguish "data labels" from "data values."

## Layout & Spacing

This design system utilizes a **Fixed-Fluid Hybrid** layout. Sidebars and utility panels maintain fixed widths (240px - 320px) to ensure consistency, while the primary data work-surface is fluid. 

- **Density:** The 4px base unit drives the system. Whitespace is used strictly to define groups, not for "breathability."
- **Grid:** A 12-column grid is used within panels for content organization.
- **Standardized Heights:** Data table rows and input fields are restricted to 36px (compact) or 44px (default) to ensure vertical predictability across complex forms and lists.

## Elevation & Depth

To maintain a scientific and clinical feel, this design system rejects depth created by shadows. Instead, it utilizes **Tonal Layering** and **Low-Contrast Outlines**:

- **Borders:** All panels and cards are defined by a 1px border (`#E2E8F0`). 
- **Z-Axis:** Depth is communicated by stacking colors. The base is the App Background, panels sit on top in Panel Background, and active/hover states use subtle shifts in background tone (e.g., Gray 50 or Gray 100).
- **Active Focus:** High-priority active states use a 2px Primary Blue border rather than an outer shadow.

## Shapes

The shape language is "Soft-Geometric." 

- **Default (6px):** Used for standard buttons, input fields, and UI cards.
- **Small (4px):** Reserved for interior elements like status chips, checkbox boxes, and tags within tables.
- **Large (8px):** Used for primary container panels and modal windows to provide a clear frame for the internal dense content.

## Components

### RoleSwitcher
A header-level component allowing users to toggle between different clinical views (e.g., Oncologist, Researcher, Data Steward). It uses a segmented control style with the secondary slate color for inactive states and primary blue for the active role.

### AgentConfidenceMeter
A linear gauge used alongside AI insights. It features a thin 4px track with a colored fill (Green/Yellow/Red) based on the percentage of confidence, accompanied by a 12px numerical value.

### StatusChips
Compact indicators with a background opacity of 10% and a solid text/border color. 
- *Verified:* Green.
- *High Risk:* Critical Red.
- *Extracted:* Info Blue.

### EvidenceCitationCards
Small, bordered callouts nested within text or at the bottom of panels. They contain a superscript number, a brief source snippet (13px text), and a "View Source" link in Primary Blue.

### SQLPreviewBlocks
Used for transparency in data fetching. These blocks use a light gray background, JetBrains Mono font, and syntax highlighting using the semantic color palette.

### Data Tables
The core of the system. Tables must feature "sticky" headers, zebra-striping (Gray 50), and 36px row heights. Cell padding is fixed at 12px horizontally.