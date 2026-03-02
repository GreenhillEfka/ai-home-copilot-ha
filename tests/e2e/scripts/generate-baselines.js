#!/usr/bin/env node

/**
 * Generate Baseline Screenshots Script
 * 
 * This script helps generate baseline screenshots for visual regression testing.
 * Run this after making intentional UI changes to update baselines.
 */

const { execSync } = require('child_process');
const { existsSync, mkdirSync, rmSync } = require('fs');
const { join } = require('path');

const SCREENSHOTS_DIR = join(process.cwd(), 'screenshots');
const BASELINE_DIR = join(SCREENSHOTS_DIR, 'baseline');
const CURRENT_DIR = join(SCREENSHOTS_DIR, 'current');
const DIFF_DIR = join(SCREENSHOTS_DIR, 'diff');

console.log('📸 PilotSuite Styx - Baseline Screenshot Generator\n');

// Parse command line arguments
const args = process.argv.slice(2);
const forceRegenerate = args.includes('--force') || args.includes('-f');
const specificTest = args.find(a => !a.startsWith('-'));

// Ensure directories exist
[SCREENSHOTS_DIR, BASELINE_DIR, CURRENT_DIR, DIFF_DIR].forEach(dir => {
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
});

// Clear current and diff directories
if (existsSync(CURRENT_DIR)) {
  rmSync(CURRENT_DIR, { recursive: true, force: true });
  mkdirSync(CURRENT_DIR, { recursive: true });
}

if (existsSync(DIFF_DIR)) {
  rmSync(DIFF_DIR, { recursive: true, force: true });
  mkdirSync(DIFF_DIR, { recursive: true });
}

// Optionally clear baselines if --force flag
if (forceRegenerate && existsSync(BASELINE_DIR)) {
  console.log('⚠️  Clearing existing baselines (--force flag)\n');
  rmSync(BASELINE_DIR, { recursive: true, force: true });
  mkdirSync(BASELINE_DIR, { recursive: true });
}

console.log('Configuration:');
console.log(`  Baseline directory: ${BASELINE_DIR}`);
console.log(`  Current directory: ${CURRENT_DIR}`);
console.log(`  Diff directory: ${DIFF_DIR}`);
console.log(`  Force regenerate: ${forceRegenerate}`);
if (specificTest) {
  console.log(`  Specific test: ${specificTest}`);
}
console.log('');

// Run Playwright tests
const testCommand = specificTest
  ? `npx playwright test ${specificTest}`
  : 'npx playwright test dashboard_screenshots.spec.ts';

console.log(`Running: ${testCommand}\n`);

try {
  execSync(testCommand, {
    stdio: 'inherit',
    env: { ...process.env, CI: 'false' } // Disable retries for baseline generation
  });
  
  console.log('\n✅ Baseline generation complete!');
  console.log('\nNext steps:');
  console.log('  1. Review generated baselines in screenshots/baseline/');
  console.log('  2. Commit baselines to version control:');
  console.log('     git add tests/e2e/screenshots/baseline/');
  console.log('     git commit -m "chore: update visual regression baselines"');
  console.log('  3. Run tests to verify: npm test\n');
} catch (error) {
  console.error('\n❌ Baseline generation failed!');
  console.error('Check the error messages above and fix any issues.');
  process.exit(1);
}
