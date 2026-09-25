# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

A single-file Erasmus exchange feedback website — *"Erasmus – Schkeuditz Vitalis"* — for
a two-week IT placement in Schkeuditz, Germany (with day trips to Leipzig and Dresden).
Built for a school presentation. Deployed as a static file, GitHub → Cloudflare Pages.

## Files

- `erasmus.html` — **the entire website.** Single file: HTML + CSS + vanilla JS. No
  frameworks, no build step, no external JS/CSS dependencies, no separate files. This is
  the only file that actually deploys.
- `converter.py` — build-time-only helper, run locally, never deployed. Resizes/compresses
  photos and base64-embeds them into `erasmus.html`'s `IMAGES` block. Requires Pillow
  (`pip install pillow --break-system-packages`).
- `manifest.template.json` — template for `converter.py`'s `--manifest` argument.

## Hard constraints — do not violate

- `erasmus.html` stays a single file. No splitting into `.css`/`.js`, no npm/build
  tooling, no CDN `<script>` tags, no frameworks (React/Vue/etc.), no jQuery. Vanilla JS
  only.
- No page scrolling, at any viewport. The whole page fits one screen
  (`html,body{overflow:hidden}`), desktop and mobile both.
- Keep `converter.py` separate from `erasmus.html` — it's a dev tool, not part of the site.

## Architecture (inside erasmus.html's `<script>`)

Three data structures, intentionally decoupled:

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
- **`I18N`** — `{ langCode: { ui: {...}, captions: { photoId: {caption, blurb, alt} } } }`.
  All user-facing text, one block per language. Currently `en`, `de`, `sk`. `blurb` is
  intentionally identical Lorem Ipsum filler across languages for any slot without a real
  caption yet — once a slot gets a real caption, it gets real (translated) blurb text too,
  never lorem ipsum.

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

## Current content state

Photos embedded: `home-1`, `home-3`, `home-4`, `home-5`, `week1-1..4`.
Still placeholder (lorem ipsum blurb, empty `src`): `home-2` (reserved for a guitar
photo), `week1-5`, and everything in `week2`, `leipzig`, `dresden`, `freetime`.

## Caption style

Short `caption` (a few words), one-line `blurb` with actual personality — not corporate,
not generic — `alt` = accurate accessibility description of the real photo content. Match
the tone of whatever's already filled in `I18N.en.captions`. Write all three languages
(en/de/sk) together for a given photo, not English-only-then-backfill.

## Running the converter

```
pip install pillow --break-system-packages
python3 converter.py --html erasmus.html --manifest manifest.json
```

`manifest.json`: `{ "photo-id": "path/to/source/photo.jpg" }` — ids must already exist in
`GALLERY_STRUCTURE`/`IMAGES` (add them there first if new). Unknown ids are skipped with a
stderr warning, not silently dropped or crashed on. The script reports each photo's
encoded size and a running total; treat >15MB combined as the signal to lower
`MAX_DIMENSION` / `JPEG_QUALITY` at the top of `converter.py`, not to switch approach.

## Deployment

Static file, GitHub → Cloudflare Pages, no build command and no output-directory config —
`erasmus.html` is served as-is (set it as Pages' entry point / rename to `index.html`).
