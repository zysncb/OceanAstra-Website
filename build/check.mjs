#!/usr/bin/env node
/* ==========================================================================
   OceanAstra — post-build checks
   A broken link or a missing asset on a company site is exactly the kind of
   detail that undermines a manual review, so verify every internal href
   resolves to a file that actually exists.  Run:  node build/check.mjs
   ========================================================================== */

import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SKIP = new Set(['.git', '.claude', 'node_modules', 'build', 'content', 'assets']);

function htmlFiles(dir = ROOT, found = []) {
  for (const entry of readdirSync(dir)) {
    if (SKIP.has(entry)) continue;
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) htmlFiles(full, found);
    else if (entry.endsWith('.html')) found.push(full);
  }
  return found;
}

/** Map a site-absolute URL path to the file that would serve it. */
function resolveTarget(urlPath) {
  const clean = urlPath.split('#')[0].split('?')[0];
  if (clean === '' || clean === '/') return join(ROOT, 'index.html');
  const local = join(ROOT, clean);
  if (existsSync(local) && statSync(local).isFile()) return local;
  const asIndex = join(local, 'index.html');
  if (existsSync(asIndex)) return asIndex;
  return null;
}

const problems = [];
const files = htmlFiles();

for (const file of files) {
  const html = readFileSync(file, 'utf8');
  const rel = file.slice(ROOT.length + 1);

  // Internal links and asset references only — external, mailto and tel are
  // out of scope for a filesystem check.
  const refs = [...html.matchAll(/(?:href|src)="(\/[^"]*)"/g)].map((m) => m[1]);
  for (const ref of new Set(refs)) {
    if (!resolveTarget(ref)) problems.push(`${rel}  ->  ${ref}  (no such file)`);
  }

  // Every in-page anchor must have a matching id.
  const anchors = [...html.matchAll(/href="[^"]*#([^"]+)"/g)].map((m) => m[1]);
  for (const id of new Set(anchors)) {
    const targetRef = [...html.matchAll(new RegExp(`href="([^"]*)#${id}"`, 'g'))][0][1];
    const targetFile = targetRef ? resolveTarget(targetRef) : file;
    const target = targetFile || file;
    if (!existsSync(target)) continue;
    if (!readFileSync(target, 'utf8').includes(`id="${id}"`)) {
      problems.push(`${rel}  ->  #${id}  (no element with that id in ${target.slice(ROOT.length + 1)})`);
    }
  }
}

if (problems.length) {
  console.log(`\n  \x1b[31m${problems.length} broken reference(s):\x1b[0m\n`);
  for (const p of problems) console.log(`    ${p}`);
  console.log('');
  process.exit(1);
}

console.log(`\n  \x1b[32mOK\x1b[0m — checked ${files.length} HTML files, every internal link and anchor resolves.\n`);
