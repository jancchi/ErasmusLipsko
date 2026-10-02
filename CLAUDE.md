# CLAUDE.md

Guidance for Claude Code when working in this repo.

## What this is

A single-file Erasmus exchange feedback website — *"Erasmus – Schkeuditz Vitalis"* — for
a two-week IT placement in Schkeuditz, Germany (with day trips to Leipzig and Dresden).
Built for a school presentation. Deployed as a static file, GitHub → Cloudflare Pages.

## Files

- `index.html` — **the whole site's code.** One file: HTML + CSS + vanilla JS. No
  frameworks, no build step, no external JS/CSS dependencies. ~112KB. (Was `erasmus.html`;
  renamed so Cloudflare Pages serves it as the entry point.)
- `data/<Gallery>/*.webp` — **the photos**, as ordinary files. `Home/`, `Week1/`,
  `Week2/`, `Leipzig/`, `Dresden/`, `FreeTime/`. ~4.4MB for 43 photos, already
  well-compressed webp. Deployed alongside `index.html`, and it must be committed or the
  live site shows placeholders. Directory names are capitalised and paths are
  **case-sensitive** on Pages, so `data/Week1/...` is not `data/week1/...`.
- `converter.py`, `manifest.template.json` — **no longer used.** They base64-embedded
  photos into `index.html` back when the page carried its own images; that approach was
  dropped in favour of `data/`. Kept only in case the embedding is ever wanted again.
  (Also: this dev machine has only the Microsoft Store Python stub — `python3` and `node`
  both resolve to nothing — so neither could run here anyway.)

## Hard constraints — do not violate

- All the *code* stays in `index.html`. No splitting into `.css`/`.js`, no npm/build
  tooling, no CDN `<script>` tags, no frameworks (React/Vue/etc.), no jQuery. Vanilla JS
  only. (Photos are the one exception — they are files under `data/`, referenced by path.
  That is deliberate, not a slip.)
- No page scrolling, at any viewport. The whole page fits one screen
  (`html,body{overflow:hidden}`), desktop and mobile both — including the postcard's
  back face, which has its own `overflow:hidden` and drops the address block on short
  viewports for exactly this reason.

## Architecture (inside index.html's `<script>`)

Four data structures, intentionally decoupled:

- **`GALLERY_STRUCTURE`** — `{ galleryKey: [photoId, ...] }`. Which photo ids belong to
  which of the 6 galleries (`home`, `week1`, `week2`, `leipzig`, `dresden`, `freetime`),
  in display order. Not fixed at 5 per gallery — add/remove ids freely; the viewer is
  length-agnostic (including the 0-image case, see Gotchas).
- **`IMAGES`** — `{ photoId: { src: "" | "data/Gallery/file.webp" } }`. One entry per id,
  language-independent (a photo isn't translated). Empty `src` → the viewer shows a
  postcard-style placeholder automatically, no request made. Keep each entry to nothing
  but `src`; per-photo extras go in `PHOTO_META`. The block sits inside marker comments
  that are matched **literally, including their `=====` decoration** — the surrounding
  prose deliberately no longer spells the bare marker words, because a loose search for
  them matches the explanatory comment first and splices new content *into* that comment,
  silently commenting out the whole declaration. (This happened; the symptom is
  "IMAGES is not defined" while every text-level grep still looks perfect.)
- **`POSTMARK_PLACE` + `PHOTO_META`** — per-photo data that isn't the image itself.
  `POSTMARK_PLACE` is a per-gallery default place for the cancellation mark;
  `PHOTO_META[id]` optionally overrides `place`, carries `date` as ISO `YYYY-MM-DD`, and
  carries **`w`/`h`, the photo's real pixel dimensions**. An empty `date` just omits the
  date line, so dates can be filled in as the stay goes on. The `w`/`h` are what make the
  card the right size and shape *before* the file loads — see the sizing gotcha below —
  so update them whenever a photo is replaced by one of a different shape. Place names are
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

- `.img-el` sizing lives on the `<img>` itself, not on the `.img-wrap` div around it. A
  plain `<div>` with its own `aspect-ratio` can render wider than its flex parent and
  overflow the postcard border on narrow phones; a replaced element like `<img>` can't.
  Don't move sizing onto `.img-wrap`.
- **How the photo is sized** (this replaced an earlier `width:auto;height:auto` +
  `max-width`/`max-height` + fixed `aspect-ratio:3/2` + `object-fit:cover` setup — don't
  reinstate any part of that without reading this):
  - There is **no fixed aspect-ratio and no `cover`**. The photos are a mix of portrait
    (3:4), landscape (4:3) and square; a 3:2 centre-crop cut the top and bottom off every
    portrait one, heads included. `object-fit:contain` + the real ratio means nothing is
    cropped.
  - The ratio arrives as a CSS custom property `--ar`, set inline per photo by
    `showImage()` from `PHOTO_META`'s `w`/`h`, with a `1.5` fallback for empty slots.
  - The width is `min(66vw, 760px, calc(min(64vh,600px) * var(--ar)))`. The third term is
    the height cap expressed as a width, which is what keeps the photo inside *both* caps.
    **`max-width`/`max-height` cannot do this job any more:** they only preserve an
    image's proportions while width and height are `auto`, and an `auto`-sized `<img>`
    that hasn't loaded has no intrinsic size — so the card would collapse to nothing until
    the file arrived, and stay collapsed if it 404'd. Photos are separate files now, so
    that is a real request, not bytes already in the page. Giving width and height
    explicitly instead would make `max-*` clamp each axis independently and distort the
    box (observed: 760×461 for a photo that should be 346×461).
- A portrait photo makes a portrait card, and the postcard's divided back can't run two
  columns side by side in one — they get too narrow to read. `showImage()` adds
  `.is-portrait` to `.image-frame` when `w < h`, and the back stacks instead. This case
  didn't exist while everything was cropped to 3:2 landscape.
- `.image-frame` needs `min-width:0` — it's a flex item (of `.stage` now), and without
  that, flexbox won't let it shrink below its content's intrinsic width. That's what
  caused arrows to get clipped off-screen on mobile before this was added.
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
- **`.stage` is what keeps the arrows still.** The card is only as wide as its photo, so
  in a plain centred flex row `[arrow][card][arrow]` both arrows slide sideways on every
  navigation — far enough that the next arrow walks out from under the pointer between
  clicks. `.stage` is a fixed-width column the card is centred inside, so the arrows never
  move. Its width is `calc(min(66vw,760px) + 2 * var(--frame-pad))` — the widest a photo
  can be, plus the card's two white borders. If you change `.img-el`'s width caps, change
  this to match or a wide card will overhang the stage and slide under an arrow.
  `.stage` keeps `flex-shrink:1` and `min-width:0` on purpose, so a very narrow phone can
  still compress the row rather than pushing the arrows off-screen (the old mobile bug);
  that compression depends on the viewport, never on which photo is showing, so the
  arrows still hold still while navigating. `.img-el`'s `max-width:100%` is what keeps the
  photo inside the stage when it does compress.
- `--frame-pad` is the card's white border, and it sets **both** `.postcard-front`'s
  padding and `.stage`'s width — they have to agree, so they read from one token. The
  `max-width:420px` query retunes the token rather than overriding the padding rule.
  (It used to be a `.postcard-front{padding:...}` override that had to sit *after* the
  base rule to win on source order; as a token that race can't happen.)
- Both faces stay in the DOM, so `setFlipped()` toggles `aria-hidden` on each; that (not
  `backface-visibility`) is what keeps a screen reader off the hidden side.
- The flip control is a sibling of `.postcard`, not a child — inside it, it would rotate
  away with the card and clicks would double-toggle.

## Current content state

**43 slots, 43 photos — every slot is filled.** No empty `src` and no lorem ipsum left
anywhere. Gallery sizes are **not** 5 each: `home` 5, `week1` 5, `week2` 5, `leipzig` 15,
`dresden` 6, `freetime` 7. The viewer is length-agnostic, so add and remove freely.

The empty-`src` placeholder path and the 0-image gallery guard are therefore no longer
exercised by any current content. **Keep both** — they're what makes it safe to add an id
before its photo exists, which is how every gallery here got built.

- `week2` is the Loxone arc, in this order: at the desks → the Config block diagram →
  the Miniserver in its cabinet → the taped-out demo wall → the finished app.
- `freetime` runs: the two walks from Gut Wehlitz (Antonov, Bismarck tower) → BMW plant
  → the Halle day (market square, the Ľudovít Štúr bust, Halloren chocolate).
- Postmark places now vary within a gallery: `freetime-3/4` are Leipzig, `freetime-5/6/7`
  are Halle, and `home-2` is **a guess** — it's the guitar photo taken at home before the
  trip, and Bratislava was borrowed from `home-4`'s departure board. Correct it to Jano's
  actual town.
- Two files in `data/FreeTime/` have **spaces in their names** (`BMW motorcycle.webp`,
  `Oldest choco shop.webp`), so their `IMAGES` paths carry `%20`. Renaming the files
  without spaces, and fixing the two paths, would be tidier.
- **Leipzig captions are drafted from the photos, not from Jano's account of the day** —
  he said he'd supply the details later. The facts in them (the Bach churches, the
  monument, the Koliba stall) are read off the images; `leipzig-4` is deliberately called
  only "the dark church" because the building wasn't identified with confidence.
- `data/Dresden/dresden_zwinger.webp` is **not** the Zwinger — it's the Katholische
  Hofkirche. The caption says Hofkirche and the note jokes about the filename. Rename the
  file (and its `IMAGES` path) if that ever gets tidied.
- All 43 `PHOTO_META` dates are still `""`, so postmarks show a place but no date.

## Caption style

Short `caption` (a few words), one-line `blurb` with actual personality — not corporate,
not generic — `alt` = accurate accessibility description of the real photo content, and
`note` = two sentences in the same voice, written as an actual message on the back of a
postcard (first person, one concrete detail, a dry aside is welcome). Match the tone of
whatever's already filled in `I18N.en.captions`. Write all three languages (en/de/sk)
together for a given photo, not English-only-then-backfill.

## Adding a photo

No tooling involved any more — it's four edits, all by hand:

1. Drop the file into the right `data/<Gallery>/` folder. Keep it webp and roughly
   1000–1300px on the long edge; the display caps are 760×600 CSS px, so anything much
   larger is wasted bytes.
2. Add its id to `GALLERY_STRUCTURE` in the position you want it shown.
3. Add an `IMAGES` entry with the path (exact case), and a `PHOTO_META` entry with the
   file's real `w`/`h` — without those the card is the wrong shape until the file loads.
4. Add a `captions` entry in **all three** `I18N` blocks.

Ids must exist in all four structures or the gallery will render a fallback with the raw
id as its caption.

## Deployment

Static, GitHub → Cloudflare Pages, no build command and no output-directory config —
`index.html` is served as-is and its name already makes it Pages' entry point.

`data/` must be committed and pushed along with it; it is now part of the deployed site,
not a local scratch folder. Two consequences of photos being files rather than embedded
bytes: paths are **case-sensitive** on Pages though not on Windows, so a wrong-case path
works locally and 404s live; and the page **no longer works offline** — it used to carry
its own images and survive dead venue wifi, which it can't now.
