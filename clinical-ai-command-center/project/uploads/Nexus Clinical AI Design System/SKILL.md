---
name: clinician-ai-kit-design
description: Use this skill to generate well-branded interfaces and assets for Clinician AI KIT, a multi-agent clinical intelligence command center, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

Quick reference:
- Tokens live in `tokens/` and are aggregated by `styles.css` (link this one file). Use CSS custom properties (`--primary`, `--surface-container-lowest`, `--space-md`, `--radius-lg`, `--font-sans`, etc), never hard-coded values.
- Reusable React components are under `components/<group>/`; read each `*.prompt.md` for usage. The visual language is flat, bordered (1px hairlines), dense, and clinical-blue. No shadows for static surfaces, no gradients, no emoji.
- Full interactive application reference: `ui_kits/clinician_ai_kit/index.html`.
- Copy rules: sentence case, no arrow glyphs, no em dashes, spell out numbers in prose, complete and clinically precise wording. See README "CONTENT FUNDAMENTALS".
- Iconography is Material Symbols Outlined (CDN). See README "ICONOGRAPHY".
