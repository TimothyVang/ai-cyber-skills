## 3. AI tells to design away from
Each is legitimate only when the brief asks for it. [anthropic frontend-design skill; youtube/zsCGS-Yzjnw; anthropic harness]
- Default shadcn: the same radius, grays and fonts as every generated app. Retheme radius, color and type first, since those three carry most of the personality.
- Purple or indigo gradients over white cards; gradient washes used as decoration. AI glow, gradient borders and generative animation may mark only content that is *actively generating*: never idle controls, and never two indicators at once. [articles/ai-ux/carbon-for-ai; articles/ai-ux/atlassian-rovo-ai-guidelines]
- Unlabeled sparkle icons; a one-time "AI can make mistakes" in a greeting or footer; anthropomorphic progress copy ("I thought about…", "I understand"). [articles/ai-ux/nngroup-ai-ux-research]
- A bordered card plus a colored status pill for every tool call (the old AI Elements look; the upstream rebuild removed it). Tool calls are plain trace lines. [github/ai-ui/vercel-ai-elements]
- **Video tells** (§5a) [github/motion-graphics/_batch-motion-graphics-repos; youtube/747ZnEtsRbg]:
  - A centered title on a gradient.
  - A dark navy void with small floating UI; device mockups; product UI tilted in 3D.
  - Typing into a prompt box as the opener; a logo docked in a corner.
  - Three cards in a row or a KPI grid; a title over a dimmed screenshot.
  - Every element fading and sliding up; the same whoosh on every cut.
  - Glow and particles as decoration; a crossfade between worlds; per-beat camera shake.
  - Landed titles that breathe, float or creep.
- The SaaS card kit: identical rounded cards, one radius regardless of hierarchy, `rgba(0,0,0,.1)` shadow on everything.
- Cream (#F4F1EA) with a serif display and a terracotta (#D97757) accent; near-black with one acid-green or vermilion accent; broadsheet hairlines with zero radius.
- Template chrome:
  - ALL-CAPS tracked eyebrows over every heading
  - `A · B · C` meta strings
  - `WORD — fragment` labels
  - `→` appended to every CTA
  - monospace micro-labels
  - `#0B0B0B` / `#111` standing in for black
- One accented word in a headline (italic, bold or colored).
- `01 / 02 / 03` markers on content that isn't a sequence.
- A big-number hero with a small label, stats and a gradient accent.
- Fade-and-slide-up on every section; a hover transition on every card.
- Many standout effects on one page. Allow **one standout moment per page.**
- "Generic AI SaaS": radial glow lights, glass cards, icon tiles, bento grids. [github/MengTo-skills]
- The 2026 tells: Inter as the only typeface, a serif headline with one italic word, a blinking cursor, a background grid, a cursor-following glow. [youtube/r2P1v64pM28] Also "Claude Beige / Algorithmic Uniqlo" (beige + serif + italic accents), decorative section numbers, and the hero formula "Build faster with intelligent workflows… Powered by AI" plus "Trusted by 10,000+". [youtube/v42opQpCy60]
- Fake proof or placeholder-looking data: invented metrics, logos, testimonials, "Acme" or "Sarah Chan", `99.99%`. Use real product truth or honest placeholders. [github/MengTo-skills]
- Color tells [youtube/7Z9rrryIOC4; youtube/EjEYTRD-W-M; youtube/kfVUlR9BnYQ]:
  - Grey or opacity-dimmed text on a colored fill.
  - White text on yellow or green.
  - Saturated solid status badges.
  - Status colors of unequal loudness: green glows, red sinks.
  - Untinted library greys.
- A border around every row and card, plus a label on every value ("Status:", "Price:").
- A rainbow of buttons (green Save, red Delete, blue Cancel side by side), or more than one solid primary per view.
- Icons from mixed sets, or icons as heavy as their label.

**Removal test** for any suspect element [.claude/skills/no-ai-design-slop]:
1. Name it precisely.
2. State the job it does.
3. Delete it mentally. If meaning, state, action and hierarchy survive and clarity improves, delete it for real.
4. Never compensate with a new effect.
