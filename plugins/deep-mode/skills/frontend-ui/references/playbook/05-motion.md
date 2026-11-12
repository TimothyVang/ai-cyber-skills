## 5. Motion
[articles/emil-kowalski-*; .claude/skills/emil-design-eng, animate, review-animations]

**Easing:**

| Motion | Easing |
| --- | --- |
| Enter or exit | ease-out |
| Moving or morphing on screen | ease-in-out |
| Hover | ease |
| Constant motion | linear |
| Draggable, throwable or reversible mid-flight | spring |

- Never use `ease-in` for UI.
- Use the strong curves, never improvised approximations [github/emilkowalski-skills]:
  - Enter and exit: `cubic-bezier(0.23, 1, 0.32, 1)`
  - On-screen moves: `cubic-bezier(0.77, 0, 0.175, 1)`
  - Drawers: `cubic-bezier(0.32, 0.72, 0, 1)`
- **Springs** [youtube/HaZ2jw9rx9M; youtube/gttSJA-kDmQ]:
  - Specify a spring as duration + bounce: Motion `{ type: "spring", visualDuration, bounce }`, or CSS `linear()` baked from the same two numbers. Never raw stiffness / damping / mass.
  - Bounce defaults to 0; about 0.15 is brisk; up to 0.3 for momentum-carrying gestures; never above 0.4. Something opened by a tap gets 0; something dismissed by a swipe may get a little.
  - Fire follow-up work (focus, unmount) at the spring's perceptual duration, not when it settles.

**Duration:**

| Element | Duration |
| --- | --- |
| Micro-interactions | 100–150 ms |
| Tooltips, dropdowns | 150–250 ms |
| Modals, drawers | 200–300 ms |

- Keep UI motion under 300 ms; Rauno caps interactions at about 200 ms.
- Exits run about 20% faster than entrances.
- Choreography: 30–80 ms steps, under about 300 ms in total, never uniform, one entrance per container, never blocking interaction. [.claude/skills/choreograph]
- **Page transitions** may exceed 300 ms if legibility doesn't wait: cap *time to legible*, not total time. Use short distances, and sequence whole-view cross-fades (old out, then new in) rather than overlapping them. Delba's route slide is 400 ms ease-out over 60 px, with old out in 150 ms and new in over 210 ms after a 150 ms delay; readable at about 360 ms. [youtube/UuUAeWpz2NA]

**Details:**
- `scale(0.97)` on `:active`.
- Enter from `scale(0.95)` plus opacity (range 0.9–0.97), never `scale(0)`. Modals stay centered; popovers scale from their trigger.
- Origin-aware popovers: `transform-origin: var(--transform-origin)` in Base UI, the Radix variable in Radix.
- Only the first tooltip in a group gets a delay; later ones open instantly.
- Animate a child element to avoid hover flicker.
- A little blur (under 20 px; 2 px for crossfades) to smooth state changes. Fast-moving content gets a few px of motion blur on entry, or travels a shorter distance. [youtube/gttSJA-kDmQ]
- Don't force one curve on every property: position, scale and radius may finish at different times. [youtube/HaZ2jw9rx9M]
- **Interruptible means velocity-preserving.** A reversed or retargeted animation continues from its current velocity. CSS transitions retarget only position; springs also carry velocity, so use springs for anything the user can reverse mid-flight. Never keyframes for interactive state. [youtube/HaZ2jw9rx9M; github/vercel-labs-web-interface-guidelines]
- **Gestures** [youtube/gttSJA-kDmQ; .claude/skills/gestures]:
  - Track the finger 1:1. Keep the grab offset (never re-center). Keep a velocity history.
  - About 10 px before a drag starts, then lock the axis.
  - Highlight on `pointerdown`; commit on `pointerup`; generous hit slop. Press-to-activate controls cancel when dragged out, but sliders and scrubbers keep the drag alive outside the track. [articles/rauno-invisible-details-interaction-design]
  - Reversible gestures may commit mid-gesture; destructive ones commit only on release. Apply the change from the first pixel and animate only past the threshold.
  - Choose the release target by **momentum projection**: `project(v) = (v/1000)·0.998/(1−0.998)`. Snap to the point nearest `pos + project(v)` and hand `v` to the spring. Distance thresholds alone make flicks snap back.
  - Rubber-band at the edges.
  - Recognize competing gestures in parallel. No double-tap handlers where single taps matter, since they add about 0.5 s to every tap.
  - Hint toward the outcome during the press, and keep enter and exit paths symmetric.
  - Use Vaul rather than a hand-built sheet.

**When to animate**, gated by frequency before choosing any curve [youtube/vjP8bNs8aok; youtube/z3Lo5QT7nME]:

| Frequency | Motion |
| --- | --- |
| 100+ times a day; anything keyboard-initiated, including Escape-to-close and ⌘K | None |
| Tens of times a day | Minimal |
| Occasional (dialogs, toasts) | Standard |
| Rare (onboarding, first success) | Delight is allowed |

Skills still miss this: with every rule installed, an agent animated Escape. Check it by hand.

- Animate in response to a user action (open, expand, confirm), to show what changed.
- Ambient motion only to draw attention: one orchestrated moment, not scattered effects.
- **Spatial consistency:** things enter from and return to where they live (popover ↔ trigger, sheet ↔ edge). [youtube/z3Lo5QT7nME]
- **Match strength to importance:** work tools are fast and predictable; bounce reads playful; overshoot is only for must-notice changes. Rules are defaults with reasons (Sonner deliberately uses 400 ms `ease`). [youtube/z3Lo5QT7nME]
- **State-to-state:** morph one container while content cross-fades with blur; roll digits rather than swapping them; make each step a legible state (button → form → loading → done). [youtube/ofoVCws7gFs]
- **Perceived performance:** spend the animation budget where users wait anyway (uploads, agent runs), and make everything else instant. [youtube/z3Lo5QT7nME]
- **Exits:** Material and NN/g use accelerating exits; for product UI we follow Emil (ease-out exits). Everyone agrees exits are shorter than entrances. [youtube/UcXWY057YuQ]
- Data the user is reading doesn't re-animate on refresh.
- Reduced motion means gentler, not zero: keep opacity and color, drop movement. Drive slide distance through `--slide-distance` and set it to `0` under `prefers-reduced-motion: reduce`. [youtube/UuUAeWpz2NA] **Exception:** spinners and progress indicators keep moving (subtly), because a frozen spinner reads as stalled. [articles/component-gallery/spinner] Decorative shimmer, generative borders and carousel slides are not progress indicators: they stop. Persistent ambient animation gets a pause control. [articles/ai-ux/google-connected-apps-guidelines; articles/ai-ux/atlassian-rovo-ai-guidelines]
- A sent message rises out of the composer (opacity and translateY only). [articles/ai-ux/atlassian-rovo-ai-guidelines]
- Motion origin encodes source: a tool-detail panel grows out of its trace row. Adaptive updates highlight the small part that changed; they never reshuffle the whole view. [articles/rauno; articles/microsoft-hax G14]
- Gate hover effects with `@media (hover: hover) and (pointer: fine)`.

**Performance** [.claude/skills/animation-performance]:
- Animate `transform` and `opacity` only; never `transition: all`.
- Per-frame values go to `ref.current.style`, not React state.
- Don't animate inherited CSS variables.
- Add `will-change` only after you've seen the glitch.
- **Layout changes** (reorder, accordion siblings, an expanding trace row) animate with Motion `layout` / `layoutId` or a View Transition, never `width`/`height`. The problem is visual (text re-wraps, pixels snap), not only performance. Scope `layout` narrowly: projection runs on the main thread and stutters while streamed content renders. [youtube/5-JIu0u42Jc]

**Platform first, the cheapest tool that works** [youtube/UcXWY057YuQ]:
- `@starting-style` + `transition-behavior: allow-discrete` (with `display`, `overlay`) for dialogs and popovers.
- `interpolate-size: allow-keywords` / `::details-content` for accordions. This is the only sanctioned height animation.
- View Transitions for **discrete** changes only: a route change, a filter applied, an item added or removed [youtube/QA5f2loqtM4; youtube/G9xD6lHgrMM; youtube/UuUAeWpz2NA; youtube/GDkFiog1D1c]:
  - **They can't be interrupted.** A second transition skips the first to its end. Anything that can be triggered rapidly or reversed uses springs, Motion `layout` or additive animation instead.
  - **A document-level transition blocks input.** Add `::view-transition { pointer-events: none }`, or use element-scoped `el.startViewTransition()` (feature-detect) for panels inside a live, streaming app.
  - **In React**, trigger only through `startTransition` / `<ViewTransition>`, never `document.startViewTransition` + `flushSync`. Give persistent chrome (header, sidebar, composer) its own named `<ViewTransition>` so it doesn't slide. Express direction with `addTransitionType` (`nav-forward` / `nav-back`).
  - **Named elements keep their aspect ratio** (`width: fit-content`). Otherwise set `object-fit: none; object-position: top left` on `::view-transition-old/new`.
  - **Live content** (a streaming message, an avatar) hides the old snapshot and doesn't animate the new one. Target enter-only and exit-only parts with `:only-child`.
  - **Size-changing groups run on the main thread.** If one janks, rewrite it to translate + scale and confirm in a performance trace.
- **Scrolling** [youtube/vPb7d28RFNE]:
  - Every nested scroller (thread, trace panel, code block) gets `overscroll-behavior: contain`.
  - `scroll-behavior: smooth` and programmatic smooth scrolling only under `prefers-reduced-motion: no-preference`; this covers MessageScroller's auto-follow and jump-to-latest.
  - Scrollbars use `scrollbar-color` with `light-dark()` and are never `thin` on primary scrollers. The thumb takes the accent on `:focus-within`.
  - Scroll shadows and edge fades use scroll-driven animations as progressive enhancement; prefer `scroll-state()` queries to JS scroll listeners.
- **Feedback:** hover and focus *raise* contrast; disabled is 50% opacity with no shadow. Never fade an element the user is about to click.
- **Slow-motion check** to end every motion pass: DevTools → Animations at 10–25%, scrub each transition, and inspect the `::view-transition` tree. A broken transition degrades to a plain fade that passes a full-speed glance.
- Scroll-driven animations only as progressive enhancement.
- A CSS transition before reaching for motion.
