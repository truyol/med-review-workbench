# 技术设计：结构性心脏病术前规划素材评审工作台

状态：P2 设计已确认；本文按 2026-09-21 的已提交实现更新。早期 P2 设想与当前代码不一致时，以本文件的“已实现/未实现”标记及运行时 OpenAPI 为准。本文描述工程评审原型，不声明临床用途。

需求依据：[PRD](docs/product/03-prd.md) · [验收矩阵](docs/product/04-acceptance-matrix.md) · [运维手册](docs/engineering/ops.md) · [交付范围](docs/product/13-delivery-readiness.md)。

## 1. 目标、范围和架构

目标是把“项目 → 病例 → 素材 → 评审结论”做成可运行、可复现的闭环，解决术前讨论前素材分散、状态不清和结论难追溯的问题。图片浏览/筛选/比较、DICOM 安全元数据与预览、STL 查看/结构标记都是服务该闭环的能力，不提供诊断、治疗建议、自动分割或真实患者系统接入。

部署是模块化单体：Nginx 提供 React 静态页面并代理 `/api`，FastAPI 提供 `/api/v1`，SQLAlchemy 访问 SQLite，上传文件和派生预览放在本地持久化目录。Compose 中 API 使用 `/data` 持久卷；宿主机开发默认使用 `apps/api/var/`。两种运行方式的数据库和绝对文件路径不可混用。

```text
浏览器（React + TypeScript + Ant Design + Three.js）
    │ /api/v1（JSON、上传 multipart、预览/模型流）
    ▼
Nginx ──► FastAPI 路由 ──► WorkbenchService ──► WorkbenchRepository
                            │                    │
                            │                    └─ SQLite（SQLAlchemy + Alembic）
                            └─ 文件解析/持久目录（DICOM、图片、STL）
```

路由负责请求/响应和依赖注入；`services/workbench.py` 负责业务规则；`services/asset_processing.py` 负责文件判型、解析及预览；`repositories/workbench.py` 负责数据访问和提交回滚；`models/` 定义实际表结构；`domain/errors.py` 定义错误契约。前端按 `apps/web/src/features/` 与 `shared/` 分离。

## 2. 数据结构与状态

当前 Alembic 迁移为 `0001_baseline`、`0002_p4_review_workbench`、`0003_tags_annotations`；共五张业务表，不存在 `audit_events` 表。UUID 在应用层生成，时间由 UTC 时间字段维护；`case_code` 在同一项目内唯一。

| 表 | 已持久化的关键字段 | 约束/用途 |
|---|---|---|
| `projects` | `id`、`name`、`description`、创建/更新时间 | 项目容器；当前仅创建和列表 |
| `cases` | `id`、`project_id`、`case_code`、`title`、`clinical_context`、时间 | `unique(project_id, case_code)`；当前仅创建和列表 |
| `assets` | `id`、`case_id`、`kind`、`status`、`source_label`、`content_type`、`size_bytes`、`sha256`、`storage_path`、`preview_path`、`metadata_summary`、`ingest_warnings`、`tags`、`note`、时间 | `kind` 为 `dicom/stl/image`；文件路径与创建时的运行环境绑定；响应不含原始文件名 |
| `annotations` | `id`、`asset_id`、`label`、`data`、`note`、时间 | 结构标记的创建、列表、删除；STL 坐标存在模型空间 |
| `reviews` | `id`、`asset_id`、`decision`、`note`、`reviewer_name`、时间 | 追加式评审记录；评审看板返回最新一条 |

资产初始状态为 `pending`。提交 `accept / needs_changes / reject` 评审时，同一事务把资产状态写为 `accepted / needs_changes / rejected`，再追加评审；前端将状态映射为中文。这里是人工评审状态，不是算法对医学影像质量的判断。`assets.deleted_at` 与 `delete_reason` 字段已在模型中预留，但当前删除路径对**无评审**素材执行物理删除；有评审历史则返回 `DELETE_RESTRICTED`，不能把它介绍成完整软删除。

当前 `source_label` 是服务端生成的通用类别标签，尚无逐素材来源 URL、许可字段、明确的去标识化状态字段或真实登录身份字段。仓库自带样例的出处、许可、哈希及清理说明记录在 [样例登记](sample-data/README.md)，特别是 [心脏 STL 署名](sample-data/stl/ATTRIBUTION.md)；不要把文档登记误说成已实现的业务数据库溯源功能。

## 3. 已实现的 API 契约

统一前缀 `/api/v1`。普通成功响应为 `{ "data": ..., "meta": { "request_id": "..." } }`；错误响应为 `{ "error": { "code", "message", "next_action", "request_id" } }`。响应头也返回 `X-Request-ID`。列表使用 `limit`（1–100）和从零开始的 `offset`，**不是** `page/size`，当前响应不承诺 `meta.total`。

| 方法 | 路径（省略 `/api/v1`） | 当前行为 |
|---|---|---|
| GET | `/health`、`/health/ready` | 存活/就绪检查 |
| POST、GET | `/projects` | 创建/分页列表 |
| POST、GET | `/projects/{project_id}/cases` | 创建/分页列表；同项目病例编号冲突返回 409 |
| POST、GET | `/cases/{case_id}/assets` | 上传/分页列表；列表支持 `kind`、`status`、`tag` |
| PATCH | `/assets/{asset_id}` | 仅修改 `tags` 与 `note` |
| DELETE | `/assets/{asset_id}` | 未评审可删除；已有评审返回 409 |
| GET | `/assets/{asset_id}/preview`、`/assets/{asset_id}/model` | 分别返回 PNG 预览或 STL 文件流 |
| POST、GET | `/assets/{asset_id}/annotations` | 新增/列出结构标记 |
| DELETE | `/annotations/{annotation_id}` | 删除结构标记 |
| POST | `/assets/{asset_id}/reviews` | 提交评审，写入历史并更新素材状态 |
| GET | `/cases/{case_id}/review-board` | 病例及素材、每项最新评审 |

文件上传接口接收 `file`，类型由服务端根据扩展名、DICOM 魔数及解析结果判定；没有前端传入 `type/source/license_note` 的现行契约。当前没有项目/病例详情及更新接口、独立评审历史列表、DICOM 元数据单独接口、`reprocess` 接口，也没有素材 `display_name` 编辑接口。以 `/api/docs` 的运行时定义核对调用参数。

## 4. 文件处理与隐私边界

上传端点是同步函数，由 FastAPI 工作线程执行阻塞解析和数据库操作，避免占用事件循环。读入时按不超过 1 MiB 的块累计，`UploadFile.size` 可用时提前检查，并在内存读入超过 `APP_MAX_UPLOAD_MB`（默认 100 MiB）后返回 `UPLOAD_TOO_LARGE`。这不是“直接流式写入存储”，大文件仍会占用内存。

- 图片：允许 PNG/JPEG，Pillow 解码并生成 PNG 缩略图；损坏时返回 `IMAGE_PARSE_FAILED`（422）。
- STL：校验二进制长度/三角面数或 ASCII facet 结构，记录编码与三角面数；损坏时返回 `MODEL_PARSE_FAILED`（422）。目前不计算包围盒、不生成 3D 缩略图。前端通过模型流加载，并提供旋转、缩放、平移、复位与结构标记；加载失败应显示重试提示。
- DICOM：pydicom 解析，输出限定白名单（模态、检查部位、SOP 类 UID、行列数、帧数）；直接身份标签不进入响应。存在可解码像素时生成缩略图；缺少像素或压缩解码失败时保留元数据并记录 `ingest_warnings`，预览不可用，不冒充上传失败。白名单细节见 [DICOM 元数据白名单](docs/design/dicom-metadata-whitelist.md)。
- 存储：文件以 UUID 命名写入 `APP_STORAGE_ROOT`，缩略图写入 `APP_PREVIEW_ROOT`；数据库保存创建时的路径（容器配置为绝对路径，本地默认配置可为相对路径）。解析失败会清理已写文件及半成品预览。**仓储层新增/更新提交失败会回滚数据库，但已写入的上传文件可能遗留；删除路径先删除文件再直接提交数据库，也可能在提交失败时出现文件/DB 不一致**。这些是待收口风险，不能称为完整事务性文件落库。

日志禁止患者姓名、患者 ID、请求正文、原始文件名及完整 DICOM 标签。仅显示白名单不等同于临床级去标识化；样例 DICOM 清理脚本也不能证明像素不存在烧录文字，录屏前须人工检查。默认演示 DICOM 是无患者来源的合成 phantom；仓库内的心脏参考 STL 是独立模型，**不是** phantom 或任何病例的重建，不用于临床判断。

## 5. 错误、可观测性与测试

错误由 `ApiError`、请求校验处理器及全局异常处理器统一包装。以下是已进入代码的主要稳定错误码，不把 P2 设想中未实现的码列为已交付：

| HTTP | 错误码 | 场景 |
|---:|---|---|
| 400 | `VALIDATION_ERROR`、`UNSUPPORTED_ASSET_TYPE` | 参数错误或不支持的类型 |
| 404 | `PROJECT_NOT_FOUND`、`CASE_NOT_FOUND`、`ASSET_NOT_FOUND`、`ANNOTATION_NOT_FOUND`、`ASSET_FILE_MISSING` | 对象或落盘文件不存在 |
| 409 | `CASE_CODE_CONFLICT`、`DELETE_RESTRICTED`、`PREVIEW_NOT_AVAILABLE`、`MODEL_NOT_AVAILABLE` | 冲突或当前素材不提供所请求内容 |
| 413 | `UPLOAD_TOO_LARGE` | 上传超限 |
| 422 | `IMAGE_PARSE_FAILED`、`MODEL_PARSE_FAILED` | 图片或 STL 内容无法解析 |
| 500 | `PERSISTENCE_FAILED`、`INTERNAL_ERROR` | 持久化或未预期错误 |

`AccessLogMiddleware` 在异常路径也记录完成事件，包含状态、耗时及 request_id；错误日志不返回堆栈给客户端。`PERSISTENCE_FAILED` 只覆盖走仓储 `_commit()` 的写路径，**不覆盖当前直接提交的删除路径**。存活和就绪检查用于容器健康探测与排障。配置通过 `.env.example` 中的 `APP_*` 环境变量提供；Docker Compose 与备份/恢复步骤见 [运维手册](docs/engineering/ops.md)。

验证分层为 API 单元/集成测试、Alembic 升降级冒烟、前端静态检查/组件测试/生产构建、隔离 Docker 栈真实后端 Playwright、日志隐私扫描及依赖审计。日常运行 `scripts/check.ps1`，交付前运行 `scripts/check-full.ps1`。门禁栈与演示栈必须隔离，具体证据与历史轮次见 [P8 测试报告](docs/product/12-p8-test-report.md)；自动化通过不替代五分钟人工录屏。

## 6. 主要技术取舍和未完成项

| 决策 | 取舍与现状 |
|---|---|
| 模块化单体而非微服务 | 当前规模优先完整闭环；无需 Redis/Celery/Kubernetes |
| SQLite + SQLAlchemy + Alembic | 可复现的本地演示；PostgreSQL 仅有切换说明，未完成在线迁移与生产负载验证 |
| 后端解析与安全预览 | 避免引入完整 PACS/阅片器；只展示技术评审需要的白名单字段与缩略图 |
| 3D 使用 Three.js/STLLoader | 满足题目至少三项交互；不提供测量、自动分割或临床定位 |
| 文件与数据库分别持久化 | 简化原型，但无法提供跨文件系统与 DB 的原子事务，需进一步补偿清理/审计 |
| 评审追加式历史 | 最新结论更新素材状态，已有评审阻止删除；没有完整业务审计事件表 |

仍未实现或未验证：真实鉴权/权限控制、`audit_events` 持久化、`reprocess`、完整软删除、逐素材来源/许可/去标识化状态的业务字段、独立方案对象及方案级评审、图片/模型医学配准、PostgreSQL 生产验证及临床合规认证。当前项目以“病例下素材评审”覆盖题目的主要演示路径，不能把素材评审等同于完整方案管理。P2 原计划的若干表字段、端点和错误码已在本版更正为实际代码口径；若以后实现，应连同迁移、测试、OpenAPI 与本设计一起更新，不可仅修改文案。

## 7. 需求与证据追溯

| 需求 | 技术落点 | 当前证据/边界 |
|---|---|---|
| FR-001～004 项目/病例/素材 | 五张表中的前三张、`workbench` 路由/服务/仓储 | 创建/列表/上传/卡片与标签备注；项目/病例更新未做 |
| FR-005 DICOM | `asset_processing.py`、元数据白名单 | 元数据与可用时的缩略图；不是完整阅片 |
| FR-006 3D | STL 模型流、`StlViewer.tsx`、`annotations` | 四项视图操作与结构标记；手势体验仍需人工验收 |
| FR-007～009 评审/筛选/比较 | `reviews`、素材列表筛选、前端比较视图 | 评审持久化；比较是前端交互，不另设比较 API |
| FR-010～011 异常/隐私 | `domain/errors.py`、中间件、隔离测试 | 稳定错误码与 request_id；真实权限和临床脱敏未做 |

项目阶段和是否已收口以 [PROGRESS.md](PROGRESS.md) 为准；面试交付最终清单见 [DELIVERY_CHECKLIST.md](DELIVERY_CHECKLIST.md)。
