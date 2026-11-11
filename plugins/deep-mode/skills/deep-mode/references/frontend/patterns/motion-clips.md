# What the motion clips show

Every clip cut from the reference talks, described as motion (easing feel, duration, stagger, transitions, beat sync). Use these as vocabulary for prompts and reviews. Clips: `TimothyVang/frontend:reference/youtube/<id>/clips/`.

## Inside Framer Motion's Layout Animations

Source: https://www.youtube.com/watch?v=5-JIu0u42Jc

- An App-Store-style card growing into a full-screen view and back.
- A shuffled layout list, then an accordion whose siblings glide as content changes.
- The scale-distortion problem: a resizing box with a fixed-size child dot.
- An app icon expanding into a full app view with a shared box and cross-fade.

## How to Make Insane Motion Graphics With Opus 5.5

Source: https://www.youtube.com/watch?v=747ZnEtsRbg

- Showreel built under the studio rules. A serif "move." whose "o" swells into an orange disc, then a "timing" card where four dots slide on snappy, default, heavy and playful easing (playful overshoots). A dot grid then flips into orange diamonds in a wave from the centre, a "form" blob, and a Claude end card. Hard cuts land on 2- and 4-beat blocks of a 128 BPM grid.
- The MagicPath "one path" reel: a single cursor stroke threads the film. Chapter cards (mono label plus bold display line) run Describe it., Generate., Refine. (radius slider dragged live), Explore. (3×3 variant grid), Together. (motion-blurred whip-pan into a multiplayer board) and Design is code. (a card beside its `<Button radius="md" tone="ink">` source). Each card holds about 1.5–2 s; transitions are directional pushes with heavy motion blur.
- The brand-prompt launch (20 s, 60 fps). Huge black kinetic words "One" and "Slow." hit on the beat (hook: "One developer. One chat. Slow."), then the frame cuts to a warm-white canvas: "The shared workspace for humans and agents" with the real UI sliding in. A prompt card, then two phone frames drawn by labelled agent cursors, then "Plug in your agent", "Pushed to your repo as real React" and a full-bleed green "5". Roughly one beat per idea, with the accent word set in brand green.
- Full-screen voiceover cut. "The shared workspace for humans and agents." writes on word by word: each word rises in slightly blurred and settles, with "agents" in green. Then "One prompt." with a typed prompt card, and "A whole team of designer agents" as phone frames build. "Plug in" stacks the Claude Code, Codex and Cursor logos one per beat; "Design becomes code" splits phone and code; a giant green "5" lands as agent cards fan in; "at once." The end card is "Path 2.0" with a "Try it at magicpath.ai" pill wiping in. Words are timed to a Fish Audio voiceover (audio stripped here).
- The reference film whose grammar was borrowed: javi's mtioon launch (@javiiarchive). "Say it." on a pastel gradient becomes "Say it. Watch it moove." as bright pill chips fly diagonally. "Your repo is the brief." shows an orange folder mascot with eyes swallowing a diagonal stream of file chips (README.md, logo.svg…). The camera then pulls back into an editor UI. Playful spring overshoot, saturated chips and bottom captions.
- Style transfer: MagicPath in mtioon's grammar (15 s, 60 fps). The logo tile has Claude Code and Codex pills orbiting it. "The visual layer for all your agent work." sweeps in with heavy motion blur, then "Every agent. One canvas." as agent pills ride a long 3D-tilted bar. An "Overview 122,872,886" counter rolls its last digits, phone screens tilt in perspective, and "Humans." and "Agents." chips pop. A full-bleed green "Prototypes." card closes. Same chips and oblique slides as the reference, in MagicPath's green palette.
- The "one container never cuts" loop (16 s, 8 bars at 120 BPM, seamless). A pill input types "Design an onboarding flow, 5 screens", grows into the canvas, and five phone screens build together on successive half-beats while agent cursors drift. The cursor shift-selects every "Sign up" button (selection rings on 8ths), and all five refill ink to accent in one spring. Everything collapses into a dark terminal pill ("update the pricing", then a "Pricing screen updated" toast), "View code" opens React, and a share link copies before the loop restarts.
- Onur Ozcan's beat-synced Steve Jobs story (shown as the sync benchmark). A black cold open with one title card per beat ("Adopted at birth." / "Dropped out of college." / "Fired from his own company." / "Then he changed everything.") over a tiny character, then the Apple II and iPhone. "CONNECTING THE DOTS / STEVE JOBS" leads to rolling year counters (1955 over a Golden Gate sunset, a white-out to 1971 meeting Wozniak, then 1972 "Stays for calligraphy"). Every cut and text pop sits on a beat.
- The MagicPath film re-scored to a synthesized 120 BPM track. The prompt types char by char, and "One request, / a whole team at work." has its second line slide up with motion blur. Then a green full-bleed "Every screen, all at once.", black "Bring the agent you already trust." over a Claude Code terminal, "Design becomes code, code becomes design.", "Not a static file, a real prototype", a tilted 3D wall of UI cards, and the logo end card. Per the score prompt, cursor presses click, container morphs whoosh and the logo thumps, all on measured beats.
- Final 45 s "Design Team" film from the director's-brief template: one continuous camera, no hard cuts. "One prompt." types; five empty screens wait while agent cursors fly in ("Five screens. At once.") beside a thread panel listing five named agents; the screens fill (card, pricing, sign-up) under "You just hired five designers." The camera glides across the canvas to "Bring your agents.", a Claude Code terminal ("Build a web version of the sign-up flow on the MagicPath canvas"), cursors building on the canvas, "They build right here." and "View code."

## Refactoring UI: Practical Solutions to Common UI Design Problems (Steve Schoger, CSS Day 2019)

Source: https://www.youtube.com/watch?v=7Z9rrryIOC4

- Nav moved out of its bar and the subtitle recoloured on the dark hero, at 5×.
- Search form boxed in a white panel with taller inputs, muted icons and a yellow button, at 6×.
- The panel overlapping the hero, a shadow scale and a table cleanup, at 7×.
- Deal cards, cool/warm greys and the final original-vs-redesign comparison, at 5×.

## Smart Layouts: Ahmad Shadeed (CSS Day 2025)

Source: https://www.youtube.com/watch?v=_njUxg5UfR0

- A news grid re-flowing via :has() as articles and quotes are added and removed.
- A card widening as its thumbnail and title scale with cqw units.
- A GitHub-like app header hiding labels and collapsing search via container queries.
- The "Keep Calm" hero resized from ~1500 px to ~400 px as anchored elements re-flow.

## 10 GitHub Repos to 10x Your AI Motion Graphics

Source: https://www.youtube.com/watch?v=aD9X6Lc3dVk

- Lemo Opuscar, isometric explainer. On a beige isometric board a phone pings, an orange packet travels to a "CELL TOWER", and a blue line draws along "FIBRE-OPTIC CABLE ~200,000 km/s". A grey block's walls fade to reveal "SERVER builds the reply" racks in a "DATA CENTRE", and the packet returns to light the phone's screen teal. The camera pans slowly along the path and pushes in on each node; labels draw on with leader lines; a caption pill reads "Light covers 1,000 km of fibre in about 5 ms". Loops about every 8 s.
- Lemo Opuscar, three more of its 66 film styles. Paper cut ("The Keeper's Light"): layered hills, sea and clouds drift in parallax while the lighthouse beam sweeps, a red sailboat bobs, and a title tag slides in before a fade to dark. Ink wash: mountains bleed out of the fog while brush strokes paint a peak, a gnarled branch, a boat and birds. Retro terminal: a CRT power-on line opens into an ASCII-dot landscape and Saturn, and "DEEP SIGNAL_" types on with a blinking cursor.
- Three.js. "Revenue by year" as 3D stacks of banknotes: each year's stack builds from the floor in sequence ($1.2M → $4.4M) with value labels, the camera dollies, and it rebuilds on a roughly 6 s loop. Then a Claude-modelled smartwatch (orange band, face "10 08") turns 180° and back on a reflective black floor. Then a particle spiral galaxy rotates, tilts edge-on, and its particles converge into extruded "3D" text before dispersing.
- Blender MCP. Building-shaped population towers on a misty sunset sea, with a slow dolly and shallow depth of field ("United States 341 million", "China 1.41 billion", "India 1.44 billion"). Then "How a solar cell makes electricity": the panel's layers lift apart into an exploded stack with glowing edges, photons knock glowing electrons free, and a wire lights a bulb ("Freed electrons flow as current"; "Sunlight in. Electricity out."). Then headphones rotate and explode along one axis into labelled parts before reassembling.
- Prompt packs. A WebGL2 glass-and-gold mosaic where a fish made of tiles swims: tiles lift, flip, fly and click back into place, and a gold shimmer wave sweeps the wall. A flat "Three-cell circulation" explainer draws the Hadley, Ferrel and Polar cells one by one as dashed looping arrows with captions. Then opus-video-prompts "#15 UI morph loop" ("120 BPM", "one shape · no cuts"): one shape morphs from a "Get started" pill to an orange check circle, a "Night Drive" player pill (play → pause), an orange toggle, and a "Deploy to production" search field, then back to the button on a roughly 6 s cycle.
- Claude Animation Base. A boxy orange mascot on hand-drawn hills cycles through built-in emotions (heart eyes with floating hearts, sad under a rain cloud, neutral, a big grin with a sparkle and bubbles), with quick dips to dark between beats. In explainer mode it bounces beside an "Earth's surface" donut that fills clockwise while the count ticks 7% → 60% → 71% water, with "29% land" and "97% of Earth's water is salty" labels popping in.
- React Three Rapier, real rigid-body physics. A funnel pours coloured balls, and a steel ball smashes a Jenga tower whose blocks topple and scatter. A domino chain falls in sequence to spell "PHYSICS" while the camera tracks along it. A Galton board then drops hundreds of balls through pins into bins until they settle into a bell curve, and a "Binomial distribution" label fades in once the pile settles.
- React Postprocessing. A warp tunnel of neon rings with bloom and chromatic-aberration fringing pulses toward the camera. Then a glowing moon over a dotted wave terrain, and a sodium atom whose electrons orbit with glow while shell 3's gold ring and its "Valence electron" are highlighted and the "2 · 8 · 1" count lights shell by shell. The grid view's code overlay reads `<EffectComposer> <Bloom/> <DepthOfField/> <Noise/> <ChromaticAberration/>`.
- librosa (`beat_track` + `onset_detect`) at 123.0 BPM: every beat hard-cuts to a new full-frame card. A counter steps through numbers (03, 05, 07, 09, 11…) while backgrounds alternate white, yellow, black, blue and red, and motifs alternate between a dot ring and concentric ripple targets. Then "ON THE BEAT" banners in diagonal hazard stripes and beat-meter bar charts. A bottom HUD shows the onset-strength waveform, 13 beat markers, 29 onset dots and a playhead that crosses a marker at each cut.
- Video ShotCraft, a promo for a voice app called "murmur". Three nodes (Speak → Summarize → Share): an arc draws from the active node to the next, which lights teal as the camera pushes into it. A logo reveal follows ("murmur", then "SAY IT ONCE. IT'S WRITTEN."). Then a 3D coverflow of shot recipes rotates past with heavy motion blur: an "IMPACT" title card, a "+247%" stat, stacked app windows, a flock of tumbling cards, a word cloud (Grid, Camera, Loop, Keyframe, Stagger, Spring, Pivot…) and staggered gradient bars. A highlight steps along a filmstrip of recipes at the bottom.

## The Little Details of UI Design (Steve Schoger, Laracon Online)

Source: https://www.youtube.com/watch?v=EjEYTRD-W-M

- Header redesign at 6×: brand-tinted grey, restyled search input and icons, circle avatar.
- Stats panel redesign at 8×: hierarchy, text greys, brand-colour background and a lighter shadow.
- News feed post cleanup at 5×: darker links, lighter icons, merged actions and no borders.
- Sidebars at 6×: borders replaced by spacing and links grouped under small uppercase labels.

## UX Design Principles for Semi Autonomous Multi Agent Systems

Source: https://www.youtube.com/watch?v=fmZWvE7yDZo

- An Execution Plan card followed by streamed step events, with a Stop button beside the composer.
- The verifier result at 98% confidence and the rendered spheres in Blender.
- A plan card's metadata chips: time, tokens and status.

## View Transitions and Activity (React Conf 2025)

Source: https://www.youtube.com/watch?v=G9xD6lHgrMM

- A sidebar in Activity keeps its search, results and scroll position when hidden and reopened.
- A hidden Activity preloads the video so playback starts without a spinner.
- enterTheaterMode in startTransition animating the player to theatre size via ViewTransition.
- Metadata wrapped in ViewTransition and slowed in the DevTools Animations panel.

## View transition debugging

Source: https://www.youtube.com/watch?v=GDkFiog1D1c

- Text blowing up mid-transition, then paused and scrubbed in DevTools Animations.
- Fixing it with object-fit: none and object-position: top left on the snapshots.
- The simpler fix: width: fit-content on the named element.

## Designing Fluid Interfaces (WWDC18 session 803)

Source: https://www.youtube.com/watch?v=gttSJA-kDmQ

- Overscroll rubber-banding versus content hitting a hard wall.
- Strobing from too much change between frames, then normal vs motion blur vs motion stretch.
- The two-slider spring model (damping and response) redrawing its value/time curve.
- FaceTime PiP snapping to the nearest corner versus the projected momentum position.

## WWDC23: Animate with springs

Source: https://www.youtube.com/watch?v=HaZ2jw9rx9M

- A thrown knob: ease-in-out jerks to a halt while a spring carries the finger's velocity.
- iOS app launch slowed down, showing several springs with different start and end times.
- Bouncy, smooth and flattened spring families as position-over-time curves.
- The same toggle with bounce 0, 0.15, 0.3 and 0.6.

## Emil Kowalski Skills: This is CRAZY GOOD SKILL (you need to have it)!

Source: https://www.youtube.com/watch?v=huWl2J4A6FE

- The /animate output: an Account dropdown with its "ingredients" card.
- The /prototype output: a Notion-like page with Quiet, Stacked and Countdown toast variants.

## Programmable colors: bridging design and code (Config 2025)

Source: https://www.youtube.com/watch?v=kfVUlR9BnYQ

- The L, C and H slides, each changing one channel of oklch(0.6 0.15 40).
- OKLCH vs HEX hue-rotate contrast, then a hue slider re-theming a settings page in light and dark mode.
- Brand, success and error colours derived by dragging only the hue in the OkColor Figma plugin.
- The oklch.com picker, the DevTool project starter and the Harmonizer palette grid.

## Agent Output Is Not UX: Rendering Layer Your LLM Pipeline Is Missing

Source: https://www.youtube.com/watch?v=maTp79FD9gI

- A long Claude text answer for a reservation versus the same intent as a booking card.
- Flight cards streaming from skeleton to partial to complete.

## Config 2025: Typography is the foundation of any design system (Elliot Jay Stocks)

Source: https://www.youtube.com/watch?v=n0iAYEpU0Fk

- The GRAD slider on "meticulous", book cards light vs dark, then an ink-spread comparison.
- Roboto Flex's grade slider adjusting light text in a dark box, then a multiplexed face across weights.
- Optical-size slides: an "a" across sizes, "karate" display vs text, "optics" 20 pt vs 100 pt.
- The "Beach hut, Tofino" card showing how half-leading inflates the 20 px gaps.

## Armchair Safari e13: Emil's slick animations

Source: https://www.youtube.com/watch?v=ofoVCws7gFs

- A Dynamic Island pill morphing between Ring, Timer and Silent.
- Silent to Timer, with digits rolling from 0:00 to 0:01.
- Selected photo cards stacking and dropping into a trash can.
- A Feedback button morphing into a textarea card, then a spinner and "Feedback received!".

## Rethinking Color: A designer-developer's guide to modern color systems (Refill 2025)

Source: https://www.youtube.com/watch?v=pQ0asU6mB1I

- Dragging L/C/H on oklch.com and seeing chroma limits per gamut.
- Swapping one base hue recolours the whole demo page, then inverted and dark versions.
- Three cards from one colour via oklch(from …), overriding lightness and chroma with sliders.
- Alerts each generated from one picked colour, in light and dark mode.

## Cranking View Transitions up to 11 (CSS Day 2026)

Source: https://www.youtube.com/watch?v=QA5f2loqtM4

- A 3D exploded view of the view-transition groups moving during overview ↔ detail.
- A video keeps playing mid-transition, with the CSS that hides the stale old snapshot.
- A grid-gap toggle in startViewTransition and an Isotope-style periodic-table filter with linear() wobble.
- Re-triggering mid-flight skips and restarts, versus the smooth additive retarget.

## Impeccable: The BEST Frontend Design Skill For CLAUDE & CODEX

Source: https://www.youtube.com/watch?v=r2P1v64pM28

- Scrolling Impeccable's "Slop" catalog with 2022 vs 2026 specimens and the detector overlay.
- Impeccable's "Choose the visual world" picker with three concept cards and reroll.

## Design Token Architecture: Brad and Ian Frost (CSS Day 2025)

Source: https://www.youtube.com/watch?v=u5okJ0VvQwk

- An animated token diagram where remapping Brand Background turns every touchpoint from green to purple.
- Dark mode as a subtheme across Figma variable modes, CSS and React Native.

## Web animations today and tomorrow (Google I/O 2025)

Source: https://www.youtube.com/watch?v=UcXWY057YuQ

- A bio dialog with tuned entry/exit and backdrop on a team-avatar page.
- Icon buttons widening to max-content to reveal labels on hover and focus.
- A horizontal details accordion, then scroll-driven image reveals and a header shrinking on scroll.
- Cards reflowing smoothly via view-transition-name: match-element.

## Designing Page Transitions (React Conf 2025)

Source: https://www.youtube.com/watch?v=UuUAeWpz2NA

- The default ViewTransition cross-fade between product pages, then replayed slowed.
- Directional slides: Previous slides content right, Next slides left.
- Named header, footer and product elements stay put while the page slides.
- The page slide with a 3px blur applied.

## Build smarter color systems with relative colors (Kevin Powell)

Source: https://www.youtube.com/watch?v=vGfTyHPWZLE

- A toast background derived with hsl(from …), its lightness raised to a pale tint.
- data-toast variants swapping one colour to recolour text, background, border and shadow.
- OKLCH vs HSL swatch cards on one hue slider; the HSL card's text loses contrast at some hues.
- The OKLCH toasts rendered above the HSL toasts for comparison.

## Make Apps Feel Expensive: Emil Kowalski's AI Design Skills

Source: https://www.youtube.com/watch?v=vjP8bNs8aok

- Ease-in vs Emil's curve on a menu exit, frozen at 40 ms: 11% vs 80% gone.
- Menus at 400 ms vs 180 ms, then scale(0) vs 0.95 entry.
- A faster spinner that feels shorter, then a Save button pressing to scale 0.97.
- The real agent re-run with skills installed, which still animated Escape.

## Level Up your Scroll UX (CSS Day 2025)

Source: https://www.youtube.com/watch?v=vPb7d28RFNE

- A horizontal card scroller with end-aware buttons, a focus-tinted scrollbar and edge fades.
- overscroll-behavior-x: contain stopping back-navigation and scroll chaining.
- A rebuilt Nintendo Switch home row with snap, a pulsing outline on the snapped game and elastic overscroll.
- Game tiles flying in, staggered, on load via @starting-style.

## Understanding is the new bottleneck

Source: https://www.youtube.com/watch?v=WkBPX-oDMnA

- The explain-diff doc scrolling from Background to an interactive figure to a literate code diff.
- A quiz in the doc showing a red ✕ and a "Not quite." explanation on a wrong answer.
- A micro-world control panel for porting a website, with stage stepper, terminal and old/new sites side by side.
- A multiplayer agent thread in Notion, then a plan doc with Path A/B options and teammate comments.

## Turn Claude Code into Your Own INCREDIBLE UI Designer (using Playwright MCP Subagents)

Source: https://www.youtube.com/watch?v=xOO8Wt_i72s

- The design-review subagent drives a headed browser and resizes the site to 375 px.
- The finished design-review report: grade, strengths and prioritized issues.

## The Ridiculous Engineering Of Animations

Source: https://www.youtube.com/watch?v=z3Lo5QT7nME

- An app zooms out of its icon and back, then a recut that slides apps in from the side.
- A right-click menu that appears with no motion, and tooltips that show instantly after the first.
- Four easings over the same distance and duration, then their velocity graphs.
- Emil's ease-in vs ease-out dropdowns at the same duration, then spinner speed.

## UI Libraries for Claude Code (Ban the AI Look)

Source: https://www.youtube.com/watch?v=zsCGS-Yzjnw

- Dark tile grid of toggle, toast, search and dropdown primitives animating.
- shadcn default, then a "Create project" dialog restyled through radius, color and serif type variants.
- Sonner toast stacking, Vaul drawer drag, cmdk filtering and NumberFlow digit roll.
- Hand-built toast, drawer and command menu failing.
- The pick-ui-library skill page.
- Beautiful UI agent states: pricing card, loader, task list, approval prompt and chat.
- Beautiful UI, RareUI, Magic UI, Aceternity and 21st.dev landing pages and component grids.
- "One standout per page": a single orb vs a grid of glowing effects.
- A prompt naming the libraries, the shadcn CLI install and the pick-ui-library card.
