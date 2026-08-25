# How this site actually behaves

Facts about the Design Canvas export that were established by measurement, not
by reading the code and assuming. Each one is recorded because getting it wrong
cost something — twice, a broken site in production.

Read the second half before diagnosing anything. Both incidents came from a
measurement that could not have shown the problem, not from a wrong hypothesis.

---

## The export

**It is client-rendered.** Without `tools/prerender.py` each page serves its
head, ~200 KB of JavaScript, and fifteen characters of visible text —
"OA Unpacking...". Googlebot executes JavaScript and gets there; GPTBot,
ClaudeBot and PerplexityBot generally do not.

**The bundle swaps the root element on load.** Its own comment says so: *"Parse
the template and swap the root element."* This is why `prerender.py` can insert
a static copy of the page alongside the bundle without the two fighting — the
copy is discarded the moment JavaScript runs, so there is no duplication and no
hydration mismatch to reconcile.

**It has no responsive CSS.** Four media queries exist across the whole site,
all `prefers-reduced-motion` and `print`. Layout is chosen in JavaScript from
`this.state.width < 900`. Anything that renders the page and discards the bundle
freezes whatever viewport it rendered at, permanently, at every screen size.

**It is already trilingual.** The runtime carries a complete `DICT` for `zh` and
`ar`, switches right-to-left for Arabic on its own (`isAr` drives line height,
letter spacing and direction), and has a Chinese brand name — 越海星辰. The
header switcher was never decorative; as exported it set component state and
re-rendered.

**Setting state was not enough to keep a language.** State lives on one page.
Every internal link is a full page load, so the next page booted from its own
`defaultLang` and came back in English — the switch worked and lasted exactly
until the visitor clicked something. `tools/lang-urls.py` repoints the switcher
at the locale URL (`/about/` → `/zh/about/`), which is what makes the choice
survive a click, a reload and a shared link. Verified in a browser across all
eighteen pages, both directions, desktop and 375 px.

**Language resolves as** `this.state.lang || this.props.defaultLang || "en"`,
and props come from the schema in `data-props` on the `<x-dc>` script. Setting
that schema's `default` is the entire mechanism behind `/zh/` and `/ar/`.

**Internal links are relative** — `solutions/` at the root, `../about/` one level
down. They resolve correctly inside any locale directory, so localised copies
need no link rewriting.

**Navigation items are real anchors with hrefs**, but only after JavaScript
renders them. In the served HTML they do not exist at all, which is why
dropping the bundle also dropped every internal link on the site.

**The template is a JSON-encoded string** containing a full HTML document,
including a nested `</script>`. Re-encoding it must escape `</` as `<\/`, which
`json.dumps` does not do. Leaving it literal ends the enclosing `<script>`
element early and truncates the page.

**Mobile has no overflow.** At 375 px: `documentWidth` 375, zero overflowing
elements, no horizontal scroll.

---

## Measurements that cannot show what they appear to show

**Searching index.html for Chinese or Arabic characters always returns zero.**
The template is JSON-encoded and JSON escapes non-ASCII as `\uXXXX`. This is
what produced the conclusion that the language switcher was fake, and then the
removal of its listener. Decode the template first, or click the button in a
browser — which takes ten seconds and is conclusive.

**Headless Chrome at `--window-size=375` is not a phone.** No device emulation,
no device pixel ratio, no mobile user agent. It reported a horizontal overflow
that does not exist on a real mobile viewport. Use actual mobile emulation.

**Comparing prerender output against itself proves nothing.** The run that froze
the mobile layout across the entire site looked correct that way. Output has to
be compared against what the site rendered *before* the change, at several
widths — which is what `tools/compare-viewports.sh` does.

**Chrome's default headless viewport is 800x600.** For a site whose layout is
decided in JavaScript from the window width, the default is a decision. Set it
explicitly.

**Generated output is only as current as the base it was generated from.**
The localised `<title>` work was produced in a separate worktree branched
before the language-URL fix landed. Its twelve HTML files were correct about
titles and, being rebuilt from that older base, silently dropped `switchLang`
from every /zh/ and /ar/ page — reintroducing the exact bug the fix had just
removed. Reviewing them against the goal would have passed. Take the tool
change and re-run it on the current base; then check the output still carries
what the base carries, not only what the change was for.

**A dumped DOM carries runtime artefacts.** `blob:` script srcs are minted
against whatever origin rendered the page; baked into a file they point at a
build server that existed for ninety seconds. `prerender.py` refuses to write a
fragment containing one.
