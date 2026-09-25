# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

A single-file Erasmus exchange feedback website — *"Erasmus – Schkeuditz Vitalis"* — for
a two-week IT placement in Schkeuditz, Germany (with day trips to Leipzig and Dresden).
Built for a school presentation. Deployed as a static file, GitHub → Cloudflare Pages.

## Files

- `index.html` — **the entire website.** Single file: HTML + CSS + vanilla JS. No
  frameworks, no build step, no external JS/CSS dependencies, no separate files. This is
  the only file that actually deploys. (Was `erasmus.html`; renamed so Cloudflare Pages
  serves it as the entry point. `converter.py`'s docstring still says the old name —
  harmless, `--html` has no default.)
- `converter.py` — build-time-only helper, run locally, never deployed. Resizes/compresses
  photos and base64-embeds them into `index.html`'s `IMAGES` block. Requires Pillow
  (`pip install pillow --break-system-packages`). **Note:** the dev machine currently has
  only the Microsoft Store Python stub — `python3` and `node` both resolve to nothing, so
  the converter can't run here until real Python is installed.
- `manifest.template.json` — template for `converter.py`'s `--manifest` argument.

## Hard constraints — do not violate

- `index.html` stays a single file. No splitting into `.css`/`.js`, no npm/build
  tooling, no CDN `<script>` tags, no frameworks (React/Vue/etc.), no jQuery. Vanilla JS
  only.
- No page scrolling, at any viewport. The whole page fits one screen
  (`html,body{overflow:hidden}`), desktop and mobile both.
- Keep `converter.py` separate from `index.html` — it's a dev tool, not part of the site.

## Architecture (inside index.html's `<script>`)

Four data structures, intentionally decoupled:

- **`GALLERY_STRUCTURE`** — `{ galleryKey: [photoId, ...] }`. Which photo ids belong to
  which of the 6 galleries (`home`, `week1`, `week2`, `leipzig`, `dresden`, `freetime`),
  in display order. Not fixed at 5 per gallery — add/remove ids freely; the viewer is
  length-agnostic (including the 0-image case, see Gotchas).
- **`IMAGES`** — `{ photoId: { src: "" | "data:image/jpeg;base64,..." } }`. One entry per
  id, language-independent (a photo isn't translated). Empty `src` → the viewer shows a
  postcard-style placeholder automatically, no network request. **`converter.py` rewrites
  entries here with a regex matching the literal pattern `"id": { src:"..." }`**, inside
  the `/* ===== IMAGES:START ===== */` … `IMAGES:END` markers. Don't hand-reformat that
  block's spacing or the script stops matching.
- **`POSTMARK_PLACE` + `PHOTO_META`** — the place/date on the postcard's cancellation mark.
  `POSTMARK_PLACE` is a per-gallery default place; `PHOTO_META[id]` optionally overrides
  `place` and carries `date` as ISO `YYYY-MM-DD`. An empty `date` just omits the date line,
  so dates can be filled in as the stay goes on. **This is deliberately NOT a field on
  `IMAGES`** — `converter.py`'s regex expects each `IMAGES` entry to contain nothing but
  `src`, so any extra per-photo data has to live in its own structure. Place names are
  intentionally untranslated (a real postmark shows the local name).
- **`I18N`** — `{ langCode: { ui: {...}, captions: { photoId: {caption, blurb, alt, note} } } }`.
  All user-facing text, one block per language. Currently `en`, `de`, `sk`. `blurb` is the
  one-liner under the photo on the card's front; `note` is the longer handwritten message
  on its back and is **optional** — a slot without one falls back to its `blurb`. `blurb`
  is intentionally identical Lorem Ipsum filler across languages for any slot without a
  real caption yet (and such a slot has no `note` at all) — once a slot gets a real
  caption, it gets real (translated) blurb and note text too, never lorem ipsum.

Adding a language: copy one `I18N` block, translate every value, add the code to the
`LANGUAGES` array — the footer's language switcher builds itself from that array, no
other change needed.

Nav labels, footer, empty-state text etc. are wired via `data-i18n="path.in.ui"`
attributes plus a generic `applyTranslations()` walker in the script. A new UI string is
one attribute + one dict key, nothing else.

## Known gotchas — don't regress these

- `.img-el` sizing lives on the `<img>` itself (`max-width`/`max-height`/`aspect-ratio`,
  `width:auto;height:auto`), not on the `.img-wrap` div around it. A plain `<div>` with
  its own `aspect-ratio` can render wider than its flex parent and overflow the postcard
  border on narrow phones; a replaced element like `<img>` can't. Don't move sizing onto
  `.img-wrap`.
- `.image-frame` needs `min-width:0` — it's a flex item, and without that, flexbox won't
  let it shrink below its content's intrinsic width. That's what caused arrows to get
  clipped off-screen on mobile before this was added.
- The 0-image-in-a-gallery case is real UI, not dead code (`render()` guards it, arrows
  get `disabled`) — keep it even though every gallery currently has content.
- `showImage()` has two paths (real `src` → load/error listeners handle the fade + missing
  fallback; empty `src` → `removeAttribute` + immediate placeholder, no network request).
  Read both before changing either.
- **The postcard flip's 3D chain** is `.image-frame` (`perspective`) > `.postcard`
  (`transform-style:preserve-3d`) > two `.postcard-face` children, both with
  `backface-visibility:hidden`. Two traps: (1) never put `overflow` (or `filter`/
  `clip-path`) on `.postcard` itself — a non-visible overflow on the same element that
  carries `preserve-3d` flattens the 3D context and the flip degrades to a flat fade;
  overflow on an *ancestor* (`.page`) is fine. (2) The front face sits in normal flow and
  drives the card's box while the back is `position:absolute; inset:0` to match it — this
  is what preserves the `.img-el`-drives-sizing rule above, so don't give `.postcard` or
  either face its own `width`/`aspect-ratio`.
- `.postcard-front`'s base `padding` is declared *after* the `@media (max-width:420px)`
  block that used to override `.image-frame`'s padding, so that mobile override now lives
  in the postcard section's own `max-width:420px` query. Equal specificity — source order
  is the only thing deciding it. Don't move the base rule below its override again.
- Both faces stay in the DOM, so `setFlipped()` toggles `aria-hidden` on each; that (not
  `backface-visibility`) is what keeps a screen reader off the hidden side.
- The flip control is a sibling of `.postcard`, not a child — inside it, it would rotate
  away with the card and clicks would double-toggle.

## Current content state

Photos embedded: `home-1`, `home-3`, `home-4`, `home-5`, `week1-1..4`.
Still placeholder (lorem ipsum blurb, no `note`, empty `src`): `week1-5`, and everything in
`week2`, `leipzig`, `dresden`, `freetime`.
Real text but no photo yet: `home-2` (reserved for a guitar photo) — it has a real
caption/blurb/note in all three languages, just an empty `src`.
Postcard backs: real `note` text in en/de/sk for `home-1..5` and `week1-1..4` (the nine
slots with real captions). All 30 `PHOTO_META` dates are still `""`.

## Caption style

Short `caption` (a few words), one-line `blurb` with actual personality — not corporate,
not generic — `alt` = accurate accessibility description of the real photo content, and
`note` = two sentences in the same voice, written as an actual message on the back of a
postcard (first person, one concrete detail, a dry aside is welcome). Match the tone of
whatever's already filled in `I18N.en.captions`. Write all three languages (en/de/sk)
together for a given photo, not English-only-then-backfill.

## Running the converter

```
pip install pillow --break-system-packages
python3 converter.py --html index.html --manifest manifest.json
```

`manifest.json`: `{ "photo-id": "path/to/source/photo.jpg" }` — ids must already exist in
`GALLERY_STRUCTURE`/`IMAGES` (add them there first if new). Unknown ids are skipped with a
stderr warning, not silently dropped or crashed on. The script reports each photo's
encoded size and a running total; treat >15MB combined as the signal to lower
`MAX_DIMENSION` / `JPEG_QUALITY` at the top of `converter.py`, not to switch approach.

## Deployment

Static file, GitHub → Cloudflare Pages, no build command and no output-directory config —
`index.html` is served as-is, and its name already makes it Pages' entry point.
