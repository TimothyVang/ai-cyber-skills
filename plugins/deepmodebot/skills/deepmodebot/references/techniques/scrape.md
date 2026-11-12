# scrape

**Use when:** the user asks to scrape, pull, archive, or "get everything" from a web page, video, channel, playlist, or a diagram shown in a video.

1. **Probe the cheapest source first, once.** `read` the URL (YouTube returns description plus transcript), then any repo, doc, or canvas the item links or shows. A diagram on screen usually has a source: check the linked repo's `docs/images/`, and read the address bar in a video frame for a tldraw, Excalidraw, or Figma link. Export from that source rather than screenshotting video.
   Done when you know what the cheap source gives and what it lacks.
2. **Inventory before bulk.** Count the items (`yt-dlp --flat-playlist -J <channel>/videos`, then `/shorts` and `/streams`) and decide scope from the count. Over ~200 page loads or any signed-in fetch → state scope options with time estimates.
   Done when the item count is known and the scope is chosen.
3. **Fix the output layout up front:** `index.md` + `index.csv` (one row per item, newest first, with a status column per field), one Markdown file per item, `_raw/` for resumable JSONL and source JSON. Raw first, render after, so a render bug never costs a refetch.
   Done when the folders and index headers exist.
4. **Pace from the first request.** A bot wall arrives within minutes at 6 concurrent requests and outlives the run. Start at 2 workers with ~1.5 s between requests and backoff of 15 s or more on failure. Every bulk script appends to JSONL and skips ids already done, so a rerun only retries failures.
   Done when the bulk script runs with those limits and skips done ids.
5. **Tell blocked from absent.** An empty transcript or "No transcript available" can mean the IP is walled. Re-probe one item known to have the data. "Sign in to confirm you're not a bot" or `LOGIN_REQUIRED` means blocked; an empty caption track list on a page that loaded means absent.
   Done when every empty result is marked blocked or absent.
6. **Signed-in sessions are a hard stop.** Using the user's browser (relay) or exporting its cookies attributes every request to their account. Ask once with pacing, scope, and an anonymous alternative, then run sequentially at 3 to 5 s per item. Done when the user has answered, or no signed-in fetch is needed.
7. **Prove completeness per item and in total.** Errors reach zero after retries; each transcript's last timestamp lands within seconds of the duration; counts in the index equal the inventory. Name every remaining gap with its reason (no captions, upcoming stream).

## YouTube facts (2026-11)

- **Metadata without auth:** the watch page HTML carries `ytInitialData` even while the player API is walled. `assets/scrape/yt_meta.py` extracts title, date, views, likes, full description, and chapters (`macroMarkersListItemRenderer`) and is resumable.
- **Transcripts when walled:** caption `baseUrl` returns an empty body (needs a PO token), and an in-page `youtubei/v1/get_transcript` POST returns 400 "Precondition check failed". Clicking the description's "Show transcript" button and reading the panel works. `assets/scrape/yt_transcript_relay.js` handles both A/B panel variants (`ytd-transcript-segment-renderer` and `PAmodern_transcript_view` with `transcript-segment-view-model`).
- **Unwalled path:** `yt-dlp --skip-download --write-auto-subs --sub-langs "en-orig,en" --sub-format json3 --write-info-json` gives timed captions plus chapters; group into ~60 s paragraphs under chapter headings, each with a `?t=` deep link.
- **Frames without downloading:** `ffmpeg -ss <sec> -i "$(yt-dlp -f 'bv*[height<=1080][ext=mp4]' -g URL)" -frames:v 1 out.png`.
- **Flat entries** lack date and description; stream entries lack nearly everything. Counts on videos under ~2 days old lag and disagree between sources; stamp them with the scrape date.

## tldraw boards

A shared `tldraw.com/f/<id>` board opens without login, and `window.editor` is exposed. In a managed tab: `editor.store.getStoreSnapshot()` saves a `.tldr` (wrap as `{tldrawFileFormatVersion:1, schema, records}`), `editor.getSvgString(ids, {background:true, darkMode:true, padding:32})` gives vector, `editor.toImage(ids, {format:'png', scale:2, ...})` gives PNG. Group shape ids by page-bounds y-range to export each section separately.

**Done when** every inventoried item has a row, every gap carries a reason, and one rendered file per type was opened and read.
