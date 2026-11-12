# Reference Rebuild

Use when: rebuilding or redesigning a product UI to the standard of an app the user names ("make it like herdr / Grok Bot / Linear"). You own the design canvas, the build, and the proof.
Method adapted from Nick Vasilescu's Grok Bot rebuild (T3 Code + Paper MCP, youtu.be/vNpJz-K644k): use the reference, design first, then build from the design.

## Steps

1. **Study the reference by using it.** Launch the real app (installed build, or an unpacked Electron build with `--remote-debugging-port`) and drive it with computer use or CDP: every main screen, empty states, approvals, settings.
   Save screenshots and a measured system sheet from computed styles (type scale, colour tokens, radii, spacing, row heights, icon library, motion).
   Marketing pages and model-generated mockups are not a reference. Read-only: navigation only, nothing sent, created or approved.
   Done when every main screen has a saved screenshot and the system sheet lists a measured value for each item above.
2. **Map the product's real data** before drawing: list every field the backend actually emits for each screen (`/state.json`, API responses). The canvas may only show fields on that list; invented values are labelled sample data.
   Done when each screen has a field list taken from a real backend response.
3. **Design first on a canvas.** One frame per screen and key state, product fidelity, real labels and real data shapes. Tool order: Paper MCP, then Figma MCP, then a static self-contained HTML canvas page of frames. The canvas carries the design system as tokens, not adjectives.
   Done when every screen and key state has a frame and the canvas defines its tokens.
4. **Review the canvas before code.** Run the restraint check below on every frame, then pick the direction yourself, log why (SKILL.md Autonomy), and show the user the canvas in the report. Code starts from the chosen canvas.
   Done when every frame passes the restraint check and the chosen direction is logged with its reason.
5. **Build from the canvas**, one screen per owner, shared tokens and primitives first (`references/playbooks/visual-parity.md` for the harness and per-component loop). Done when every canvas screen renders in the running app.
6. **Prove it in the real app**, not a mock: screenshot each built screen in the running app at the canvas size and compare it frame by frame with the canvas; fix and reshoot until each matches.
   Add real-data and worst-case passes (long names, empty, every state, outages, narrow widths).
   Done when every screen has a matching canvas-vs-app screenshot pair and every worst-case pass has a result.

Run steps 1 to 3 as parallel threads when they are independent (reference study, backend mapping, canvas), and settle each thread when its output is saved.

## Restraint check (what made earlier rebuilds look AI-made)

Ship only when every frame passes:
- One real icon library at one size and stroke (Lucide or the host SDK's set); no hand-drawn icons, no Unicode glyphs as icons.
- Neutral palette with one accent; colour only where it means state; status as a small dot plus text, pills only for the single needs-attention element.
- Sentence-case headings; no uppercase tracking labels, no eyebrow labels above headings.
- One container per section, hairline dividers between rows, nothing boxed inside a box, no glows.
- Monochrome mark; no rainbow per-role colours.
- One sans, three weights, mono only for IDs, queries and code; tabular numbers.

## Gates

- No canvas, no build. Code builds only from the chosen canvas.
- A field on the canvas that the backend does not emit is either removed or added to the backend as separate, named work.
- Take layout, density, type and interaction patterns from the reference; never its code, logos, icons, images or brand name.
- Claims of parity cite a running-app screenshot next to its canvas frame.

## Evidence

- Reference screenshots and system sheet; the data-field map; canvas location and the direction you chose, with why.
- Per-screen canvas-vs-app screenshot pairs; worst-case pass results; what still differs and why.
