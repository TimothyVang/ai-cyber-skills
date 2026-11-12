## 5a. Motion graphics and video
Scope: anything rendered to MP4 (launch films, explainers, social clips, docs videos, UI motion captured as video). **§5's 300 ms caps and frequency gates do not apply here; these do.** Rendered video has different physics: the viewer can't interact, sees each beat once, and the clock is music or voice. Evidence:
`TimothyVang/frontend:reference/youtube/747ZnEtsRbg/` (Lukas Margerie's Opus 5.5 harness), `TimothyVang/frontend:reference/youtube/aD9X6Lc3dVk/` (Matt Penny's 10 repos), `TimothyVang/frontend:reference/github/motion-graphics/_batch-motion-graphics-repos.md` (engines, prompt packs, stack), and `TimothyVang/frontend:reference/youtube/channels/_batch-motion-graphics.md` (both creators' channels).

**The prompt is about 10% of the result; the harness is the other 90%:** brand assets, style rules, beat grid, springs, critique loop, sound. [youtube/747ZnEtsRbg 1:02]

1. **Render contract.**
   - Every frame is a pure function of time: `useCurrentFrame()` in Remotion, `seek(t)` in HyperFrames, `window.seek(t)` in plain HTML. No CSS transitions, timers, `requestAnimationFrame` accumulation, `Date.now()`, unseeded random, or integrated physics (bake physics to a per-frame table).
   - Frames render alone and in parallel through headless Chrome, then ffmpeg.
   - **One timeline file** is the single source of truth for picture, music, SFX, captions and checks. Write times in beats or sections; round to frames only at the end.
   - Left alone, Opus builds a zero-dependency single-HTML pipeline, so **name the engine and install its skill**.
   - **Cache every stage artifact to disk** (script, scene list, images, narration, timings) and render through a fixed template that only swaps inputs, so reruns are cheap and never regenerate approved assets by accident. [youtube/channels/_batch-motion-graphics pass 2]
   - [github/motion-graphics/remotion-dev-remotion; github/motion-graphics/heygen-com-hyperframes; github/motion-graphics/lemomo-ai-lemo-opuscar; youtube/747ZnEtsRbg 2:19]
2. **Plan in words, then gate:**
   - Three storylines in words → a spec (goal, output, time, look, objects, motion, shots, **Banned**, QA) with **a number for every adjective** → a storyboard listing each shot's *reads* → a beat map.
   - Show the beat map plus about 6 stills, or a contact sheet of one frame per beat, **before the full render**.
   - Workflow gates: plan → rig → stills → animatic → full pass → polish → audio → render. [github/motion-graphics/heygen-com-hyperframes; github/motion-graphics/JohnHeibel-ClaudeAnimationBase; youtube/747ZnEtsRbg 16:42]
   - **Re-edits start from scratch.** An agent that has seen the source quietly reuses its earlier cut, so say so explicitly ("make these motion graphics from scratch; don't look at any earlier edit of this source"). [youtube/channels/_batch-motion-graphics pass 2]
3. **Director's brief** (the prompt skeleton every strong pack shares) [github/motion-graphics/yihui-dev-awesome-opus5-5-videos; youtube/747ZnEtsRbg 12:44, 17:44]:
   - **Inputs:** product URL, real assets pulled with Playwright, fonts, one accent, format(s), music.
   - **Direction:** the film in one line, references (keep their grammar, never their content), and a **Banned** list that grows after every render.
   - **Structure:** BPM, bars, "something happens on every beat".
   - **Build rules and gotchas.**
   - **Gate.**
   - **Deliverables:** final MP4, loop check, poster frame, contact sheet, source with a README.
4. **Timing (video, not UI)** [github/motion-graphics/diffusionstudio-editor; github/motion-graphics/Vincentwei1021-video-shotcraft; github/motion-graphics/heygen-com-hyperframes]:

   | Element | Duration |
   | --- | --- |
   | Entrance | about 400 ms |
   | Exit | about 200 ms, 25–50% shorter than the entrance |
   | Single move | ≤ 600 ms |
   | Fast move | 0.3–0.6 s, with motion blur |
   | Words / list items | 60–120 ms / 40–80 ms apart |
   | Text hold | 0.3 s per word + 0.5 s (last line ≥ 2 s) |
   | Wordmark hold | ≥ 1 s |
   | Stillness before the payoff | 0.3–0.75 s |
   | Something new | every 2–4 s; a slow zoom alone doesn't count, so cap stills at about 4 s or land a caption, graphic or cut inside longer shots |

   **First drafts run too fast**: budget the holds first. Landed text is **dead still**; motion moves elsewhere (staged reveals, a camera with intent, the UI working).
5. **Easing by role:**
   - Arrivals long-tailed (`cubic-bezier(0.16, 1, 0.3, 1)` / `expo.out`); camera moves in-out; exits accelerate.
   - Springs at damping 0.7–0.85 for a premium feel, 1.0 for product UI. Opacity and color never bounce.
   - Choose one motion voice per brand (energy × tone preset) and keep it across entrances, transitions and holds. [github/motion-graphics/Vincentwei1021-video-shotcraft; github/motion-graphics/heygen-com-hyperframes]
6. **Transitions have a cause:**
   - Use 3–5 kinds per film, each carried by an on-screen object (zoom through a button, object becomes the world, morph, whip, iris from the click).
   - Exit and entry vectors match; cut mid-motion. Worlds never crossfade.
   - Hard cuts only on action, on the beat, or between layout forms (≤ 1/3 of seams).
   - A strong pattern: **one element that never cuts**, where a button morphs through loader → check → chart and back into the button as a seamless loop. [youtube/747ZnEtsRbg 12:17; youtube/aD9X6Lc3dVk]
7. **Beat sync** [github/motion-graphics/librosa-librosa; youtube/747ZnEtsRbg 14:49–15:04]:
   - At 120 BPM, 1 beat = 0.5 s, 1 bar = 2 s, and 15 s = 30 beats. Scenes run 3–4 beats.
   - Downbeats carry scene changes; beats carry SFX; onset peaks place the hits.
   - Fit the beat grid with librosa (least-squares, ≤ 15 ms residual) into `beats.json`. Big moments (logo, CTA) land on downbeats.
   - At most 3 full-frame impacts per film.
   - Verify cut error ≤ 3 frames on the rendered file.
8. **Sound is half the film:**
   - Three layers: bed, foley on visible actions, music. Every effect has a visible cause: a click per cursor press, a whoosh per container morph, one riser → impact.
   - Rotate takes. Cinematic timbres, never game or meme sounds.
   - Master at −14 LUFS, ≤ −1 dBTP. SFX peaks land one frame after the picture.
   - Use a licensed or user-supplied track by default; synthesize music in code only for stylized pieces, and measure it. [github/motion-graphics/_batch-motion-graphics-repos contradictions]
9. **Launch films show the real product doing one real task:**
   - Real UI only (captured at 2× or rendered from real components and tokens). Establish → isolate the action at 1.6–2× → return the result.
   - The cursor is 4–7% of the frame, and its click fires the next beat.
   - The first frame is the thumbnail (never black or a lone logo). The end card sits in the last 5–10%, with the CTA held 1.5–3 s.
   - Results-based films outperformed effects-heavy ones by about 10×. [github/motion-graphics/heygen-com-hyperframes; github/motion-graphics/Vincentwei1021-video-shotcraft]
10. **Type floors, measured on the rendered frame:**
    - Captions ≥ 56 px effective at 1080; secondary text ≥ 28–32 px; headline ≥ 84 px at 1080 wide.
    - ≤ 6 words a line, one line at a time; check at 360–480 px width.
    - Rewrite the copy rather than shrink the type.
11. **Review a film by looking, not by reading code:**
    - Contact sheet → consecutive-frame strips around each key move and seam → full-resolution crops of text → one full-speed viewing with sound.
    - Then a clean-context reviewer who gets only the storyboard and sheets.
    - Write **timestamped notes** (`t · where · problem → change · what stays`) ranked P0–P2, and fix the worst three per round, for at least three rounds.
    - **No numeric film scores** (Lukas's 7–8+ score loop is the dissent): a score finds nothing to fix.
    - The model can't watch in real time, so a human watches the final cut. [github/motion-graphics/heygen-com-hyperframes; youtube/747ZnEtsRbg 18:42]
12. **Stack:**
    - **Remotion** for us (React/TS, reuses our components and tokens; its license is free for companies of up to 3 people, otherwise a company license).
    - **HyperFrames** (Apache-2.0) as the permissive alternative.
    - **Three.js / R3F** for 3D, Rapier baked per frame for physics, postprocessing sparingly.
    - **librosa** for beats; Blender MCP for photoreal hero objects.
    - One *motion* engine per composition. Compositing pre-rendered clips in an editor (CapCut, DaVinci) is fine. Full table: `TimothyVang/frontend:reference/github/motion-graphics/_batch-motion-graphics-repos.md`.
13. **Pipeline safety:** deny `.env` reads, keep MCP sockets on localhost, disable skill telemetry, scope paid-API permissions. [github/motion-graphics/ahujasid-mcp-for-blender; github/motion-graphics/heygen-com-hyperframes]

**From the creators' channels** (101 videos from Lukas Margerie and Matt Penny, each read in full) [youtube/channels/_batch-motion-graphics]:
14. **Keep a video manifest the agent rereads every run:**
    - `design.md`: logo, hex palette, one typeface with weights, real UI screenshots.
    - `frames.md`: how things move, i.e. text in and out, transition types, shot lengths, camera moves, pacing, subtitle style, SFX density.
    - The Banned list.

    Build it by reverse-engineering videos you already approved. **Lock the theme across generated stills:** pass the previous image (or a character or product reference) into each new generation as the style reference, because a style reference alone drifts. Fix palette, mood and font per video.
15. **An asset bank with a dictionary:** each file maps to what it shows or sounds like and when to use it, covering real screenshots, logos, icons, licensed fonts, footage and SFX. Never AI-drawn logos or icons.
16. **Reference grammar from frames:** download the reference, sample a frame every 0.5 s (denser where edits happen), then write a style guide and a shot list. Pick a reference in the same format.
17. **Voice-over first.** Word-level timestamps place every graphic on its word; captions stay editable text. Overlays never cover the speaker's face (compute a face-safe zone). Split multi-speaker audio into one track per speaker that keeps silence while the other talks, so each avatar or layout lines up without manual cutting. SFX go in last, after QA.
18. **Shot budget:**
    - About 6–8 shots per 15 s; generated-video shots run 4–10 s.
    - The hook lands within 3 s; edits are densest at the start.
    - Generate one shot per call so a bad shot regenerates alone.
    - Chain generated clips from each previous clip's real last frame.
    - Iterate on stills, not video, and render a 15 s proof before a long cut.
    - **One visual at a time:** a B-roll image never lands on top of an active motion graphic unless its placement is specified.
    - **Narrated stills:** about 225 words per 90 s (2.5 words/s), structured hook → open loop → story → payoff. Cut silences longer than 0.4 s.
    - **Camera and text instructions are requests, not guarantees.** Video models have zoomed in when asked to zoom out and burned in subtitles unless told "Don't put in subtitles". Constrain with start and end frames, and check direction and text on every clip.
19. **Critique adds a fresh checker:** a separate agent checks overlaps, text size, spelling, the face zone, icons and dead stretches. Both creators score 1–10 and fix anything below 8. Keep §5a.11's timestamped notes as the record; a score may serve only as the stop condition. Expect many rounds (one showcased film took 163 calls and about 7 h).
20. **Models and knobs:**
    - Opus 5.5 on high is the default. Fable 5.2 only for planning, frame-by-frame reference analysis or multi-hour 3D builds (about 2× the price, about 5× slower). Max effort scored lower at about 3× the cost.
    - Tier models by task: the top model only for the motion-graphics and beat pass, where the hard part is choosing what to emphasize; cheaper tiers for setup, cuts, subtitles and images.
    - Expose tweakable values (blur, opacity, timing) as editor or Remotion props instead of re-prompting.
    - Once a look works, save it as a skill that asks for URL, duration and format, and update it after each revision round.
21. **Scroll-scrubbed marketing sections (Persuade surfaces only):**
    - Separate depth layers, or a scrubbed generated video, driven by scroll position, never timers.
    - Sticky pinning: every ancestor stays `overflow: visible`.
    - Parallax within about 15% speed difference; no hover or cursor effects on touch.
    - Under `prefers-reduced-motion`, one poster frame per section with plain text and a working CTA.
    - **Sticky video recipe:**
      - A full-viewport video sits sticky at z 0 inside a fixed scroll runway (about 2,000 px).
      - Text swaps by scroll variant (zero bounce, about 0.7 s).
      - The next section overlaps with rounded top corners.
      - Passed sections dim to opacity 0.2 through an exit state, because scroll transforms can't express exits.
      - On phones, drop sticky and horizontal scroll entirely.
    - This widens §5's "scroll-driven only as progressive enhancement" for marketing pages; product UI stays under §5.
22. **Video embedded in product UI:** muted autoplay only when it's decorative, captions on, a pause control, and a poster frame under reduced motion.
