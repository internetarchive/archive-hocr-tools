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

