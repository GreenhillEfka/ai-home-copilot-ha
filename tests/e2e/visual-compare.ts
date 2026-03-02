/**
 * PilotSuite Styx - Visual Comparison Utility
 * Pixel-diff comparison for screenshot regression testing
 * 
 * Features:
 * - Compare screenshots with baseline
 * - Calculate pixel difference percentage
 * - Generate diff images
 * - Configurable tolerance thresholds
 */

import { readFileSync, readdirSync, writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';

// Configuration
const SCREENSHOTS_DIR = join(process.cwd(), 'tests', 'e2e', 'screenshots');
const BASELINE_DIR = join(SCREENSHOTS_DIR, 'baseline');
const CURRENT_DIR = join(SCREENSHOTS_DIR, 'current');
const DIFF_DIR = join(SCREENSHOTS_DIR, 'diff');

// Default tolerance: 2% pixel difference is acceptable
const DEFAULT_TOLERANCE_PERCENT = 2.0;

/**
 * Ensure directories exist
 */
function ensureDirectories() {
  [SCREENSHOTS_DIR, BASELINE_DIR, CURRENT_DIR, DIFF_DIR].forEach(dir => {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  });
}

/**
 * Compare two images and return difference percentage
 * 
 * @param baselinePath - Path to baseline image
 * @param currentPath - Path to current image
 * @param tolerance - Acceptable difference percentage (default: 2%)
 * @returns Comparison result with diff percentage
 */
export async function compareImages(
  baselinePath: string,
  currentPath: string,
  tolerance: number = DEFAULT_TOLERANCE_PERCENT
): Promise<ComparisonResult> {
  ensureDirectories();

  return new Promise((resolve, reject) => {
    try {
      // Read baseline image
      const baselineData = readFileSync(baselinePath);
      const baseline = PNG.sync.read(baselineData);

      // Read current image
      const currentData = readFileSync(currentPath);
      const current = PNG.sync.read(currentData);

      // Check dimensions match
      if (baseline.width !== current.width || baseline.height !== current.height) {
        resolve({
          passed: false,
          diffPercentage: 100,
          reason: `Dimension mismatch: baseline (${baseline.width}x${baseline.height}) vs current (${current.width}x${current.height})`,
          diffImagePath: null
        });
        return;
      }

      // Create diff image
      const diff = new PNG({ width: baseline.width, height: baseline.height });

      // Compare pixels
      const numDiffPixels = pixelmatch(
        baseline.data,
        current.data,
        diff.data,
        baseline.width,
        baseline.height,
        { threshold: 0.1 }
      );

      // Calculate difference percentage
      const totalPixels = baseline.width * baseline.height;
      const diffPercentage = (numDiffPixels / totalPixels) * 100;

      // Determine if test passed
      const passed = diffPercentage <= tolerance;

      // Save diff image if there are differences
      let diffImagePath: string | null = null;
      if (numDiffPixels > 0) {
        const diffFileName = `diff_${Date.now()}.png`;
        diffImagePath = join(DIFF_DIR, diffFileName);
        writeFileSync(diffImagePath, PNG.sync.write(diff));
      }

      resolve({
        passed,
        diffPercentage,
        reason: passed ? 'Within tolerance' : `Exceeded tolerance (${diffPercentage.toFixed(2)}% > ${tolerance}%)`,
        diffImagePath
      });
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Compare screenshot with baseline
 * 
 * @param screenshotName - Name of screenshot (without extension)
 * @param tolerance - Acceptable difference percentage
 * @returns Comparison result
 */
export async function compareScreenshot(
  screenshotName: string,
  tolerance: number = DEFAULT_TOLERANCE_PERCENT
): Promise<ComparisonResult> {
  const baselinePath = join(BASELINE_DIR, `${screenshotName}.png`);
  const currentPath = join(CURRENT_DIR, `${screenshotName}.png`);

  if (!existsSync(baselinePath)) {
    return {
      passed: false,
      diffPercentage: 100,
      reason: `Baseline not found: ${baselinePath}`,
      diffImagePath: null
    };
  }

  if (!existsSync(currentPath)) {
    return {
      passed: false,
      diffPercentage: 100,
      reason: `Current screenshot not found: ${currentPath}`,
      diffImagePath: null
    };
  }

  return compareImages(baselinePath, currentPath, tolerance);
}

/**
 * Save screenshot as baseline
 * 
 * @param screenshotPath - Path to screenshot
 * @param baselineName - Name for baseline (without extension)
 */
export function saveAsBaseline(screenshotPath: string, baselineName: string): void {
  ensureDirectories();
  
  const baselinePath = join(BASELINE_DIR, `${baselineName}.png`);
  const data = readFileSync(screenshotPath);
  writeFileSync(baselinePath, data);
  
  console.log(`Baseline saved: ${baselinePath}`);
}

/**
 * Save screenshot as current
 * 
 * @param screenshotPath - Path to screenshot
 * @param currentName - Name for current (without extension)
 */
export function saveAsCurrent(screenshotPath: string, currentName: string): void {
  ensureDirectories();
  
  const currentPath = join(CURRENT_DIR, `${currentName}.png`);
  const data = readFileSync(screenshotPath);
  writeFileSync(currentPath, data);
  
  console.log(`Current screenshot saved: ${currentPath}`);
}

/**
 * Get all baseline screenshots
 * 
 * @returns Array of baseline names
 */
export function getBaselines(): string[] {
  ensureDirectories();
  
  const files = readdirSync(BASELINE_DIR)
    .filter(f => f.endsWith('.png'))
    .map(f => f.replace('.png', ''));
  
  return files;
}

/**
 * Comparison result interface
 */
export interface ComparisonResult {
  passed: boolean;
  diffPercentage: number;
  reason: string;
  diffImagePath: string | null;
}

/**
 * CLI interface for manual comparison
 */
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.log('Usage: node visual-compare.js <baseline> <current> [tolerance]');
    console.log('Example: node visual-compare.js baseline/dashboard-light.png current/dashboard-light.png 2');
    process.exit(1);
  }

  const [baseline, current, toleranceStr] = args;
  const tolerance = toleranceStr ? parseFloat(toleranceStr) : DEFAULT_TOLERANCE_PERCENT;

  compareImages(baseline, current, tolerance)
    .then(result => {
      console.log('Comparison Result:');
      console.log(`  Passed: ${result.passed}`);
      console.log(`  Difference: ${result.diffPercentage.toFixed(2)}%`);
      console.log(`  Reason: ${result.reason}`);
      if (result.diffImagePath) {
        console.log(`  Diff Image: ${result.diffImagePath}`);
      }
      process.exit(result.passed ? 0 : 1);
    })
    .catch(error => {
      console.error('Error:', error);
      process.exit(1);
    });
}

export default {
  compareImages,
  compareScreenshot,
  saveAsBaseline,
  saveAsCurrent,
  getBaselines,
  DEFAULT_TOLERANCE_PERCENT
};
