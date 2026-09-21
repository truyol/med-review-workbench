import { expect, test } from "@playwright/test";

test.skip(!process.env.PLAYWRIGHT_LIVE, "requires the Docker-backed P8 environment");

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("real backend supports project-to-review closed loop", async ({ page, request }) => {
  const suffix = Date.now().toString();
  const projectName = `P8 Live ${suffix}`;
  const caseCode = `P8-${suffix}`;

  await page.goto("/projects");
  await page.getByRole("button", { name: "新建项目" }).click();
  await page.getByLabel("项目名称").fill(projectName);
  await page.locator(".ant-modal-footer .ant-btn-primary").click();
  await expect(page.getByRole("heading", { name: projectName })).toBeVisible();

  await page.getByRole("button", { name: "新建病例" }).click();
  await page.getByLabel("病例编号").fill(caseCode);
  await page.getByLabel("病例标题").fill("P8 real backend review");
  await page.locator(".ant-modal-footer .ant-btn-primary").click();
  await expect(page.getByText("还没有素材，请上传 DICOM、图片或 STL")).toBeVisible();

  const caseId = new URL(page.url()).pathname.split("/").at(-1);
  expect(caseId).toBeTruthy();
  await page.locator("input[type=file]").setInputFiles({
    name: "p8-synthetic.png",
    mimeType: "image/png",
    buffer: png,
  });
  await expect(page.getByText("素材已上传并完成基础校验")).toBeVisible();
  await expect(page.getByText("IMAGE review asset")).toBeVisible();

  await page.getByRole("button", { name: "查看" }).click();
  await expect(page.getByText("白名单元数据", { exact: true })).toBeVisible();
  await page.getByLabel("结论").click();
  await page.getByText("通过", { exact: true }).click();
  await page.getByLabel("说明").fill("P8 automated engineering review evidence.");
  await page.getByRole("button", { name: "保存评审" }).click();
  await expect(page.getByText("评审已保存")).toBeVisible();

  const board = await request.get(`/api/v1/cases/${caseId}/review-board`);
  expect(board.ok()).toBeTruthy();
  const body = await board.json();
  expect(body.data.assets[0].asset.status).toBe("accepted");
  expect(body.data.assets[0].latest_review.decision).toBe("accept");
});

test("real backend unsupported upload exposes recoverable next action", async ({ page }) => {
  const projectsResponse = await page.request.get("/api/v1/projects?limit=100");
  const projects = await projectsResponse.json();
  const projectId = projects.data[0].id;
  const casesResponse = await page.request.get(`/api/v1/projects/${projectId}/cases?limit=100`);
  const cases = await casesResponse.json();
  const caseId = cases.data[0].id;

  await page.goto(`/cases/${caseId}`);
  await page.locator("input[type=file]").setInputFiles({
    name: "unsupported.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("not a supported review asset"),
  });
  await expect(page.getByText("Upload a supported, de-identified review asset.")).toBeVisible();
});
