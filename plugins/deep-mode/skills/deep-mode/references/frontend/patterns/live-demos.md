# Live library demos (what specialists do that hand-rolled versions don't)

Recordings: `TimothyVang/frontend:reference/demos/`.

These were recorded on 2026-11-11 from each library's official demo page in a headless browser (1280×800, 30 fps). They're the reference for "what the specialist does that a hand-rolled version doesn't" (PLAYBOOK §4). Click a preview for the MP4.

## Sonner: toasts
Sonner: four toasts collapse into a stack, expand on hover, then success, error, and a promise toast going from loading to success

- **Stacking:** new toasts push older ones back into a collapsed, scaled stack instead of piling up.
- **Hover to expand:** the stack fans out with even gaps; the auto-dismiss timers pause while it's open.
- **Typed toasts and promise:** a promise toast swaps from "Loading…" to its result in place, without a second toast.

Source: https://sonner.emilkowal.ski

## Vaul: drawer
Vaul: drawer opens with a dimmed backdrop, a partial drag springs back, a quick flick dismisses it

- **Tracks the pointer 1:1** while dragging. The backdrop and the scaled page behind follow the drag.
- **Partial drag, release:** it springs back open (below the distance and velocity threshold).
- **Fast flick:** it dismisses on velocity even though the distance was short. See PLAYBOOK §5, Gestures (momentum projection).

Source: https://vaul.emilkowal.ski

## cmdk: command menu
cmdk via shadcn Command: typing filters the list live, deleting restores it, arrow keys move the highlight

- **Live filtering:** groups collapse to the matches ("cal" → Calculator, Calendar) and the first match is highlighted.
- **Keyboard first:** arrow keys move the highlight across groups. There's no animation on these 100+-times-a-day interactions (PLAYBOOK §5, frequency gate).
- `cmdk.paco.me` now redirects to GitHub, so this was recorded from shadcn's `Command` (built on cmdk): https://ui.shadcn.com/docs/components/command

## NumberFlow: animated numbers
NumberFlow: Shuffle rolls each digit into the next value, across currency, percent, negative and CJK compact formats

- **Digit rolls:** each digit translates and fades into its new value. Changed digits move; unchanged ones stay put.
- **Format changes animate too:** `$12,348.43` → `42` → `+39,843%` → `-3,243.5` → `143.52万米` (sign, separators, suffix).

Source: https://number-flow.barvian.me
