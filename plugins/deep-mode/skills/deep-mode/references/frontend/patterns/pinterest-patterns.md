# Patterns from popular Pinterest UI pins

What 341 top pins across 14 searches (2026-11-11) teach, as text. Mostly Dribbble/Behance concept shots: take a pattern only if it passes `references/frontend/playbook/03-ai-tells.md`. Images and clips: `TimothyVang/frontend:reference/screens/pinterest/`.

## ui-ux-design

- Bold flat colour fields (lime, yellow, lilac) with black 1.5–2 px outlines and hard offset shadows: neo-brutalist cards with real hierarchy, not glow (§6a, §3 counter-example).
- Big numerals as the hero of a screen (timers 00:14:98 and 17:41, balances $12,304) set in a tight grotesk: the type scale does the work (§6).
- Folder-shaped collection tiles (Unsorted / Must watch) with an icon tab: a component with a recognisable silhouette instead of a generic card (§4).
- §3 tells to avoid: frosted 'liquid glass' login panels over 3D renders, iridescent blobs and purple-to-blue NFT gradients appear in several pins. They're decoration, not product.

## button-design

- Every state shown side by side: primary, secondary, icon, toggle, select, disabled ('Liquid glass UI kit'). Spec all states, not just the default (§4, §5 Feedback).
- Pill buttons with a trailing icon (paper-plane 'Get started') in a solid or outline pair: a clear primary/secondary hierarchy (§4).
- Tactile / skeuomorphic controls (knobs, chunky 3D toggles, cartoon game buttons) belong to playful or hardware briefs only (§6a).
- §3 tells: neon gradient borders and glow on idle CTAs ('Generate Site', 'Create', glowing 'Get Started' variants). Per §3, glow marks only content that's actively generating.

## ui-animation

- A notched tab bar whose active bubble travels between icons recurs in at least three pins; an on-screen move, so use ease-in-out (§5).
- Product card → detail as one shared element (jacket pin): build it with Motion layoutId / View Transitions (§5).
- Two pills merging into a card (Dynamic Island style): state-to-state morph of one container (§5).
- Much of this set is promo-reel editing (hard cuts between phone screens), not interface motion; don't copy reel pacing into product UI.

## micro-interactions

- Submit → dots → Success ✓ → reset, and Refresh pill → spinner circle → pill: the textbook §5 state-to-state sequence.
- Search icon that expands into a field, then a result dropdown, collapsing back to its origin: origin-aware motion (§5 spatial consistency).
- Heart like: outline → fill with a scale pop. Keep it ≤150 ms (§5 micro-interactions).
- Avatar grid collapsing into a stacked pill with a stagger: a §5 choreography reference.

## dashboard

- Bento-grid dashboards with 3–4 KPI tiles in a row over one large chart; numbers are the biggest type on the page (§6).
- A 'Good morning, <name>' greeting header + search + avatar is the near-universal top bar; fine, but it's the generic default (§3).
- Light dashboards with one saturated accent (orange bars, green highlight) read more product-like than the dark neon ones (§6a: one accent).
- §3 tells: purple-glass dashboards with 3D blobs, gradient washes behind charts, and neon line charts on near-black.

## mobile-app

- Category-specific accent colours drive whole flows (sage green plant shop, burger orange, sneaker colour per product) rather than a default palette (§6a).
- Large photography with UI chips overlaid (hiking stats '84 / 78 / 42' on a mountain photo): content first, chrome minimal (§6).
- Mascot-led onboarding (Worly, habit blobs) fits rare flows only (§5 When to animate: rare = delight allowed).
- Most pins are hand-held or floating device mockups; judge the screen, not the render.

## ai-chat

- The dominant pattern is an empty-state hero: greeting ('How can I help you today?') + one composer + 3–4 suggestion chips (§4a).
- Sidebars with New chat / Search chat / GPTs follow the ChatGPT layout; useful as a baseline for the shadcn chatbot template (§4a).
- Voice mode as a large orb with waveform controls under it (mic, stop).
- §3 tells, heavily present: glowing iridescent orbs on idle screens, purple-pink gradient backdrops, and glass cards. Per §3 the orb should animate only while the model is responding.

## design-system

- One-page style guides ('CALM / KIT', 'SOFT / SYSTEM', 'Product UI Styleguide'): colour palette, type specimen 'Aa', buttons, inputs, toggles, progress and nav on one board. A token plan before code (§1).
- Warm off-white + muted sage/olive palettes with a single dark green primary are a fresh, non-shadcn default (§6a).
- Neo-brutalist design-system boards (hard black borders, yellow/green blocks) show a complete alternate personality (§3 'retheme radius, colour, type').
- Watch for kits that show states (focus ring, hover, disabled) vs. ones that don't; only the former are useful component specs (§4, §8).

## icons-assets

- Consistent stroke-weight line icon sets (onyx icons, 24 px grids) on dark and light: one icon family per product (§4: use Lucide/Phosphor rather than mixing).
- Many results are game UI assets (potions, coins, cartoon buttons); out of scope for product UI but useful for gamified moments.
- Filled glyph sets (white on black, black on yellow) work for dense toolbars where outline icons are too light.
- None of these should be used as assets: copyrighted; use an OSS icon library.

## ui-motion-design

- Containers that morph (timer widget → list → card; grey card → fanned photo stack) are the reusable product motion here (§5 State-to-state).
- Hero headline cross-fades over changing photography, one word set at a time (§5: sequence whole-view crossfades).
- Most entries are marketing-site and Jitter/Figma showcase motion; long, decorative, and not product interaction speed.
- §3 tell: wobbling glass orbs and purple glass assistant cards.

## app-animation-interaction

- Numbers roll digit-by-digit in counters (vacancies 8 → 6): §5 'roll digits rather than swapping them'.
- List → detail shared-element zooms (clothing, product with heart) keep spatial continuity (§5).
- Slider-driven characters that change colour and expression as you drag apply the change from the first pixel (§5 Gestures).
- Long-press with a filling arc ripple hints toward the outcome during the press (§5 Gestures).

## button-hover-animation

- Best reusable hovers: fill slide, lift, arrow nudge, offset shadow slide. All transform/opacity-only (§5 Performance) and ≤200 ms ease (§5 Hover).
- Arrow-dot → pill expansion ('Learn more') is popular but is usually built by animating width; use clip-path/scale instead (§5).
- Click → full 'loading..' state → back is the right idea (state-to-state) but should stay inside the button's own box.
- §3 tells: neon glow pulses, travelling gradient borders and shine sweeps on idle buttons (about a third of this set).

## loading-animation

- Determinate progress with a clear end state ('Preparing' → 'All set'; download arrow → check 'Complete') beats endless spinners (§5 State-to-state).
- Simple loaders (3 dots fading or bouncing, an arc spinner) are linear constant motion and keep moving under reduced motion (§5).
- Mascot loaders (duck, cat, flask, walking character) are delight for rare waits only (§5 When to animate).
- Preloaders that cover a whole site with a 2–4 s intro (Suit, BUILD, stripe wipes) violate §5's time-to-legible cap.

## micro-interaction-app

- Send → plane flies → ✓ Sent!; clap → +1 bubble and counter roll: complete feedback loops on single buttons (§5).
- Checkbox, radio and toggle with animated checked states: a reference for 100–150 ms control motion (§5).
- Avatar + '+' pill that unfolds into a toolbar and folds back: an origin-aware popover (§5).
- Notification card expanding into a widget: a morph that keeps identity (§5 State-to-state).
