## 4. Components: compose, don't hand-roll
Order of preference [youtube/zsCGS-Yzjnw; .claude/skills/pick-ui-library]:
1. **A library already in `package.json`.** Don't churn dependencies unasked.
2. **Foundations, restyled:** shadcn/ui (code copied into the repo) on Base UI or Radix primitives, for dialogs, popovers, menus, selects, tabs and tooltips.
3. **Specialists** for components that are hard to get right:

| Need | Library | What a hand-rolled version gets wrong |
| --- | --- | --- |
| Toasts | Sonner. Error and actionable toasts persist until dismissed and never take focus; others stay at least 5 s, scaled by length, and pause on hover or focus. At most 3–4 visible, and any toast action also exists elsewhere [articles/wai-aria-apg/alert; articles/component-gallery/toast] | Pile up or vanish; no stacking or hover-expand |
| Drawers / bottom sheets | Vaul | No drag; no flick to close |
| ⌘K command menu | cmdk | Breaks with the keyboard |
| Animated numbers | NumberFlow | Digits jump instead of rolling |
| OTP inputs | input-otp | — |
| Long lists (1k+ rows) | Virtuoso | — |
| Drag and drop | dnd kit | — |
| Charts | recharts (Liveline for live streams) | — |
| Animation (springs, layout, exit) | motion | — |
| Shared state / class names / variants / theme | zustand / clsx / cva / next-themes | — |

4. **Design components** (Magic UI, Aceternity, RareUI, 21st.dev) only for the single standout moment. Install through the CLI or registry so the code lives in the repo and can be edited.
5. **AI-product states** come from shadcn's chat components; see §4a. Beautiful UI is the visual reference.
