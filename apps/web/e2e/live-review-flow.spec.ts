import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";

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

test("real backend persists asset tags and note", async ({ page, request }) => {
  const suffix = Date.now().toString();
  const project = await (await request.post("/api/v1/projects", { data: { name: `P9 Tags ${suffix}` } })).json();
  const created = await (
    await request.post(`/api/v1/projects/${project.data.id}/cases`, {
      data: { case_code: `TAG-${suffix}`, title: "Tag persistence" },
    })
  ).json();
  const caseId = created.data.id;
  const uploaded = await (
    await request.post(`/api/v1/cases/${caseId}/assets`, {
      multipart: { file: { name: "tag.png", mimeType: "image/png", buffer: png } },
    })
  ).json();
  const assetId = uploaded.data.id;

  await page.goto(`/assets/${assetId}?caseId=${caseId}`);
  await page.getByLabel("标签").click();
  await page.getByLabel("标签").fill("瓣膜");
  await page.keyboard.press("Enter");
  await page.getByLabel("备注").fill("E2E 标签与备注验证");
  await page.getByRole("button", { name: "保存标签与备注" }).click();
  await expect(page.getByText("标签与备注已保存")).toBeVisible();

  const assets = await (await request.get(`/api/v1/cases/${caseId}/assets`)).json();
  expect(assets.data[0].tags).toContain("瓣膜");
  expect(assets.data[0].note).toBe("E2E 标签与备注验证");
});

test("real backend compares two distinct image previews", async ({ page, request }) => {
  const projects = await (await request.get("/api/v1/projects?limit=100")).json();
  const demo = projects.data.find((item: { name: string }) => item.name.includes("SHD"));
  expect(demo).toBeTruthy();
  const cases = await (await request.get(`/api/v1/projects/${demo.id}/cases?limit=100`)).json();
  const caseId = cases.data[0].id;
  const secondImage = readFileSync(
    new URL("../../../sample-data/image/synthetic-cardiac-ct-annotated.png", import.meta.url),
  );
  const upload = await request.post(`/api/v1/cases/${caseId}/assets`, {
    multipart: {
      file: { name: "synthetic-compare.png", mimeType: "image/png", buffer: secondImage },
    },
  });
  expect(upload.ok()).toBeTruthy();

  await page.goto(`/cases/${caseId}`);
  await page.getByRole("button", { name: "并排比较" }).click();
  const dialog = page.getByRole("dialog", { name: "图片并排比较" });
  await expect(dialog).toBeVisible();
  await dialog.locator(".ant-select").nth(0).click();
  await page.locator(".ant-select-dropdown:visible .ant-select-item-option").first().click();
  await dialog.locator(".ant-select").nth(1).click();
  await expect(page.locator(".ant-select-dropdown:visible .ant-select-item-option")).toHaveCount(1);
  await page.locator(".ant-select-dropdown:visible .ant-select-item-option").first().click();

  const left = dialog.getByRole("img", { name: "左侧素材" });
  const right = dialog.getByRole("img", { name: "右侧素材" });
  await expect(left).toBeVisible();
  await expect(right).toBeVisible();
  await expect.poll(() => left.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  await expect.poll(() => right.evaluate((image: HTMLImageElement) => image.naturalWidth)).toBeGreaterThan(0);
  expect(await left.getAttribute("src")).not.toBe(await right.getAttribute("src"));
});

test("real backend persists a structure marker on the seeded STL asset", async ({ page, request }) => {
  const projects = await (await request.get("/api/v1/projects?limit=100")).json();
  const demo = projects.data.find((item: { name: string }) => item.name.includes("SHD"));
  expect(demo).toBeTruthy();
  const cases = await (await request.get(`/api/v1/projects/${demo.id}/cases?limit=100`)).json();
  const caseId = cases.data[0].id;
  const board = await (await request.get(`/api/v1/cases/${caseId}/review-board`)).json();
  const stl = board.data.assets.find((item: { asset: { kind: string } }) => item.asset.kind === "stl").asset;

  await page.goto(`/assets/${stl.id}?caseId=${caseId}`);
  await expect(page.getByText("结构标记", { exact: true })).toBeVisible();
  await page.waitForSelector(".stl-viewer canvas");
  // Let the STL load and the camera auto-fit before raycasting.
  await page.waitForTimeout(2500);

  // The aorta is a tubular mesh, so some rays pass through the lumen. Sweep a
  // grid of points until one lands on the surface and opens the marker dialog.
  const canvas = page.locator(".stl-viewer canvas");
  const box = await canvas.boundingBox();
  expect(box).toBeTruthy();
  const fractions = [0.5, 0.4, 0.6, 0.3, 0.7, 0.2, 0.8];
  let dialogOpen = false;
  for (const fx of fractions) {
    for (const fy of fractions) {
      await canvas.click({ position: { x: box!.width * fx, y: box!.height * fy } });
      dialogOpen = await page
        .getByLabel("结构名称")
        .isVisible()
        .catch(() => false);
      if (dialogOpen) {
        break;
      }
    }
    if (dialogOpen) {
      break;
    }
  }
  expect(dialogOpen, "clicking the model should open the marker dialog").toBe(true);

  await page.getByLabel("结构名称").fill("主动脉瓣环");
  await page.locator(".ant-modal-footer .ant-btn-primary").click();
  await expect(page.getByText("主动脉瓣环")).toBeVisible();

  const annotations = await (await request.get(`/api/v1/assets/${stl.id}/annotations`)).json();
  expect(annotations.data.some((item: { label: string }) => item.label === "主动脉瓣环")).toBe(true);
});
