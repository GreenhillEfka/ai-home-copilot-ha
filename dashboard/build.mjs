/**
 * PilotStack Dashboard Build
 * Minimal esbuild bundle for TS card sources.
 *
 * Usage:
 *   node build.mjs              # full build (www + cards)
 *   node build.mjs --cards      # cards only
 */

import * as esbuild from 'esbuild';
import { existsSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');

// ── helpers ────────────────────────────────────────────────────────────────────

function ensureDir(filePath) {
  mkdirSync(dirname(filePath), { recursive: true });
}

// ── shared esbuild options ────────────────────────────────────────────────────

const commonOpts = {
  bundle: true,
  format: 'esm',
  platform: 'browser',
  target: 'es2020',
  minify: false,
  sourcemap: false,
};

// ── card bundle ───────────────────────────────────────────────────────────────
// Bundles dashboard/static/cards/index.ts → www/pilotstack-zone-cards.mjs

const wwwDir = join(ROOT, 'custom_components', 'copilot_ha', 'www');
ensureDir(join(wwwDir, '.gitkeep'));

const cardsOutfile = join(wwwDir, 'pilotstack-zone-cards.mjs');

await esbuild.build({
  ...commonOpts,
  entryPoints: [join(ROOT, 'dashboard', 'static', 'cards', 'index.ts')],
  outfile: cardsOutfile,
  banner: {
    js: '/* PilotStack Zone Cards Bundle | Do not edit – built from TS sources */',
  },
  external: [],
  logLevel: 'info',
});

console.log('Cards bundle →', cardsOutfile);

// ── done ──────────────────────────────────────────────────────────────────────
console.log('Build complete.');
