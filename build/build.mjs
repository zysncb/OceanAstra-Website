#!/usr/bin/env node
/* ==========================================================================
   OceanAstra — static site generator
   Reads content/company.json + content/i18n/*.json and writes plain HTML
   into the repository root, which is what GitHub Pages serves directly.
   Zero dependencies. Run with:  node build/build.mjs
   ========================================================================== */

import { readFileSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import {
  LOCALES, PAGES, renderPage, render404, pageFile, pageUrl
} from './templates.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => JSON.parse(readFileSync(join(ROOT, p), 'utf8'));

const company = read('content/company.json');
const all = Object.fromEntries(LOCALES.map((l) => [l, read(`content/i18n/${l}.json`)]));

// '' for an apex/custom domain (the intended setup). Set to '/RepoName' only
// if the site is ever served from a GitHub project-pages subpath.
const base = company.basePath || '';
const buildYear = new Date().getFullYear();

/* --------------------------------------------------------------- output -- */

function write(relPath, contents) {
  const target = join(ROOT, relPath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, contents, 'utf8');
  return relPath;
}

// Remove only the directories this script owns, so a renamed or deleted page
// cannot survive as a stale file. Source directories are never touched.
for (const dir of ['zh', 'ar', ...PAGES.filter((p) => p !== 'home')]) {
  rmSync(join(ROOT, dir), { recursive: true, force: true });
}

const written = [];

for (const locale of LOCALES) {
  const t = all[locale];
  for (const page of PAGES) {
    const ctx = { t, all, locale, page, company, base, buildYear };
    written.push(write(pageFile(locale, page), renderPage(ctx)));
  }
}

// GitHub Pages serves /404.html for any unmatched path, in English.
written.push(write('404.html', render404({
  t: all.en, all, locale: 'en', page: 'home', company, base, buildYear
})));

/* ------------------------------------------------------------- sitemap -- */

const urls = LOCALES.flatMap((locale) =>
  PAGES.map((page) => ({ locale, page, loc: company.siteUrl + pageUrl('', locale, page) }))
);

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.map(({ page, loc }) => `  <url>
    <loc>${loc}</loc>
${LOCALES.map((l) => `    <xhtml:link rel="alternate" hreflang="${all[l].meta.htmlLang}" href="${company.siteUrl + pageUrl('', l, page)}"/>`).join('\n')}
    <changefreq>monthly</changefreq>
    <priority>${page === 'home' ? '1.0' : '0.7'}</priority>
  </url>`).join('\n')}
</urlset>
`;
written.push(write('sitemap.xml', sitemap));

written.push(write('robots.txt', `User-agent: *
Allow: /

Sitemap: ${company.siteUrl}/sitemap.xml
`));

// Tells GitHub Pages to serve the files as-is instead of running Jekyll.
written.push(write('.nojekyll', ''));

/* -------------------------------------------------------------- report -- */

console.log(`\n  OceanAstra — built ${written.length} files (${LOCALES.length} locales x ${PAGES.length} pages + 404, sitemap, robots)\n`);

if (company._placeholders) {
  console.log('  \x1b[33m! PLACEHOLDER DATA IS STILL IN content/company.json\x1b[0m');
  console.log('    These values are published on every page and must match the');
  console.log('    D-U-N-S record and trade licence exactly before going live:\n');
  for (const field of company._needsReview) console.log(`      - ${field}`);
  console.log('\n    Set "_placeholders": false once they are all confirmed.\n');
}
