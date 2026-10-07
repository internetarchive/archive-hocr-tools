# EPUB deriver punch list

- **LANG** — Every page declares `lang="None"` (`bin/hocr-to-epub:671`) and the package carries no `dc:language`, so emit a real tag or omit the attribute instead of stringifying `None`, and stop joining multiple languages into one invalid tag at `:353`.
- **PAGENAV** — There are no page breaks, no `page-list` and no `pageTargets` while the bound-in notice promises page navigation, so read the printed numbers out of the scandata the deriver already parses and emit them with a `pageBreakSource`.
- **TOC** — The whole book is a single nav entry added only to silence an epubcheck `navMap incomplete` error (`:699`), so split at chapters rather than at scanned leaves and add a nested ToC plus landmarks.
- **READORDER** — Blocks are emitted in hOCR document order with no reordering pass, so two-column pages read out of order and the reader cannot trust the linear text at all.
- **ALT** — Alt text is a book-wide counter (`alt="Image %u"`, `:658`), so use the printed caption where OCR found a usable one and reserve `alt=""` for genuinely decorative images, since empty alt asserts the image carries no information.
- **META** — `accessibilityFeature` is hardcoded to `none` (`:494`), which lets the file be filtered out of accessible-catalogue search before anyone opens it, so derive the list from what was actually emitted.
- **WCAG** — The summary claims WCAG 2.0 Level A unconditionally (`:469`) on a file with 459 Ace violations, and a conformance claim should be the output of a check rather than a constant.
- **STRUCT** — Zero headings, `<hr>`, `<aside>`, `<em>` or `<strong>` means footnotes cannot be switched off and scene breaks vanish into paragraph boundaries, so emit `aside epub:type="footnote"`, `<hr>` for breaks, and landmarks for the rest.
- **IMGPOS** — Images are appended after the page's text (`:658`), so an illustration set mid-page is announced at the end of the page, detached from its caption and context.
- **PROSE** — Already partly fixed at HEAD by `6a78901` (one `<p>` per hOCR block rather than per page), leaving only book-relative 75th-percentile gap splitting for scans where a block spans a whole column.
- **HYPHEN** — Any trailing `-` or `¬` at a line end is deleted and the words joined, which is wrong for hard-hyphenated compounds split across a line and has no dictionary check behind it.
- **BLANKS** — Every `ocr_photo` box is cropped with no emptiness test (`:647`), shipping plate versos, show-through and scanner foam as illustrations, so measure each crop before keeping it.
- **CONFWARN** — The prepended "this page is estimated to be only 43.21% accurate" warning (`:640`) is announced mid-reading as a number the reader cannot act on and has no way to dismiss.
- **REPASS** — A stronger model re-reading from the page images recovers what OCR cannot, including italic prefaces, captions and emphasis, at roughly $0.028 per printed page, and must be queued by how often print-disabled patrons open the book because `x_wconf` does not separate bad pages from good ones.
- **REDO** — Give patron services a one-click rebuild and tell the patron at the point of download that they can report a bad EPUB, because the validators pass these files and the reader is the only reliable detector we have.
- **NOIMG** — Offer a text-only EPUB on request so text can ship on its own schedule while image handling stays unsettled, but not by default, since the plates are the reason some editions are remembered.
- **FILEDATE** — Put the build date in the filename so a patron or admin can tell which copy is current, keeping `ITEM.epub` as a stable alias and leaving `dc:identifier` untouched across rebuilds.
- **ABBYY (dropped)** — The deriver in use reads `_hocr.html` rather than ABBYY XML, so the claim that it cannot run on items without `_abbyy.gz` is refuted, though one test item should be checked against a few more scan dates before closing.

---

## Status

### Current status (as of Round 2)

| Item | Status | Notes |
|------|--------|-------|
| LANG | ✅ done | real `dc:language` + page `lang` (`28af5eb`, `7db9fcd`); `xml:lang` on the OPF `<package>` added via a `LangEpubWriter` subclass |
| PAGENAV | ✅ done | page-list from scandata page numbers + `pageBreakSource` (`5ce98b5`, `4fb6977`) |
| TOC | ✅ done | real ToC + landmarks (`a42c5ce`); running-head pollution fixed by the furniture pass |
| ALT | ✅ done | `alt=""` (`766f38a`) |
| META | ✅ done | features derived from emitted content (`289c21f`, `4fb6977`) |
| WCAG | ✅ done | false conformance claim removed (`ae92103`); full checker still a TODO |
| NOIMG | ✅ done | `--images` allowlist (`8a78e5c`); cover now decoupled from it (`4fb6977`) |
| PROSE | ✅ done | `hocr-fix-paragraphs` (`1dab0e6`) |
| STRUCT | ✅ done | headings + `<hr>` (`dfd819e`); running-head furniture pass + `THE BOOK OF X` vocabulary (`this round`) |
| FILEDATE | 🟡 partial | build date emitted in the front-matter notice text; filename left to the caller by decision |
| READORDER | ⬜ open | multi-column reading order |
| IMGPOS | ⬜ open | image position vs caption |
| HYPHEN | ⬜ open | soft-hyphen join correctness |
| BLANKS | ⬜ open | empty-crop detection |
| CONFWARN | ⬜ open | low-confidence warning UX |
| REPASS | ⬜ open | model re-OCR pass |
| REDO | ⬜ open | one-click rebuild + patron report |
| FILEDATE | ⬜ open | build date in filename |

### New tasks (from Round 2 — P&P + Book of Love feedback)

1. **Running-head furniture fix (the big one).** DONE — see the work log
   entry "Running-head furniture pass". `classify()` no longer lets
   repeated top-of-page labels through to the headings/ToC, and
   `structuralNavigation` is no longer over-claimed on P&P (60 ToC entries,
   exactly one `PREFACE`) or Book of Love (102 entries, all 11 section
   names present).
2. **`xml:lang` on the OPF `<package>` element (fix 8).** DONE —
   `LangEpubWriter` subclass injects `xml:lang` on the package element
   when a language is known; omitted (like the page-level attribute) when
   none is.

### Reproduction runbook

Iterate against the Huckleberry Finn test item in `epub-improvement-files/` using the `venv3.14` virtualenv. Full run takes ~30s.

```bash
cd /home/merlijn/archive/archive-hocr-tools
PYTHONPATH="$PWD" ./venv3.14/bin/python bin/hocr-to-epub \
  -f epub-improvement-files/adventuresofhuck0000mark_f2t7_hocr.html \
  -s epub-improvement-files/adventuresofhuck0000mark_f2t7_scandata.xml \
  -i epub-improvement-files/adventuresofhuck0000mark_f2t7_jp2.zip \
  -o /tmp/epubout/out.epub \
  -w /tmp/epubwork > /tmp/epubout/run.log 2>&1
```

Notes:
- No `_meta.xml` in the fixture, so metadata/dc:language arrive empty (relevant to LANG/ALT).
- No `derivermodule` in this checkout, so the `_meta.xml`/`_scandata.xml` helpers fall through the try/except; scandata is still parsed for skip/cover pages (PAGENAV source).
- Pillow opens the `.jp2` (no kakadu needed); `use_kakadu` is off by default.
- Inspect the unpacked result with `cd /tmp/epubout && mkdir -p ex && cd ex && unzip -q ../out.epub`.

### Baseline (first successful run, 2026-10-05)

- 460 hOCR pages -> 458 `page_*.html` + `notice.html`; 56 image crops.
- `LANG`: every page emits `lang="None" xml:lang="None"` (no `dc:language` present).
- `ALT`: `alt="Image <book-wide counter>"`.
- `TOC`: `nav.xhtml` has exactly one `<li>`; no `page-list`/`landmarks`.
- `STRUCT`: zero `h1-6`/`em`/`strong`/`hr`/`aside` in any page.
- `CONFWARN`: warnings like `Warning for page due to low confidence: 47.43%` and the `This text ... only X% accurate` string are emitted into the reading flow.
- `BLANKS`/`IMGPOS`: log shows full-page crops e.g. `[0.0, 0.0, 1665.0, 2589.0]`; all images are appended after the page text.

### Work log

_(append one entry per change as we go; mark the punch-list item.)_

- [x] Reproducible full run established (above).
- [x] ALT — Images now emit `alt=""` instead of a book-wide counter (`alt="Image N"`). Verified: all 56 images in the test output now carry `alt=""`. (Commit `766f38a`.) Note: empty alt asserts the images are decorative; a real caption pass is still open.
- [x] NOIMG — Added a repeatable `--images` allowlist (`photos`, `cover`); unset = none. The photo loop is gated on `photos`, the cover crop on `cover` (plus a `img_stack is not None` guard so a missing stack can't crash or leave a dangling `cover` spine entry). `has_images` still tracks only content photos, so a cover-only build reports as text-only. Verified all four modes (none / cover / photos / both) for photo count, cover presence, spine, and accessibility metadata. (Commit `8a78e5c`.)
  - Note: `internetarchive-deriver-module` is now installed in `venv3.14`, so scandata is parsed for real (skip_pages confirmed active). The huck fixture's own cover is `clothCover=true`, which the existing cloth-cover heuristic clears; verified the cover actually gets set using a non-cloth-cover scandata (`alienatemyhomewo0004swar`, covers=[1,20]) against the huck stack: `--images cover` -> cover+spine, `--images photos,cover` -> photos+cover.
  - Breaking change: the tool's default is now text-only (no images). Callers that want images must pass `--images photos`/`--images cover` explicitly.
- [x] LANG — Stopped emitting `lang="None"`. Language now comes from the explicit `language` metadata, falling back to `ocr_detected_lang` when `ocr_detected_lang_conf >= 0.9` (threshold in `_ocr_detected_language_confident`). Multiple languages are emitted as separate `dc:language` entries (first = primary for the HTML `lang`), not joined into one tag. When no language is known, a `PageHtml` subclass omits `lang`/`xml:lang` entirely. Verified: single (`ocr_detected_lang=en` -> page `lang=en` + `dc:language=en`), none (no meta -> page omits lang, no `dc:language`), multiple (`['eng','spa']` -> page `lang=en`, `dc:language` en + es). (Commit `28af5eb`.) Threshold raised to 0.9 in commit `7db9fcd`.
  - Note: the nav document still inherits ebooklib's default `book.language` (`en`) in the no-language case; pages are the focus here. Per-page language (each page's own dominant language) was deferred in favor of the single book-wide primary.
- [x] WCAG — Removed the hardcoded "meets WCAG 2.0 Level A" sentence from the `accessibilitySummary` (it was a constant, not the output of a check, and false against Ace). Kept the rest of the accessibility metadata; no `dcterms:conformsTo` is emitted, so the book now makes no conformance claim. (Commit `ae92103`.)
  - TODO (later) — to *properly* claim conformance, minimally: (1) run a checker (DAISY Ace / `pyace`) on the generated EPUB; (2) parse violations by severity and map them to a WCAG version + level; (3) emit the formal claim `dcterms:conformsTo` = the WCAG version+level URL, plus `accessibilityFeature: conformsWithNoExceptions` (or `conformsWithExemption` + exemption URL); (4) only claim the level actually achieved, re-running on every rebuild; (5) reflect the real result in the summary. This adds a heavyweight validation stage (Java/`pyace` runtime + time) to the deriver.
- [x] META — `accessibilityFeature` is now derived from what the build emits instead of hardcoded `none`. Currently claims `displayTransformability` when there is reflowable text; falls back to `none` only when nothing applies. Future items plug in with one `if` each keyed off their emit-site flag (ToC -> `tableOfContents`, page-list -> `pageBreakMarkers`/`printPageNumbers`, meaningful alt -> `alternativeText`, headings/landmarks -> `structuralNavigation`). (Commit `289c21f`.)
- [x] PROSE — Built a separate `hocr-fix-paragraphs` tool (fixes the source hOCR rather than adding paragraph detection to `hocr-to-epub`, per the preference to keep the epub tool a simple renderer). It splits an `ocr_par` into multiple `ocr_par`s wherever the vertical gap between adjacent lines exceeds a threshold measured across the whole book. `hocr-to-epub` consumes the fixed hOCR unchanged. (Commit `1dab0e6`.)
  - Findings on the fixture: the tall full-column prose blocks are already genuine single paragraphs (Tesseract segmented the prose well) — nothing to split there. The blocks with real gaps are short *structural* ones: chapter headings (`CHAPTER I` + title), title pages, and book-title lists. Default `min-height-frac` was set to `0.0` after finding that a `0.05` guard cut out the chapter headings (they are only ~0.04 page height).
  - Threshold: the gap distribution has a big peak at normal line spacing (~0.2) and a tail of real breaks (0.7+) with a valley at ~0.68. The default `--gap-percentile 0.99` lands at ~0.649, right at that valley. Otsu (0.425) and 1-D k-means (0.420) were tested and are worse — they land on the shoulder of irregular line spacing and over-split (~385 splits).
  - Result with defaults: 88 clean splits; e.g. the contents page `CHAPTER I Civilizing Huck…` becomes `CHAPTER I` / `Civilizing Huck…`. Knobs: `--gap-threshold` (absolute), `--gap-percentile`, `--min-height-frac`.
  - Caveat: this is a heuristic; the real fix is better paragraph detection in the source hOCR. The tool is a stopgap that can be tuned per book.
- [~] STRUCT — Headings and separators now emitted. New `hocr/structure.py` holds the classification as pure functions (`body_size`, `classify`, `front_matter_type`, `is_caps_heading`) so it can be reused or inlined if it stays fragile. `hocr-to-epub` samples the body font size and classifies each block at emit time. (Commit `dfd819e`.)
  - Signals checked on the fixture: line `x_size` is present but **unreliable** — chapter headings are set *smaller* than body (33–41 vs body 50), so the size heuristic misses them; the only lines ≥1.35× body are title-page OCR gibberish. The robust signal is the text pattern (`CHAPTER_RE`). `ocr_caption` is present but empty (dead end); `ocr_separator` (687) are thin rules, mostly running-head underlines in the top page decile.
  - Approach borrowed from the `ocr2any` project (`/tmp/access/ocr2any`, see `ocr2any-summary.md`): heading = short (≤80) AND (`CHAPTER_RE` OR size≥1.35×body), OR all-caps; level 1 if `CHAPTER_RE` or size≥1.8×body else 2; `RUNNING_HEAD_RATIO` keeps small all-caps running heads from becoming headings. Pattern is trusted first because size is unreliable. English-only vocabulary for now (non-English chapter words under-promote to size detection).
  - Separators → `<hr>`: skip the running-head zone (top 15% of page) and thick non-rule blocks; insert each before the first block below it so paragraph reading order is preserved (no global re-sort, which would break multi-column pages).
  - Result on fixture (after `hocr-fix-paragraphs`): 91 `<h1>`, 30 `<h2>`, 111 `<hr>`, 2994 `<p>` (total blocks unchanged, just reclassified). Contents page reads `CONTENTS`→h1, `CHAPTER I`→h1, title→p. Tests in `tests/test_structure.py` (27).
  - **Not yet done**: front-matter landmarks. `front_matter_type()` detects `contents→toc`, `preface→preface`, `list of illustrations→loi`, etc., but the EPUB landmark wiring (`epub:type` on pages / landmarks nav) overlaps the TOC punch-list item and is deferred to it. Lists and blockquotes also deferred (high false-positive risk without a layout model).
  - Note: `ocr2any` does **not** require docling — its heading detection has a pure-hOCR path (`label is None`); docling only produces the optional layout JSON overlay. We stayed on that pure path.
- [x] TOC — Replaced the single dummy nav entry (`book.toc = (front_matter_epub,)`) with a real ToC built from the level-1 headings, page-level links, plus landmarks and the `structuralNavigation` accessibility feature. (Commit `a42c5ce`.)
  - ToC = h1 headings, each `epub.Link` pointing at the page it starts on (page-level, per the decision — no heading anchors, no printed page numbers). h1-only (h2 is display/title-page noise here, not sub-sections).
  - **Printed-contents-page problem**: the contents pages (15–18) list every chapter as h1, so a naive ToC pointed at the contents page and duplicated. Title-based dedup failed because the contents OCR is noisy (`CHAPTER IX PAGE`, `CHAPTER. XXVIII`). Fixed structurally instead: a page with **>1 chapter heading is the printed contents page → skip it**; real chapters each open a page with a single heading. The `toc` landmark is pointed at the contents page found via the `CONTENTS` heading.
  - ToC inclusion filtered by `is_toc_entry()` (matches `CHAPTER_RE` or a front-matter type) so large-font display junk (`z >`) stays out while `ILLUSTRATIONS`/chapters stay in.
  - Landmarks via `book.guide` (ebooklib maps it to the EPUB3 landmarks nav): `cover` (if set), `toc` (→ contents page), `bodymatter` (→ first chapter), and detected front-matter sections. `structuralNavigation` added to `accessibilityFeature` when a ToC exists.
  - Result on fixture: 44-entry ToC — `ILLUSTRATIONS`→p21, `CHAPTER I`→p23 … `CHAPTER THE LAST`→p448; landmarks `toc`→p15, `bodymatter`→p23. NCX (EPUB2 fallback) gets the same 88 navPoints. Tests unchanged (7 pre-existing failures).
  - Relationship to PAGENAV: the ToC and the page-list are separate nav structures that share the page files as targets and the scandata `pageNumData` (leaf→printed number) map. The ToC was built first; PAGENAV (page-list + `pageBreakSource`) is the adjacent follow-on that reuses that scandata map. Printed page numbers were deliberately left out of the ToC for now.

### PAGENAV — page numbers from scandata (done)

**Decision:** use the **scandata page-entry `pageNumber`** as the source (not
`_page_numbers.json`). The scandata is the canonical single source, the maker
already loads it, and it carries `addToAccessFormats`. Numbers are used
**as-is — no interpolation** (any correction belongs upstream in the
pagenumber tool).

**Implementation:**
- Build a leaf → printed-number map from the scandata page entries, skipping
  leaves with `addToAccessFormats="false"` and empty numbers.
- Prepend a pagebreak marker to each numbered page. **Current form (after
  Round 2):** an empty `<span epub:type="pagebreak" role="doc-pagebreak"
  aria-label="N" id="pgLEAF"></span>` (inline `xmlns:epub` so it is
  self-contained). The number lives in `aria-label`, not as visible text —
  see the Round 2 section for why.
- ebooklib's `epub3_pages` (default on) scans those markers and builds the
  **page-list** nav automatically.
- (The original `.pagebreak` folio CSS was removed in Round 2 when the marker
  became an empty span.)

**Result on the fixture:** 407 pagebreak markers → 407 page-list entries
(`page_24.html#pg24` → 2 … `page_450.html#pg450` → 388).

**Known data quirk (kept as-is):** the scandata page entries carry ~40
**duplicated printed numbers** in irregular regions (e.g. page 11 on both
leaf 33 and leaf 35), so 20 page-list labels appear twice. These come from
the page-entry numbers interpolating across the 3-leaf/1-page gaps and
colliding with the next confirmed anchor.

**Future option:** reconcile duplicates against the `pageNumData`
**assertions** (the confirmed anchors) and keep the asserted leaf per number,
which would make every page-list target unique. Not done now per the
"use as-is" decision.

**`pageBreakSource`:** now emitted (added in Round 2 — required by Ace once a
page-list ships). Composed from `meta.xml` title/publisher/date + the
archive.org access URL; the full-citation format was kept by decision.

**Remaining:** printed numbers in the ToC entries themselves.

## Round 2 — P&P / Book of Love feedback (Ace 1.3 + epubcheck + Kobo)

The colleague ran the branch against two more books — `prideprejudice00aust`
and `bookoflovenovel0000link` — through Ace 1.3, epubcheck, and a Kobo device
(feedback in `/tmp/Epub Branch Fixes 10_6.pdf`). Both are now in
`epub-improvement-files/` (hOCR + meta + scandata, no jp2). All reported
issues reproduced on P&P.

**Fixed this round:**

- **Pagebreak span (fix 5)** — was `<span epub:type="pagebreak" class="pagebreak"
  title="N" id="pgN">N</span>` with `#888` CSS: no matching ARIA role, 3.54:1
  contrast fail, and the number spoken twice (text + `title`). Now an empty span
  with `role="doc-pagebreak"` and `aria-label="N"`; the page-list label comes
  from `aria-label` (verified `get_pages` reads it). Dead `.pagebreak` CSS
  removed. Clears `epub-type-has-matching-role` and `color-contrast`.
- **Nav not first in reading order** — the nav was linear and first, so Kobo
  (which ignores `hidden` on `<nav>`) opened the book on the page-list. Spine
  now `('nav', 'no')`, matching the cover.
- **META under-declares** — added `tableOfContents`, `pageBreakMarkers`,
  `pageNavigation` (markers and the page-list that navigates them are
  deliberately two separate features).
- **pageBreakSource (fix 7)** — required by Ace once a page-list ships, and
  good provenance. Composed from `meta.xml` title/publisher/date + the
  archive.org access URL, e.g. "Pride and prejudice. London : George Allen.
  1894. http://www.archive.org/details/prideprejudice00aust".
- **Cover in text-only builds** — decoupled from `--images`. The cover is the
  book's identity, not a content photo, so it now emits whenever there is an
  image stack and a non-cloth cover page. Verified on a de-clothed Huck:
  `cover.jpeg` + `cover.xhtml` + `properties="cover-image"` + `epub:type="cover"`
  landmark, with no `--images`.

**Still open — the running-head cluster (fixes 1–3), the real work:**
DONE this round — see the work log entry "Running-head furniture pass".
Residuals: P&P still misses `CHAPTER I`/`CHAPTER IV` (OCR mangling on those
openings, not furniture-related) and carries two OCR-noise entries
(`Chapter 3TJ?VJ`, `CHAPTER XL` twice — the mangled XI); Book of Love carries
two title-page/colophon entries (`BOOK`, `BOOK DESIGN BY CAROLINE CUNNINGHAM`).

Tests unchanged (7 pre-existing `FileNotFoundError` failures, 43 pass) plus
81 new tests (`tests/test_structure.py`, `tests/test_hocr_to_epub_furniture.py`).


## Round 3 — running-head furniture pass + package xml:lang + notice date

- [x] STRUCT/TOC — **Running-head furniture pass** in `bin/hocr-to-epub`
  (`_collect_running_heads` / `_decide_furniture`, plus
  `hocr/structure.py` helpers). Running heads repeat at the top of many
  pages, so font size alone cannot separate them from real section
  titles (The Book of Love sets its section titles and its recto running
  heads at the same size and position). The pass:
  - collects every line in the top 12% of each page, strips a folio-like
    leading/trailing token (printed page number, tolerating OCR
    confusions like `3O` for `30`; roman numerals, grammar-checked so
    ordinary words like `vivid`/`civil` are not eaten) and normalizes
    the rest;
  - phrases recurring on >= 3 pages (or on 2 pages when both lines read
    like heads, i.e. mostly caps — recurring body text such as dialogue
    is safe) form a furniture family; mangled variants extending a
    family phrase by <= 2 tokens join it (`THE BOOK OF LOVE of`);
  - within a family, occurrences > 5 pages apart are separate runs, so a
    chapter heading that doubles as its chapter's running head keeps the
    first occurrence of every run (each chapter survives);
  - an occurrence is kept if set at body size or larger, or if it is the
    first heading-classifying occurrence of its run — except in
    folio-styled families (>= 2 occurrences carrying the page's own
    printed number at the line edge), whose lines are never kept.
  - `RUNNING_HEAD_RATIO` raised 0.8 -> 0.85 so the classification guard
    and the furniture boundary agree (P&P running heads sit at 0.71-0.88
    of body size, straddling the old 0.8 line).
- [x] TOC — **`THE BOOK OF X` vocabulary**: new `CHAPTER_THE_RE` matches
  the structural vocabulary behind a leading article, trusted only for
  all-caps or enlarged lines so ordinary sentences starting "The book"
  stay paragraphs. `is_toc_entry()` matches the same condition. ToC and
  landmark titles are cleaned (`PREFACE. xi` -> `PREFACE`, trailing
  lowercase-roman folios and stray punctuation stripped; `CHAPTER XL`
  keeps its numeral).
- [x] LANG — **`xml:lang` on the OPF `<package>`**: `LangEpubWriter`
  (ebooklib `EpubWriter` subclass) injects `xml:lang` on the package
  element when a language is known; omitted when none is, mirroring the
  page-level behavior. Clears Ace `epub-lang` on P&P and Book of Love.
- [x] FILEDATE — **generated date in the notice**: the front-matter
  notice now carries "This EPUB was generated on YYYY-MM-DD" so a patron
  or admin can tell which copy is current. Filename unchanged by
  decision (the caller owns naming); `dc:identifier` untouched.
- [x] Verification across all three fixtures: P&P drops 405 running-head
  lines, ToC 66 -> 60 entries with exactly one `PREFACE` and a cleaned
  `Dedication`; Book of Love drops 449 verso-head lines, ToC 0 of 11
  section names -> 102 entries covering all of them (each `THE BOOK OF
  X` line in this book is a genuine one-page interlude opening — the
  drop-cap body after each confirms it); Huck (which has no recurring
  top-band heads) is byte-identical to HEAD (45 ToC entries).
  Tests: `tests/test_structure.py` (74), `tests/test_hocr_to_epub_furniture.py`
  (7); the 7 pre-existing fixture-missing failures are unchanged.
  Known residuals: P&P still misses `CHAPTER I`/`CHAPTER IV` and carries
  the mangled `CHAPTER XL` + one OCR-noise entry (pre-existing OCR
  issues, not furniture); Book of Love carries the title-page `BOOK` and
  colophon `BOOK DESIGN BY CAROLINE CUNNINGHAM` entries.
