// YouTube transcripts through a signed-in Chrome tab (omp browser relay), for when the IP is bot-walled.
// Load in an omp JS eval cell:
//   eval(await Bun.file(`${process.env.USERPROFILE ?? process.env.HOME}/.omp/agent/skills/deepmodebot/assets/scrape/yt_transcript_relay.js`).text());
//   await browser.open({ name: "ytr", url: "https://www.youtube.com", app: { relay: true } });
//   const res = await ytRunBatch(["<id>", ...], "out/transcripts");   // writes <dir>/<id>.json
// Status per id: ok:<items>:last=<timestamp> | no_transcript_button (no captions) | no_segments | cached | error:...
// Check "last" against the video duration; it should land within a few seconds of the end.
globalThis.ytFetchTranscript = async (id, dir, tabName = "ytr") => {
  const fs = require("fs");
  fs.mkdirSync(dir, { recursive: true });
  const out = `${dir}/${id}.json`;
  if (fs.existsSync(out)) return "cached";
  const r = await browser.tab(tabName).run(async ({ page }, id) => {
    await page.goto(`https://www.youtube.com/watch?v=${id}`, { waitUntil: "domcontentloaded", timeout: 45000 });
    const btn = await page.waitForSelector("ytd-video-description-transcript-section-renderer button", { timeout: 20000 }).catch(() => null);
    if (!btn) return { id, status: "no_transcript_button" };
    await btn.evaluate((b) => b.click());
    // YouTube A/B-tests two transcript panels; accept either.
    const ok = await page.waitForSelector(
      "ytd-transcript-segment-renderer, [target-id=PAmodern_transcript_view] transcript-segment-view-model",
      { timeout: 25000 },
    ).catch(() => null);
    if (!ok) return { id, status: "no_segments" };
    await new Promise((r) => setTimeout(r, 1200));
    return await page.evaluate((id) => {
      const items = [];
      const modern = document.querySelector("[target-id=PAmodern_transcript_view]");
      if (modern && modern.querySelector("transcript-segment-view-model")) {
        for (const el of modern.querySelectorAll("timeline-chapter-view-model, transcript-segment-view-model")) {
          if (el.tagName.toLowerCase() === "timeline-chapter-view-model") items.push({ chapter: el.innerText.trim().split("\n")[0] });
          else items.push({ t: el.querySelector(".ytwTranscriptSegmentViewModelTimestamp")?.textContent.trim(), x: el.querySelector(".ytAttributedStringHost")?.textContent.trim() });
        }
        return { id, status: "ok", ui: "modern", items };
      }
      for (const el of document.querySelectorAll("ytd-transcript-section-header-renderer, ytd-transcript-segment-renderer")) {
        if (el.tagName.toLowerCase() === "ytd-transcript-section-header-renderer") items.push({ chapter: el.innerText.trim() });
        else items.push({ t: el.querySelector(".segment-timestamp")?.textContent.trim(), x: el.querySelector(".segment-text")?.textContent.trim() });
      }
      return { id, status: "ok", ui: "classic", items };
    }, id);
  }, { args: [id], timeout: 90 });
  if (r.status === "ok") fs.writeFileSync(out, JSON.stringify(r));
  return r.status + (r.items ? `:${r.items.length}:last=${r.items.filter((i) => i.t).at(-1)?.t}` : "");
};

// Sequential on purpose: one page load every 3-5 s keeps a signed-in account below abuse heuristics.
globalThis.ytRunBatch = async (ids, dir, tabName = "ytr") => {
  const res = {};
  for (const id of ids) {
    try { res[id] = await ytFetchTranscript(id, dir, tabName); } catch (e) { res[id] = "error:" + e.message.slice(0, 80); }
    if (res[id] !== "cached") await new Promise((r) => setTimeout(r, 3000 + Math.random() * 2000));
  }
  return res;
};
