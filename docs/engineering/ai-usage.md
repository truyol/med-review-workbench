# AI 使用记录

> 当前交付证据以 `docs/product/12-p8-test-report.md` 第 10 节为准。以下按时间保留早期迭代记录，旧测试数量不是当前状态。

## 2026-09-21：公开仓库可复现性复核

- 任务：对照原始 Word 题目检查公开仓库能否在无私有素材的新环境直接演示。
- AI 建议：把本机 `DEMO SET` 中的 STL 与外部 DICOM 一起提交；人工拒绝，原因是许可、隐私和分发边界不清。
- 修改方案：只提交合成 PNG，seed 在缺少外部文件时确定性生成无患者来源的 DICOM phantom 与曲管 STL；优先使用另行准备的清理样例。
- 验证：单测验证新环境 seed 产生三类素材且重复执行不增量；隔离完整门禁通过，API 29、Playwright 6、隐私扫描 95 行零命中。
- 医疗边界：合成 phantom/曲管仅用于工程交互演示，不表示真实解剖、不用于诊断或治疗；评审结论仍由人工确认。

## 2026-09-21：演示验收整改（UI / 3D / 数据隔离）

- 任务：修复演示时发现的问题——前端观感、STL 视图空白、图片"打不开"、演示库被 P7/P8 测试数据污染。
- AI 建议：把根因分成三类分别处理：测试数据隔离、3D 查看器相机适配、UI/开发残留清理；不要靠手工删数据掩盖问题。
- 人工验证：实测 `/preview` 与 `/model` 均返回 200（图片其实正常，"打不开"实为 STL 视图空白）；查询容器卷确认脏数据来自 `live-review-flow` 每次新建的时间戳项目与手动验证数据。
- 修改/拒绝：拒绝只删脏数据不改根因；改为让 `check-full.ps1` 使用隔离 Compose 项目 `medreview-p8-gate` + 端口 18080 并在结束后 `down -v`，另加 `reset-demo.ps1`。拒绝保留顶栏 `P5 前端` 开发标签。STL 查看器改用 `geometry.center()` + drei `<Bounds fit clip observe>` 做模型居中与相机自适应。
- 验证方式：`check-full.ps1` 实测输出 `Full P8 gate passed.`（Playwright 4 passed），且运行后演示卷中仍只有 `Demo - SHD preoperative asset review` 一个项目；`reset-demo.ps1` 实测清空脏数据并重建种子。
- 医疗边界：仅工程素材评审能力，使用合成/清理样例；未接入真实 AI、真实患者数据，未生成诊断或治疗建议。

## 2026-09-21：P8 测试与证据收口

- 任务：用自动化和真实运行证据验证当前实现，并形成可追溯测试报告。
- AI 建议：增加真实后端 Playwright 闭环、可复用隐私日志扫描、依赖审计和一键完整门禁；同时报告覆盖率实际数值。
- 人工约束：不以 Mock E2E 冒充真实联调，不设置没有依据的覆盖率数字，不把结构标记、标签筛选、图片并排比较等未实现能力写成通过。
- 修改/拒绝：拒绝为了让 P8 报告“全绿”而篡改需求状态；FR-006/008/009 保留为部分通过。迁移检查改为临时数据库，避免测试工具破坏开发数据；Ant Design 弃用属性同步修正。
- 验证：修复 Mock E2E 的严格定位冲突并补齐可解码 PNG 预览响应后，完整门禁重新执行通过；API 25 tests/89%，Web 3 tests，Playwright 4 tests，运行日志 62 行零敏感命中，Python/Node 依赖无已知漏洞，最终输出 `Full P8 gate passed.`。
- 医疗与 AI 边界：只验证工程素材评审能力，使用合成或清理样例；没有接入真实 AI、真实患者数据，也没有生成诊断或治疗建议，评审结论继续由人工确认。

## 2026-09-21：P7 运维化

- 任务：建立可部署、可观测、可备份恢复的单机演示运行方式。
- AI 建议：使用 API/Web 多阶段镜像、Nginx 反代、Compose readiness 和持久卷，并把 request_id 排障写成可执行步骤。
- 人工约束：默认保留 SQLite，PostgreSQL 只提供驱动、配置方式和限制说明；拒绝为了展示技术栈提前加入 Kubernetes、Redis、Celery 或未经验证的高可用声明。
- 验证：Compose 配置静态解析、SQLite 备份恢复 round-trip 和统一工程检查；容器运行证据必须等 Docker engine 可访问后补齐。
- 医疗边界：运维能力不改变产品用途，不接入真实患者数据、真实 AI、诊断或治疗决策。
- 复核修正：发现宿主机 seed 无法填充容器卷后，将 seed 逻辑放入 API 包并提供容器内显式命令；同时把 `psycopg` 改为可选镜像依赖、关闭同源容器部署不需要的 CORS。拒绝在缺少容器运行证据时提前把 P7 标为完成。

## 2026-09-21：P6 异常边界收口

- 任务：验证上传、持久化和前端媒体加载失败时的工程恢复行为。
- AI 建议：把失败路径作为面试验收的一等公民，优先固定错误码、请求追踪、回滚和重试入口，而不是增加业务端点。
- 人工确认：人工检查了 `IMAGE_PARSE_FAILED`、`UPLOAD_TOO_LARGE`、`PERSISTENCE_FAILED` 及前端 fallback 的测试证据；没有接入真实 AI，也没有生成诊断或治疗建议。
- 最终结果：P6 只增强可见性、可记录性和可恢复性，素材评审结论仍必须由人工确认。

## 记录原则

每条重要记录包含：任务、AI 建议、人工验证、修改/拒绝、最终结果和证据。

## 2026-09-20：需求与定位分析

- 任务：将岗位要求、本地题目和素材转换为可交付产品方案。
- AI 建议：主选全栈题；产品暂定位为医学影像与 3D 素材技术验收工作台；先设产品门禁再编码。
- 人工验证：逐份核对 README/DOCX；盘点本地 STL、DICOM 和在线占位文件；将功能映射到岗位职责。
- 结果：用户提供产品方向后，定位收敛为“结构性心脏病术前规划素材评审工作台”。

## 2026-09-20：P1 产品设计收口

- 任务：根据用户提供的 `产品方向.txt` 完成 P1 产品设计文档。
- AI 建议：把 txt 中的“P0/P1 功能范围”转换为本项目的 Must/Should/Later，避免和全局 P0-P10 阶段混淆。
- 人工验证：核对本地样例数据路径、DICOM 帧数、STL 文件大小和 SHA256；用户强调以产品思维推进。
- 结果：更新 PRD、用户流程、验收矩阵、问题收口、演示脚本和样例数据记录。

## 2026-09-20：P2 技术设计

- 任务：根据 P1 产品定义和用户提供的两张 P2 建议图，形成技术设计文档。
- AI 建议：保持 FastAPI、React、R3F、pydicom、structlog 的轻量组合；Docker/Nginx 延后到 P7，但提前设计配置外置、健康检查、结构化日志和 `request_id`。
- 人工验证：对照 PRD、验收矩阵、DICOM 白名单、当前本地环境和已安装依赖检查设计范围。
- 修改/拒绝：拒绝引入 Cornerstone/OHIF、Celery、Redis、微服务和真实 AI SDK；理由是它们不服务当前素材评审闭环，会增加实现和合规风险。
- 结果：产出根目录 `TECH_DESIGN.md`，同步 README、PROGRESS、DICOM 白名单和架构输入文档；用户已确认 P2，可进入 P3。

## 2026-09-20：P2 复审整改

- 任务：根据用户提供的 P2 复审建议图，判断是否需要优化并整改。
- AI 建议：将压缩 DICOM 解码、服务端素材类型判定、软删除、唯一约束、统一错误模型、上传临时文件清理、reprocess、权限/审计边界补入 P2 设计。
- 人工验证：对照当前 `TECH_DESIGN.md`、`pyproject.toml`、`.env.example` 和 Git 状态核查缺口。
- 修改/拒绝：未引入 GDCM 作为 Windows MVP 强依赖；保留为未来可选项。未提前实现业务代码，只更新 P2 设计与依赖声明。
- 结果：更新 `TECH_DESIGN.md` 和 `apps/api/pyproject.toml`，并处理 Git `safe.directory` 环境问题。

## 2026-09-20：P3 脚手架

- 任务：进入 P3，搭建可启动、可检查的工程底座。
- AI 建议：按“三刀”完成后端健康检查、前端空壳、Alembic baseline 和统一检查入口；不提前写项目/病例/素材业务逻辑。
- 人工验证：执行 `scripts/check.ps1`，并实际启动 FastAPI 与 Vite 开发服务器检查可访问性。
- 修改/拒绝：没有实现 DICOM/3D/素材上传业务，避免 P3 范围膨胀。
- 结果：P3 门禁通过，准备进入 P4 后端。

## 2026-09-20：P3 退出前整改与面试边界复核

- 任务：修复 P3 配置、错误契约、CORS、前端弃用项和目录漂移，并重新核对面试题边界。
- AI 建议：把图片比较继续留在 Should；人工对照原始题目后拒绝该建议，因为题目明确要求图片浏览、筛选、比较、整理和结论沉淀，已改为 Must。
- 人工验证：复现 `.env.example` 的 origins 解析失败；检查未知路由原生 404；核对 CORS 中间件和 Ant Design v6 警告；扫描 DICOM 仅报告敏感标签是否存在而不输出值。
- 修改/拒绝：没有引入产品内 AI。使用 ImageGen 只生成两张无身份信息的非临床合成 PNG，作为面试题图片闭环的可提交测试素材；产品仍不依赖 AI API。
- 医疗边界：原始 DICOM 含已填充身份标签，因此禁止直接进入应用或演示；通过可复现脚本生成本地清理副本，同时明确该脚本不等同于临床级去标识化，仍需检查像素烧录文字。
- 结果：补齐 JSON origins、CORS、统一 404/500 信封、AntD v6 属性、`app/domain/errors.py`；新增图片 Must 验收、真实医疗场景能力差距文档和 AI 决策边界文档。
- 补充收口：异常请求现在也输出统一 `request.completed` 访问日志（含 500、耗时和 request_id）；根 README 增加不随 Git 分发的 DICOM/STL 获取与准备步骤，避免只在子文档登记而无法复现。

## 已修改或拒绝的建议

- 拒绝“一开始实现完整 DICOM 阅片器”：超出题目边界，改为安全元数据与单张预览。
- 拒绝“立即接入真实大模型”：不能直接证明核心价值，会增加密钥和可用性风险；改为记录研发 AI 使用，产品内 AI 在本次 MVP 中明确为 Out，未来必须重新验证价值和医疗边界后才能立项。
- 延后“立即安装 PostgreSQL、Nginx、Docker”：开发期 SQLite 足够；部署工具待产品门禁通过且 WSL2 条件就绪后再引入。

## 2026-09-21: P4 backend vertical slice

- Task: implement the first backend loop for project, case, asset upload, review, and review-board retrieval.
- AI suggestion: focus on the vertical review loop first and defer tags, advanced filters, comparison, annotation CRUD, preview streaming, and reprocess until the core loop has test evidence.
- Human/product constraint: the user explicitly requested strict interview scope control and product thinking. The implementation therefore avoids clinical diagnosis, real AI, real authentication, and broad endpoint expansion.
- Modification/rejection: the P2 design listed a larger API surface. This slice intentionally rejected implementing every endpoint immediately because that would dilute the primary user problem and make verification weaker.
- Final result: added SQLAlchemy models, Alembic migration, repository/service/route layers, asset ingestion, stable business errors, and P4 API tests.
- Evidence: `ruff check`, `mypy app tests`, `pytest -q`, `alembic upgrade head`, and `alembic downgrade base` passed for the backend.

## 2026-09-21: P4 asset validation hardening

- Task: continue P4 by improving file validation, DICOM privacy behavior, STL handling, and bounded asset filtering.
- AI suggestion: add trust-building evidence before adding more endpoints, because the interview requirement values safe file handling and medical boundary control more than broad CRUD surface.
- Human/product constraint: keep the primary review loop intact and avoid starting P5 UI or full viewer work early.
- Modification/rejection: rejected full tag/search/comparison implementation in this slice; implemented only `kind` and `status` filters because they directly support the review list.
- Final result: added DICOM allowlist/privacy tests, STL parser metadata and corrupt-STL error, asset filters, and upload log privacy assertions.
- Evidence: `scripts/check.ps1` passed; API pytest now covers 15 tests.

## 2026-09-21: P4 preview/model read endpoints

- Task: continue P4 by adding backend read endpoints for generated previews and STL models.
- AI suggestion: implement only the read endpoints needed by P5, and defer `reprocess` plus annotation CRUD to avoid expanding the backend beyond the current interview proof.
- Human/product constraint: stay centered on the case asset review loop and preserve privacy controls around original filenames.
- Final result: added `/assets/{asset_id}/preview`, `/assets/{asset_id}/model`, stable unavailable/missing-file errors, and tests for successful and unavailable paths.
- Evidence: `scripts/check.ps1` passed; API pytest now covers 17 tests.
## 2026-09-21 P4 收口整改：同步上传与 DICOM 白名单

- AI 参与：审阅上传路由的同步/异步边界，并对照 DICOM 白名单文档与运行时代码。
- 人工决策：将上传端点改为同步函数，避免在 `async` 事件处理器中直接执行同步解析、预览生成和磁盘 I/O；移除 `StudyDescription`、`SeriesDescription` 的响应输出，因为它们是自由文本。
- 验证方式：pytest 覆盖敏感描述字段不出现在 `metadata_summary`，并通过完整 `scripts/check.ps1`。
- 医疗边界：没有调用真实 AI、没有生成诊断或治疗建议；这里只做隐私最小化和工程并发边界修复。

## 2026-09-21 P5 前端主流程与性能优化

- AI 参与：根据 P5 门禁审阅页面路由、查询缓存、STL 加载和 E2E 验收范围。
- 人工决策：只实现项目→病例→素材→评审闭环；Three.js 改为懒加载；演示数据只读取仓库内合成/清理样例；标签全文检索、并排比较、标注 CRUD 和真实权限继续延期。
- 验证方式：前端 lint、Vitest、TypeScript build 通过；Playwright 主流程和 API 失败流程已使用本机 Chrome 通道执行通过（2 passed）。
- 医疗边界：界面只表达素材状态和工程评审结论，不输出诊断、治疗建议或患者身份信息。
