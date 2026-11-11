## 6a. Color
[youtube/_batch-visual-design: kfVUlR9BnYQ, pQ0asU6mB1I, vGfTyHPWZLE, u5okJ0VvQwk]
1. **OKLCH for everything.** HSL lightness lies about perceived brightness. Derive every state with relative color syntax rather than hand-picking swatches:
   - Hover: `oklch(from var(--c) calc(l + 0.1) c h)`.
   - Tint: `oklch(from var(--c) 90% calc(c / 2) h)`.
   - Same-hue shadow: `oklch(from var(--c) l c h / .3)`.
   - Gradients: `linear-gradient(in oklch, …)`.
2. **Palettes are formulas.** One shared lightness scale for every hue (e.g. 98.5/95/92/87/80/75/68/59/44/39/25/15%). Chroma peaks mid-scale and tapers at both ends.
   - Chroma budget: 0.05–0.1 muted; 0.1–0.2 for large areas; 0.2–0.3 vibrant; above 0.3 is P3-only and reserved for the one standout moment.
3. **Neutrals carry the brand hue** at chroma of about 0.01–0.06. Dark backgrounds are tinted too, never `#000`.
4. **Status colors share L and C and differ only in hue.** Check them in greyscale: all should read equally loud.
5. **Text on color uses the surface's hue:** lighter on dark fills, darker on bright fills. Badges are a light tint with dark same-hue text.
6. **Three token tiers:**
   - Tier 1 primitives (`--color-blue-500`) are never used in components.
   - Tier 2 semantic roles (`--bg-subtle`, `--fg-muted`, `--border-strong`, `--bg-knockout`) are what components consume.
   - Tier 3 component tokens are rare.

   A theme is a set of tier-2 assignments. **Rebrand test:** one token remap, zero component CSS changes. Mapping [INFERENCE]: Tailwind `@theme` palette = tier 1; shadcn `--primary` / `--muted-foreground` = tier 2.
7. **Dark mode is a tier-2 remap with compensation, not an inversion:**
   - A less saturated seed; secondary text lifted more than tertiary; accent tints more opaque.
   - Lower grade or weight for light-on-dark text.
   - A class for the user toggle, plus `prefers-color-scheme` for the OS setting.
   - Inverted bands in a light page (a dark code block) get their own `knockout` tokens. They aren't a dark theme.
8. **Verify contrast with a tool** on every role pair. Formulas make contrast predictable, not guaranteed. WCAG AA is the floor; APCA Lc targets help when choosing steps.
9. **Lint it:** no raw palette utilities (`bg-zinc-*`, `text-blue-500`) or hex literals in component files.
10. **Check support** for relative color syntax, `text-box`, style queries and anchor positioning before shipping without fallbacks.
