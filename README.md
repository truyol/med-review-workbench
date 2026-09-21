# Med Review Workbench

结构性心脏病术前规划素材评审工作台。

## 当前状态

P8 测试与证据收口已完成：快速门禁和 Docker 真实后端完整门禁均通过，验收记录见 `docs/product/12-p8-test-report.md`。

- 项目根目录：克隆后的仓库根目录
- 当前阶段：P8 测试已收口，准备进入 P9 文档一致性整理
- 产品定位：结构性心脏病术前规划素材评审工作台
- 业务代码：P4 后端闭环与 P5 前端主流程已完成
- 原则：先从用户问题定义范围，再做技术设计和实现

## 项目阶段

`P0 环境准备 → P1 产品设计 → P2 技术设计 → P3 脚手架 → P4 后端 → P5 前端 → P6 异常/边界 → P7 运维化 → P8 测试 → P9 文档 → P10 交付验收`

阶段定义和退出门禁见 [项目生命周期](docs/PROJECT_LIFECYCLE.md)。阶段按顺序推进；允许提前记录后续设计想法，但不得把后续阶段标记为已完成。

## 产品定位

面向术前规划工程师和影像技术评审员，在结构性心脏病术前讨论前，把同一病例的 CT/DICOM、图片和 3D 解剖模型汇总、验证并留下可追溯评审结论。

本产品不做临床诊断，不替代 PACS，不提供自动分割、治疗建议或真实患者系统接入。

## 产品思维门禁

每个功能进入 MVP 前必须回答：

1. 解决谁的什么痛点。
2. 做什么，不做什么。
3. 是否属于主流程闭环。
4. 如何通过一个用户流程验证。

## 文档入口

- [产品简介](docs/product/00-product-brief.md)
- [定位决策](docs/product/01-positioning-options.md)
- [用户流程与范围](docs/product/02-user-flow-and-scope.md)
- [PRD](docs/PRD.md)
- [PRD 详细版](docs/product/03-prd.md)
- [验收矩阵](docs/product/04-acceptance-matrix.md)
- [问题收口](docs/product/05-open-questions.md)
- [五分钟演示脚本](docs/product/06-demo-script.md)
- [AI 使用与医疗决策边界](docs/product/07-ai-product-boundary.md)
- [技术设计（P2 权威）](TECH_DESIGN.md)
- [技术架构（P2 输入草案）](docs/design/architecture.md)
- [DICOM 元数据白名单](docs/design/dicom-metadata-whitelist.md)
- [开发规范](docs/engineering/development.md)
- [隐私与安全](docs/engineering/privacy-and-security.md)
- [真实医疗软件场景能力差距](docs/engineering/real-world-readiness.md)
- [AI 使用记录](docs/engineering/ai-usage.md)
- [项目进度](PROGRESS.md)
- [P4 后端收口验收清单](docs/product/08-p4-backend-acceptance.md)
- [P5 前端验收清单](docs/product/09-p5-frontend-acceptance.md)
- [P6 异常与边界验收](docs/product/10-p6-boundary-acceptance.md)
- [P7 运维手册](docs/engineering/ops.md)
- [P7 运维化验收清单](docs/product/11-p7-operations-acceptance.md)
- [P8 测试与证据报告](docs/product/12-p8-test-report.md)
- [项目生命周期](docs/PROJECT_LIFECYCLE.md)

## 计划技术栈

- Web：React、TypeScript、Vite、Ant Design
- 3D：Three.js、React Three Fiber、STLLoader
- API：FastAPI、Pydantic、SQLAlchemy、Alembic
- DICOM：pydicom、NumPy、Pillow
- 数据：SQLite；生产演进目标为 PostgreSQL
- 测试：pytest、Vitest、Playwright
- 部署：Docker Compose、Nginx（部署阶段引入）

## 本地环境

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\verify-env.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

提交/交付前的 P8 完整门禁会启动 Docker 环境，并执行覆盖率、真实后端 E2E、隐私日志扫描和依赖审计：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-full.ps1
```

准备本地演示数据（仅使用仓库内合成 PNG、清理 DICOM 和 STL）：

```powershell
cd apps/api
.\.venv\Scripts\python.exe ..\..\scripts\seed-demo.py
```

容器部署使用独立的 `/data/medreview.db`。Compose 启动后需要演示数据时执行：

```powershell
docker compose -f .\deploy\docker-compose.yml exec -T api `
  python -m app.ops.seed_demo --sample-root /sample-data
```

前端主流程 E2E：

```powershell
cd apps/web
npm.cmd run e2e
```

首次运行需要本机安装 Playwright Chromium：`npx playwright install chromium`。

如需重新生成本地 DICOM 清理副本：

```powershell
.\apps\api\.venv\Scripts\python.exe .\scripts\prepare-dicom-samples.py
```

`.env.example` 中的 `APP_ALLOWED_ORIGINS` 是 JSON 数组；复制为 `.env` 后可直接被 `pydantic-settings` 解析。

## 样例数据获取与准备

仓库只提交两张明确为非临床的合成 PNG。DICOM 原文件和题目提供的 STL 因隐私、许可或体积原因不进入 Git；来源、哈希、使用条件和清理状态见 [样例数据登记](sample-data/README.md)。

1. 先完成依赖安装：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
   ```

2. 从已安装的 pydicom 测试数据复制 `CT_small.dcm`：

   ```powershell
   New-Item -ItemType Directory -Path .\sample-data\dicom -Force
   $ctSource = & .\apps\api\.venv\Scripts\python.exe -c "from pydicom.data import get_testdata_file; print(get_testdata_file('CT_small.dcm'))"
   Copy-Item -LiteralPath $ctSource -Destination .\sample-data\dicom\CT_small.dcm
   ```

3. 如需验证 96 帧压缩 XA 边界，从 [Rubo Sample DICOM files](https://www.rubomedical.com/dicom_files/) 手工下载 `DEMO 0002`，按其使用条件解压为：

   ```text
   sample-data/dicom/rubo_angiogram_0002/0002.DCM
   ```

   Rubo 样例只用于本地评价，不得随本仓库再分发。未准备该可选样例时，基础 DICOM 路径仍可使用 `CT_small.dcm` 验证。

4. 将面试题 `DEMO SET/stl/` 下的 STL 复制到：

   ```text
   sample-data/stl/
   ```

5. 原始 DICOM 含已填充的演示身份标签，不能直接用于应用或演示。准备完成后生成本地清理副本：

   ```powershell
   .\apps\api\.venv\Scripts\python.exe .\scripts\prepare-dicom-samples.py
   ```

   脚本会处理所有已存在的样例并跳过缺失的可选样例；如果一个原始 DICOM 都没有，则明确失败并提示先按本节准备数据。

安装完成后，VS Code 应选择解释器：

```text
apps/api/.venv/Scripts/python.exe
```

## 本地启动

后端：

```powershell
cd apps/api
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

前端：

```powershell
cd apps/web
npm.cmd run dev
```

访问：

- API 文档：`http://127.0.0.1:8000/api/docs`
- 后端健康检查：`http://127.0.0.1:8000/api/v1/health`
- 前端开发页：`http://127.0.0.1:5173`

## Docker 演示环境

推荐用 Docker 一键演示（Nginx + API + 持久卷）：

```powershell
docker compose -f .\deploy\docker-compose.yml up -d --build --wait
docker compose -f .\deploy\docker-compose.yml exec -T api python -m app.ops.seed_demo --sample-root /sample-data
```

访问 `http://localhost:8080`。

演示数据被污染或需要重来时：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-demo.ps1
```

> 注意：宿主机数据库（`apps/api/var/`）与容器卷（`/data`）**不可混用**，因为预览/模型记录的是创建时的绝对路径。二选一即可，详见 `docs/engineering/demo-and-test-data.md`。

## 测试门禁

```powershell
# 快速门禁：静态检查 + 单元/集成 + 前端构建
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1

# 完整门禁（P8）：隔离栈 + 覆盖率 + 真实 E2E + 隐私扫描 + 依赖审计
powershell -ExecutionPolicy Bypass -File .\scripts\check-full.ps1
```

完整门禁使用隔离的 Compose 项目与端口（`medreview-p8-gate` / `18080`），结束后连卷一起销毁，**不会污染演示数据**。

## 当前已知限制

- P3 只交付工程底座；项目/病例/素材/评审业务已在 P4/P5 实现，后续以 P6-P10 的边界、运维、测试和交付门禁为准。
- DICOM 清理脚本只处理 demo 的直接身份标签、私有标签和 UID，不等同于临床级去标识化，也不证明像素中没有烧录文字。
- Rubo DICOM 仅用于本地评价，不随仓库分发；可提交的图片样例是两张明确标注为非临床的合成 PNG。
- 测试存在来自 FastAPI/Starlette TestClient 依赖的弃用警告；不影响当前测试结果，待上游兼容版本稳定后升级。
- 当前前端已将 STL/Three.js 查看器动态拆包；首屏主包约 0.93MB，3D 查看器仅在进入 STL 详情时加载，仍保留 Vite 的大 chunk 提示作为后续性能优化项。
- P8 只证明已实现能力：结构标记、标签 CRUD/筛选和图片并排比较仍未完成；真实鉴权、持久化审计表、reprocess 和 PostgreSQL 生产验证仍在延期范围，详见 P8 报告。

## P4 backend API slice

The backend now contains the first P4 vertical slice for the main interview flow:

```text
Project -> Case -> Asset upload -> Review -> Case review board
```

Implemented endpoints:

- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `POST /api/v1/projects/{project_id}/cases`
- `GET /api/v1/projects/{project_id}/cases`
- `POST /api/v1/cases/{case_id}/assets`
- `GET /api/v1/cases/{case_id}/assets`
- `POST /api/v1/assets/{asset_id}/reviews`
- `GET /api/v1/cases/{case_id}/review-board`
- `GET /api/v1/assets/{asset_id}/preview`
- `GET /api/v1/assets/{asset_id}/model`
- `DELETE /api/v1/assets/{asset_id}`

The P4 backend slice is now consumed by the P5 frontend pages. Tags, advanced search, side-by-side comparison, annotations, reprocess, real authorization, audit persistence, and real AI remain outside the current interview scope.

P4 asset validation currently includes:

- DICOM allowlist metadata extraction with identity-tag withholding.
- Degraded DICOM handling when metadata is readable but preview is unavailable.
- STL binary/ASCII validation with triangle-count metadata.
- `kind` and `status` filters on `GET /api/v1/cases/{case_id}/assets`.
- PNG preview streaming and STL model streaming endpoints.
- Tests that assert upload responses and logs do not expose original filenames or DICOM identity values.
