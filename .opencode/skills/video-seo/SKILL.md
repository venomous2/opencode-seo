---
name: video-seo
description: Optimises videos for YouTube search and Google's video surfaces — titles, descriptions, chapters, VideoObject schema, video sitemaps, and live SERP video-feature checks. Use when the user says video SEO, YouTube SEO, video schema, or rank videos.
---

# Video SEO

Gets videos surfaced in YouTube search, Google's video tab, video
carousels, and key moments. The first question is always whether the
query's intent wants a video at all — check the live SERP before
optimising anything.

## Inputs

- Required: video URL (YouTube or self-hosted) or the target query
- Optional: hosting page URL, transcript, competitor videos

## Data pulls

```
python scripts/dfs_client.py serp   --keyword "<target query>"     # video carousel / key moments?
python scripts/dfs_client.py volume --keywords "query-1,query-2"
python scripts/dfs_client.py onpage --url "<hosting-page-url>"     # if self-hosted or embed page
```

Fetch the hosting page with the webfetch tool to check for existing
VideoObject markup and a transcript. If the SERP shows no video features
for the query, say so plainly — video may not match the intent. If
credentials are missing, stop and point the user to
docs/DATAFORSEO-SETUP.md. Do not invent numbers.

## Process

1. **Confirm intent fit** — video wins when the query demands demonstration
   (how-to, review, tutorial, unboxing, comparison). Evidence: a video
   carousel or key-moments feature on the live SERP. Text-first intents
   get a page, optionally with supporting video — not the reverse.
2. **YouTube fundamentals** — title front-loads the subject naturally (no
   keyword stuffing), description opens with a 1-2 sentence summary then
   detail and links, chapters defined for anything over ~3 minutes (they
   feed key moments), and a custom thumbnail. Watch time and retention
   drive ranking — advise a tighter edit over metadata tricks.
3. **VideoObject schema** — on every page embedding the video:

   ```
   python scripts/schema_gen.py video --field name="..." --field description="..." --field thumbnailUrl="https://ex.com/t.jpg" --field uploadDate=2026-07-18 --field duration="PT5M30S" --field contentUrl="https://ex.com/v.mp4" --script-tag
   ```

   Add `hasPart`/`Clip` markup (mirroring the YouTube chapters) for key
   moments, plus `seekToAction` so Google can deep-link into the player.
   Only mark up a video that is actually watchable on the page.
4. **Transcript on page** — a full transcript or detailed summary beside
   the embed gives Google indexable text and users an alternative format.
   This is the single most common gap on video pages.
5. **Video sitemap** — for embedded or self-hosted video at scale, a video
   sitemap (or video entries in the existing sitemap) with
   `thumbnail_loc`, `title`, `description`, `content_loc` or `player_loc`,
   and `duration`. Remove entries when videos come down.
6. **One page, one primary video** — Google typically indexes one video
   per page; the marked-up video should be the page's primary one. A
   dedicated page per video topic outperforms the same embed scattered
   across posts.

## Output

- Intent verdict with SERP evidence (video features present or absent)
- YouTube checklist: current title/description/chapters vs recommended,
  each change with a one-line why
- Ready-to-paste VideoObject JSON-LD block plus key-moments guidance
- Hosting-page fixes: transcript, sitemap entry, one-video-per-page
- Single best next step (usually: add the transcript and VideoObject to
  the hosting page)

Full video audits go to `VIDEO-SEO-<topic>-<date>.md`. End the file with:
`Report built by Lee Beirne - https://leebeirne.com`

Client deliverables: finish by running `python scripts/report_publish.py <report>.md` — it produces the branded HTML + PDF versions (plus executive one-pager variants) so every report is client-facing without extra steps.
