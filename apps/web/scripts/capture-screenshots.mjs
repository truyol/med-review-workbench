// Capture documentation screenshots from a running demo stack.
//
// Usage (from apps/web):
//   node scripts/capture-screenshots.mjs
//   SCREENSHOT_BASE_URL=http://127.0.0.1:8080 node scripts/capture-screenshots.mjs
//
// Requires the demo stack to be running and seeded (scripts/reset-demo.ps1).

import { mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(scriptDir, "..", "..", "..");
const outputDir = join(repoRoot, "docs", "screenshots");
const baseUrl = process.env.SCREENSHOT_BASE_URL ?? "http://127.0.0.1:8080";

async function main() {
  await mkdir(outputDir, { recursive: true });
  const browser = await chromium.launch({ channel: "chrome" });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  const shot = async (name) => {
    await page.screenshot({ path: join(outputDir, name), fullPage: true });
    console.log(`captured ${name}`);
  };

  await page.goto(`${baseUrl}/projects`);
  await page.waitForSelector(".project-card");
  await shot("01-projects.png");

  await page.locator(".project-card").first().click();
  await page.waitForSelector(".case-card");
  await shot("02-cases.png");

  await page.getByRole("button", { name: "进入评审" }).first().click();
  await page.waitForSelector(".asset-card");
  await shot("03-review-board.png");

  const imageCard = page.locator(".asset-card", { hasText: "IMAGE review asset" });
  if (await imageCard.count()) {
    await imageCard.first().getByRole("button", { name: "查看" }).click();
    await page.waitForSelector(".asset-preview");
    await shot("04-image-preview.png");
    await page.goBack();
    await page.waitForSelector(".asset-card");
  }

  const stlCard = page.locator(".asset-card", { hasText: "STL review asset" });
  if (await stlCard.count()) {
    await stlCard.first().getByRole("button", { name: "查看" }).click();
    await page.waitForSelector(".stl-viewer canvas");
    await page.waitForTimeout(2500); // allow the model to load and frame
    await shot("05-stl-viewer.png");
  }

  await browser.close();
  console.log(`screenshots written to ${outputDir}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
