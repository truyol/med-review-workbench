import { expect, test, type Page } from "@playwright/test";

const project = { id: "project-1", name: "Demo Project", description: "演示" };
const demoCase = { id: "case-1", project_id: "project-1", case_code: "DEMO-001", title: "素材评审" };
const imageAsset = { id: "asset-1", case_id: "case-1", kind: "image", status: "pending", source_label: "IMAGE review asset", content_type: "image/png", size_bytes: 1024, sha256: "a".repeat(64), preview_available: true, metadata_summary: { format: "PNG", width: 16, height: 16 }, ingest_warnings: [] };

const previewPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

async function mockHappyPath(page: Page) {
  let uploaded = false;
  await page.route("**/api/v1/projects?limit=100", (route) => route.fulfill({ json: { data: [project], meta: { request_id: "e2e-projects" } } }));
  await page.route("**/api/v1/projects/project-1/cases?limit=100", (route) => route.fulfill({ json: { data: [demoCase], meta: { request_id: "e2e-cases" } } }));
  await page.route("**/api/v1/cases/case-1/assets", async (route) => {
    if (route.request().method() === "POST") { uploaded = true; await route.fulfill({ status: 201, json: { data: imageAsset, meta: { request_id: "e2e-upload" } } }); return; }
    await route.fulfill({ json: { data: uploaded ? [imageAsset] : [], meta: { request_id: "e2e-assets" } } });
  });
  await page.route("**/api/v1/cases/case-1/review-board", (route) => route.fulfill({ json: { data: { case: demoCase, assets: uploaded ? [{ asset: imageAsset, latest_review: null }] : [] }, meta: { request_id: "e2e-board" } } }));
  await page.route("**/api/v1/assets/asset-1/reviews", (route) => route.fulfill({ status: 201, json: { data: { id: "review-1", asset_id: "asset-1", decision: "accept", reviewer_name: "e2e", note: null }, meta: { request_id: "e2e-review" } } }));
  // Preview must resolve so the image renders instead of the fallback alert.
  await page.route("**/api/v1/assets/asset-1/preview", (route) => route.fulfill({ status: 200, contentType: "image/png", body: previewPng }));
}

test("main review flow reaches upload and review board", async ({ page }) => {
  await mockHappyPath(page);
  await page.goto("/projects");
  await expect(page.getByRole("heading", { name: "项目工作台" })).toBeVisible();
  await page.getByText("Demo Project").click();
  await expect(page.getByText("DEMO-001")).toBeVisible();
  await expect(page.getByText("素材评审", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "进入评审" }).click();
  await expect(page.getByText("还没有素材，请上传 DICOM、图片或 STL")).toBeVisible();
  await page.locator("input[type=file]").setInputFiles({ name: "demo.png", mimeType: "image/png", buffer: Buffer.from("fake") });
  await expect(page.getByText("IMAGE review asset")).toBeVisible();
  await page.getByRole("button", { name: "查看" }).click();
  await expect(page.getByText("白名单元数据", { exact: true })).toBeVisible();
});

test("API failure shows a recoverable error", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.abort());
  await page.goto("/projects");
  await expect(page.getByText("页面加载失败")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("请检查 API 服务后重试")).toBeVisible({ timeout: 15_000 });
});
