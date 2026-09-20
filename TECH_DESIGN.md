# 技术设计（P2）：结构性心脏病术前规划素材评审工作台

状态：Approved（P2 已确认）
版本：1.0
更新时间：2026-09-20
权威 PRD：[`docs/product/03-prd.md`](docs/product/03-prd.md)
本文是题目要求的 `TECH_DESIGN.md`，覆盖模块划分、数据结构、关键接口、技术取舍与异常处理。

---

## 1. 设计目标与约束

- 交付一个**可运行的模块化单体**，优先打通「病例素材评审闭环」。
- **本地优先**：核心流程不依赖外部 API、API Key 或公网。
- **隐私优先**：日志、界面、Git 不出现患者身份信息与原始文件名。
- **可演进**：SQLite/本地存储通过接口抽象，保留切换 PostgreSQL/对象存储的能力。
- **后端可信**：文件类型、DICOM 解码能力、删除限制和权限边界由服务端判定，前端输入只作为提示。
- 不做：临床阅片、诊断、自动分割、模型训练、多人实时协同、微服务。

---

## 2. 系统上下文与架构

```text
Browser (React + TypeScript)
  ├─ 项目 / 病例 / 素材 / 评审 功能
  ├─ Three.js STL Viewer（旋转/缩放/平移/复位/结构标记）
  └─ API client（附带 X-Request-ID）
            │  REST /api/v1  (JSON + multipart)
            ▼
FastAPI (模块化单体)
  ├─ api/routes        协议转换、鉴权占位、参数校验
  ├─ services          业务规则（评审状态流转、校验）
  ├─ repositories      数据访问（SQLAlchemy）
  ├─ domain            实体、枚举、错误码
  ├─ media             pydicom 解析、缩略图、STL/图片校验
  ├─ storage           文件存储抽象（本地 → 对象存储）
  └─ observability     structlog、request_id、健康检查
            ├─ SQLite（开发）/ PostgreSQL（演进）
            └─ var/uploads（原始，只读）+ var/previews（派生）
```

### 分层规则

- `routes` 只做协议转换与调用 service，不写业务规则。
- 业务规则集中在 `services`，持久化集中在 `repositories`。
- `domain` 不依赖 Web/DB 框架，便于单测。
- 任何跨层依赖只允许向内：`routes → services → repositories → domain`。

---

## 3. 模块划分（代码结构）

```text
apps/api/app/
  main.py                 # 应用装配、中间件、异常处理器
  api/
    deps.py
    routes/
      health.py
      projects.py
      cases.py
      assets.py
      annotations.py
      reviews.py
  services/
    project_service.py
    case_service.py
    asset_service.py
    review_service.py
    media_service.py
  repositories/
    base.py
    project_repo.py
    case_repo.py
    asset_repo.py
    review_repo.py
  domain/
    enums.py              # AssetType / AssetStatus / ReviewStatus
    errors.py             # 稳定错误码
    models.py             # 内部实体
  media/
    dicom.py              # pydicom 解析 + 白名单 + 缩略图
    stl.py                # STL 头校验与统计
    image.py              # 图片校验与缩略图
  storage/
    base.py               # Storage 接口
    local.py              # 本地实现
  observability/
    logging.py            # structlog 配置
    request_id.py         # 中间件
  db/
    session.py
    base.py
  settings.py             # pydantic-settings

apps/web/src/
  app/                    # 路由、Provider、布局
  features/
    projects/
    cases/
    assets/
    reviews/
    viewer3d/
  shared/
    api/                  # fetch 封装 + request id
    ui/
    types/
```

---

## 4. 数据模型

### 4.1 实体关系

```text
Project 1 ── n Case 1 ── n Asset 1 ── n Annotation
                              └─ 1 ── n Review（追加式历史）
```

### 4.2 表设计

**projects**

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | |
| name | varchar(120) | not null | |
| description | text | | |
| status | enum | not null | `active` / `archived` |
| created_at | timestamptz | not null | UTC |
| updated_at | timestamptz | not null | UTC |

**cases**

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | |
| project_id | UUID | FK → projects, index | |
| case_code | varchar(64) | not null | 脱敏编号，如 `DEMO-TAVR-001`；同项目内唯一 |
| note | text | | |
| created_at / updated_at | timestamptz | not null | UTC |

约束：`unique(project_id, case_code)`，命中后返回 `CONFLICT`。

**assets**

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | 同时作为存储目录名与日志标识 |
| case_id | UUID | FK → cases, index | |
| type | enum | not null | `dicom` / `image` / `model` |
| display_name | varchar(160) | not null | 用户可见名，默认可编辑 |
| original_name | varchar(255) | | 仅受控保存，**不进入日志与默认响应** |
| format | varchar(32) | not null | 识别结果，如 `DICOM` / `STL` / `PNG` |
| source | varchar(255) | not null | 来源说明，缺失则校验失败 |
| source_url | varchar(512) | | |
| license_note | varchar(255) | | 许可/使用条件 |
| sha256 | char(64) | not null | 流式计算 |
| size_bytes | bigint | not null | |
| storage_key | varchar(255) | not null | 相对 `var/uploads` 的路径 |
| preview_key | varchar(255) | | 相对 `var/previews` |
| status | enum | not null | `pending` / `available` / `needs_supplement` / `unavailable` |
| load_state | enum | not null | `unknown` / `ok` / `failed` |
| tags | json | not null | 字符串数组 |
| note | text | | |
| metadata | json | | 仅 DICOM 白名单字段 / 模型统计 |
| error_code | varchar(48) | | 加载失败时的稳定错误码 |
| deleted_at | timestamptz | | 软删除时间；已评审资产默认禁止硬删除 |
| created_at / updated_at | timestamptz | not null | UTC |

索引：`(case_id)`、`(case_id, status)`、`(case_id, type)`、`(deleted_at)`。默认查询过滤 `deleted_at is null`。

**annotations**

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | |
| asset_id | UUID | FK → assets, index | |
| type | enum | not null | `point` / `label` |
| label | varchar(120) | | 结构名，如「主动脉瓣环」 |
| data | json | not null | 坐标 / 相机状态 |
| note | text | | |
| created_at | timestamptz | not null | UTC |

**reviews**（追加式，最新一条决定资产状态）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | |
| asset_id | UUID | FK → assets, index | |
| status | enum | not null | `pending` / `available` / `needs_supplement` / `unavailable` |
| conclusion_text | text | not null | |
| reviewer | varchar(80) | not null | 演示角色或评审人 |
| issue_summary | text | | |
| next_action | text | | |
| reviewed_at | timestamptz | not null | UTC |
| created_at | timestamptz | not null | UTC |

索引：`(asset_id, reviewed_at desc)`。

**audit_events**（P4 可选实现，P2 先定义边界）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | UUID | PK | |
| actor | varchar(80) | not null | 演示角色；MVP 无真实登录 |
| action | varchar(80) | not null | 如 `asset.uploaded` / `review.created` / `asset.deleted` |
| target_type | varchar(40) | not null | `project` / `case` / `asset` / `review` |
| target_id | UUID | not null | |
| request_id | UUID | not null | 与运行日志关联 |
| metadata | json | | 不含患者字段、请求正文、原始文件名 |
| created_at | timestamptz | not null | UTC |

### 4.3 状态机

```text
pending ──► available
pending ──► needs_supplement ──► available
pending ──► unavailable
needs_supplement ──► unavailable
unavailable ──► pending        # 重新上传/修复后
```

- 资产 `status` 由最新 `review.status` 派生；无评审时为 `pending`。
- 加载失败自动置 `load_state=failed` 并建议 `unavailable`，但最终状态仍由人确认（不做自动临床/质量判断）。

---

## 5. API 契约

统一前缀 `/api/v1`；ID 为 UUID；时间为 UTC ISO 8601。

### 5.1 约定

- 成功响应：`{ "data": ..., "meta": { "request_id": "..." } }`
- 分页参数：`?page=1&size=20`（`size` 上限 100），响应含 `meta.total`。
- 上传：`multipart/form-data`。
- 所有响应头返回 `X-Request-ID`。

### 5.2 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 存活检查，不访问依赖 |
| GET | `/health/ready` | 就绪检查：DB + 存储可写 |
| POST | `/projects` | 创建项目 |
| GET | `/projects` | 项目列表（分页） |
| GET | `/projects/{project_id}` | 项目详情 |
| PATCH | `/projects/{project_id}` | 更新项目 |
| POST | `/projects/{project_id}/cases` | 创建脱敏病例 |
| GET | `/projects/{project_id}/cases` | 病例列表 |
| GET | `/cases/{case_id}` | 病例详情（含素材计数） |
| PATCH | `/cases/{case_id}` | 更新病例 |
| POST | `/cases/{case_id}/assets` | 上传/关联素材（multipart） |
| GET | `/cases/{case_id}/assets` | 素材列表，支持 `status`、`type`、`tag` 筛选 |
| GET | `/assets/{asset_id}` | 素材详情 |
| PATCH | `/assets/{asset_id}` | 更新 display_name / tags / note / source |
| DELETE | `/assets/{asset_id}` | 软删除未评审素材；已存在评审历史时返回 `DELETE_RESTRICTED` |
| GET | `/assets/{asset_id}/preview` | 缩略图（image/dicom） |
| GET | `/assets/{asset_id}/model` | 模型文件流（STL） |
| GET | `/assets/{asset_id}/dicom/metadata` | 白名单 DICOM 元数据 |
| POST | `/assets/{asset_id}/reprocess` | 重新解析素材并重建预览/模型统计 |
| POST | `/assets/{asset_id}/annotations` | 新增结构标记 |
| GET | `/assets/{asset_id}/annotations` | 标记列表 |
| DELETE | `/annotations/{annotation_id}` | 删除标记 |
| POST | `/assets/{asset_id}/reviews` | 提交评审结论 |
| GET | `/assets/{asset_id}/reviews` | 评审历史 |
| GET | `/cases/{case_id}/reviews` | 病例评审时间线 |

### 5.3 关键请求/响应示例

创建病例：

```http
POST /api/v1/projects/{project_id}/cases
{ "case_code": "DEMO-TAVR-001", "note": "术前讨论前素材汇总" }
```

上传素材：

```http
POST /api/v1/cases/{case_id}/assets
Content-Type: multipart/form-data
file=<binary>
type=dicom              # 前端提示值，服务端仍以内容嗅探为准
source=pydicom test data
source_url=https://github.com/pydicom/pydicom
license_note=no restriction per README
```

上传类型判定：

- 前端提交的 `type` 只用于 UI 提示和用户意图记录。
- 服务端必须根据扩展名、魔数/文件头和解析结果判定最终 `assets.type` 与 `format`。
- 如果前端声明与服务端判定不一致，返回 `TYPE_MISMATCH`，不落库为正常素材。
- 上传失败必须清理临时文件；只有 DB 提交成功后才移动到正式 `var/uploads/{asset_id}`。

提交评审：

```http
POST /api/v1/assets/{asset_id}/reviews
{
  "status": "available",
  "conclusion_text": "LA 模型可加载，结构完整，可用于讨论前展示。",
  "reviewer": "术前规划工程师",
  "issue_summary": null,
  "next_action": null
}
```

错误响应：

```json
{
  "error": {
    "code": "UNSUPPORTED_FORMAT",
    "message": "文件内容与声明格式不一致。",
    "next_action": "请重新导出为受支持格式后上传。",
    "request_id": "0f4c...a91"
  }
}
```

---

## 6. 错误模型

所有错误返回稳定 `code` + 用户可读 `message` + `next_action` + `request_id`，**不返回堆栈**。

| code | HTTP | 触发场景 | 用户下一步 |
|---|---:|---|---|
| `VALIDATION_ERROR` | 400 | 参数不合法 | 修正输入 |
| `PROJECT_NOT_FOUND` | 404 | 项目不存在 | 返回项目列表 |
| `CASE_NOT_FOUND` | 404 | 病例不存在 | 返回病例列表 |
| `ASSET_NOT_FOUND` | 404 | 素材不存在 | 返回素材列表 |
| `CONFLICT` | 409 | 编号重复 | 修改编号 |
| `FILE_TOO_LARGE` | 413 | 超过 `APP_MAX_UPLOAD_MB` | 压缩或拆分 |
| `TYPE_MISMATCH` | 422 | 前端声明类型与服务端判定不一致 | 检查文件类型后重新上传 |
| `UNSUPPORTED_FORMAT` | 415 | 扩展名/魔数不符 | 重新导出 |
| `CHECKSUM_MISMATCH` | 422 | 哈希不一致 | 重新上传 |
| `DICOM_PARSE_FAILED` | 422 | DICOM 解析失败 | 检查文件完整性 |
| `DICOM_DECODE_UNSUPPORTED` | 422 | DICOM 压缩格式当前解码器不支持 | 保留元数据，预览不可用 |
| `DICOM_NO_PIXEL_DATA` | 422 | 无像素数据 | 保留元数据，无法预览 |
| `MODEL_PARSE_FAILED` | 422 | STL 损坏/过大 | 重新导出模型 |
| `IMAGE_PARSE_FAILED` | 422 | 图片解码失败 | 重新导出图片 |
| `SOURCE_REQUIRED` | 422 | 来源信息缺失 | 补充来源/许可 |
| `DELETE_RESTRICTED` | 409 | 已有评审历史的素材被删除 | 改用软删除或保留资产 |
| `FORBIDDEN` | 403 | 演示角色无权执行操作 | 切换到允许的演示角色 |
| `PERSISTENCE_FAILED` | 500 | 保存失败 | 重试，保留未提交内容 |
| `INTERNAL_ERROR` | 500 | 未预期异常 | 携带 request_id 反馈 |

映射规则：`domain/errors.py` 定义枚举与默认文案；`main.py` 注册全局异常处理器统一序列化。FastAPI/Pydantic 原生 422 在对外响应中统一映射为本项目错误模型，字段级细节放入 `error.details`，避免出现 400/422 契约漂移。

---

## 7. 文件、DICOM 与 3D 处理

### 7.1 上传校验

1. 大小 ≤ `APP_MAX_UPLOAD_MB`（默认 100）。
2. 扩展名 + 魔数/文件头嗅探 + 解析器试读三重校验，拒绝伪造格式。
3. 存储名使用 `asset_id`，禁止使用原始文件名，防止路径穿越。
4. 流式计算 SHA256 与字节数。
5. 使用临时文件接收上传；解析、哈希、DB 提交均成功后再移动到正式目录。
6. 任一阶段失败都清理临时文件和半成品预览。

### 7.2 存储布局

```text
var/uploads/{asset_id}/payload          # 原始文件，只读
var/previews/{asset_id}/thumbnail.png   # 派生预览
```

`storage/base.py` 定义 `put / get / open_stream / delete / exists`；`local.py` 为当前实现，未来可换对象存储。

### 7.3 DICOM 处理（pydicom）

- 元数据：`dcmread(path, stop_before_pixels=True)`，仅提取白名单字段（见 `docs/design/dicom-metadata-whitelist.md`）。
- 多帧：读取 `NumberOfFrames`；Rubo 清理副本 `0002_anonymized.DCM` 为 96 帧单文件，按 multiframe 处理，不按目录当序列。
- 解码依赖：安装 `pylibjpeg`、`pylibjpeg-libjpeg`、`pylibjpeg-openjpeg`、`pylibjpeg-rle`、`pyjpegls`，覆盖常见 JPEG Baseline、JPEG Lossless、JPEG 2000、JPEG-LS 和 RLE。GDCM 不作为 Windows 本地 MVP 强依赖。
- 缩略图：取中间帧 → 应用窗宽窗位 → Pillow 转 PNG。
- 解码失败降级：若元数据可读但像素解码失败，保留白名单元数据，`load_state=failed`，错误码 `DICOM_DECODE_UNSUPPORTED`，前端提示“元数据可用，预览不可用”。
- 无 Pixel Data：保留元数据，`load_state=failed`，错误码 `DICOM_NO_PIXEL_DATA`。

### 7.4 STL 处理

- 校验 80 字节头 + 三角面数，识别 binary/ASCII。
- 计算三角面数、包围盒写入 `assets.metadata`。
- 原始文件通过 `/assets/{id}/model` 流式返回，前端 `STLLoader` 加载。
- 大 STL 策略：默认允许 100 MB 内上传；前端加载超过 10 MB 的 STL 时显示加载进度和取消入口。`LA.stl` 约 14 MB，作为性能边界样例。首版不生成 3D 缩略图，`/preview` 对 `model` 返回 `PREVIEW_NOT_AVAILABLE` 或占位信息。

### 7.5 图片处理

- Pillow 校验解码 → 生成缩略图；失败返回 `IMAGE_PARSE_FAILED`。
- 图片列表默认展示缩略图；查询接口支持 `type`、`status`、`tag` 三个筛选维度。
- 用户最多选择两张图片进入并排比较；首版只做独立缩放/适应窗口，不做配准、融合、测量或诊断工具。
- “整理”在 MVP 中严格定义为维护标签、状态和备注，并保存人工评审结论；不扩展为文件夹树、画布标注系统或实时协作。

---

## 8. 可观测性

### 8.1 Request ID

- 读取请求头 `X-Request-ID`，缺失则生成 UUID4。
- 通过 `contextvars` 绑定到本次请求，写入响应头与所有日志。

### 8.2 结构化日志（structlog，JSON）

允许字段：`ts, level, event, request_id, method, path, status, duration_ms, asset_id, error_code`。

**禁止字段**：`PatientName`、`PatientID`、请求正文、原始文件名、完整 DICOM 标签集合、堆栈（客户端）。

### 8.3 健康检查

- `GET /health`：进程存活，不访问依赖。
- `GET /health/ready`：DB 可连接 + 存储目录可写；失败返回 503。

### 8.4 配置外置（pydantic-settings）

`APP_ENV / APP_LOG_LEVEL / APP_DATABASE_URL / APP_STORAGE_ROOT / APP_PREVIEW_ROOT / APP_MAX_UPLOAD_MB / APP_ALLOWED_ORIGINS`，见 `.env.example`。

---

## 9. 安全与隐私

- 只使用公开、去标识化或物理模体数据，登记来源/许可/日期/哈希（见 `sample-data/README.md`）。
- DICOM 元数据仅经后端白名单输出，前端不得直出原始标签。
- 原始文件名仅受控保存，不进入日志与默认响应。
- 上传、数据库、日志、预览默认不进入 Git（见 `.gitignore`）。
- 不宣称任何医疗法规认证；界面保留「仅供工程评审、不用于临床」声明。
- 权限边界：MVP 不做真实登录，只使用演示角色；写操作预留 `actor` 字段并写入审计事件，后续可接入真实权限。
- 角色建议：`planner_engineer` 可创建项目/病例/素材和提交评审；`technical_reviewer` 可提交评审和标记问题；`viewer` 只读。
- 真实医疗软件所需权限、审计、隐私合规、数据脱敏和协作能力差距见 `docs/engineering/real-world-readiness.md`；该文档说明演进边界，不代表本 MVP 已获得法规认证。

---

## 10. 技术选型与取舍（ADR 摘要）

| ADR | 决策 | 备选 | 理由 |
|---|---|---|---|
| 001 | 模块化单体 + 单仓库 | 微服务 | 面试规模，优先闭环；微服务引入无收益复杂度 |
| 002 | 开发用 SQLite，保留 PostgreSQL 路径 | 直接 PostgreSQL | 本地零依赖；经 SQLAlchemy + Alembic 可平滑切换 |
| 003 | FastAPI + Pydantic + SQLAlchemy | Node/Express、Java、Go | 医学影像 Python 生态最强；自动 OpenAPI |
| 004 | 服务端 pydicom 解析 + 服务端缩略图 | Cornerstone/OHIF 前端阅片 | 隐私可控、前端简单；完整阅片超出题目边界 |
| 005 | three.js + R3F + Drei 加载 STL | vtk.js、Babylon.js | STLLoader/OrbitControls 现成，交互覆盖 4 项以上 |
| 006 | Ant Design | shadcn/ui、MUI | 中后台组件齐全，出活快；与已装依赖一致 |
| 007 | structlog + request_id | 标准 logging | JSON 结构化，满足运维排障与 JD 要求 |
| 008 | 本地文件存储抽象 | 立即对象存储 | MVP 足够，接口抽象保留演进 |
| 009 | 评审追加式历史，状态由最新评审派生 | 就地覆盖状态 | 结论可追溯，符合产品核心价值 |
| 010 | Docker/Nginx 延后到 P7 | 立即容器化 | 当前未装 Docker，不阻塞 P1-P6 |
| 011 | 增加 pylibjpeg/pyjpegls，GDCM 不做 MVP 强依赖 | 只依赖 Pillow 或强依赖 GDCM | 覆盖常见压缩 DICOM；Windows 本地安装风险可控 |
| 012 | 素材默认软删除，已评审资产禁止硬删除 | DELETE 直接物理删除 | 保留评审历史，避免破坏“结论可追溯”核心价值 |
| 013 | 后端判定最终素材类型 | 信任前端 `type` | 避免声明类型与内容不一致，降低伪造/误传风险 |

---

## 11. 本地环境与工具链对齐

| 项 | 版本/状态 | 设计影响 |
|---|---|---|
| Node.js | v24.14.0 | Vite 8 / React 19 可用 |
| npm | 11.18.0 | PowerShell 下用 `npm.cmd` / `npx.cmd` |
| Python | 3.11.9（`apps/api/.venv`） | `requires-python >=3.11,<3.13` |
| Git | 2.53.0 | 提交门禁见 `docs/engineering/development.md` |
| Docker | 未安装 | P7 引入，本设计已预留配置外置与健康检查 |
| VS Code | 1.138.0 | Tasks 调用 `scripts/*.ps1` |

VSCode 扩展：Python / Pylance / Ruff（后端）、ESLint / Prettier（前端）、Playwright（E2E）、Docker（P7）、SQLite Viewer（数据查看）、ChatGPT/Codex（AI 协作）。

---

## 12. 需求 → 设计追溯

| 需求 | 设计落点 |
|---|---|
| FR-001 项目/病例 | `projects`/`cases` 表 + 第 5.2 端点 |
| FR-002 关联素材与来源 | `assets.source/source_url/license_note` + 上传端点 |
| FR-003 UUID/大小/哈希/格式 | `assets.id/size_bytes/sha256/format` + 7.1 |
| FR-004 素材卡片字段 | `assets.display_name/format/source/tags/status/note` |
| FR-005 DICOM 元数据/缩略图/多帧 | 7.3 + 白名单文档 |
| FR-006 3D 五项交互 | 第 2 节前端 viewer3d + 7.4 |
| FR-007 评审结论保存 | `reviews` 表 + 第 5.3 示例 |
| FR-008 类型/状态/标签筛选 | 5.2 `GET /cases/{id}/assets?status&type&tag`（Must） |
| FR-009 图片浏览/比较/整理 | 7.5 + 前端 `features/assets`（Must） |
| FR-010 异常与 request_id | 第 6 节错误模型 + 8.1 |
| FR-011 结构化日志与脱敏 | 8.2 + 第 9 节 |
| NFR-002 SQLite/PostgreSQL | ADR-002 |
| NFR-004 稳定错误码 | 第 6 节 |
| NFR-005/006 日志与白名单 | 8.2 + 9 |
| NFR-007 自动化 | `docs/engineering/development.md` 提交门禁 |
| 边界：审计/权限 | 第 9 节角色边界 + `audit_events` 预留 |
| 边界：重处理 | 第 5.2 `POST /assets/{asset_id}/reprocess` |

---

## 13. 测试策略

| 层 | 工具 | 覆盖 |
|---|---|---|
| 单元 | pytest | 白名单过滤、哈希、状态机、错误映射、STL/DICOM 解析 |
| 集成 | pytest + httpx | 项目/病例/素材/评审 API、异常路径 |
| 前端组件 | Vitest + Testing Library | 素材卡片、筛选、状态流转、viewer 交互 |
| E2E | Playwright | 五分钟主流程 + 至少一条异常流程 |
| 隐私 | 日志扫描脚本 | 断言无 PatientName/PatientID/原始文件名 |

P3/P4 必测补充：

- `unique(project_id, case_code)` 命中后返回 `CONFLICT`。
- 前端声明 `type` 与服务端判定不一致时返回 `TYPE_MISMATCH`。
- 已存在评审历史的资产执行 DELETE 返回 `DELETE_RESTRICTED`。
- DICOM 元数据可读但像素解码失败时返回 `DICOM_DECODE_UNSUPPORTED`，且仍可展示白名单元数据。
- 上传失败后临时文件与预览半成品被清理。
- `POST /assets/{asset_id}/reprocess` 可重建 metadata/preview，失败时不破坏旧记录。

---

## 14. 部署与运维演进（P7）

- Dockerfile（多阶段）+ docker-compose（API/Web/Nginx，健康检查，持久卷）。
- Nginx 托管前端静态 + `/api` 反代。
- 配置全走环境变量；提供 `.env.example`。
- 结构化日志 + request_id 贯穿；提供日志分析示例。
- SQLite 备份脚本 + 恢复演练；说明 PostgreSQL 切换路径。

---

## 15. P2 退出检查清单

- [x] 系统上下文、模块边界、分层规则
- [x] 数据模型（实体、字段、索引、状态机）
- [x] API 契约（端点、约定、示例）
- [x] 错误模型（稳定错误码 + 下一步）
- [x] 文件/DICOM/3D 处理与隐私策略
- [x] 可观测性（request_id、日志字段、健康检查、配置外置）
- [x] 技术取舍 ADR 与需求追溯
- [x] 人工评审确认（用户已确认，可进入 P3）
- [x] P2 复审整改：压缩 DICOM、服务端判型、软删除、唯一约束、统一错误、reprocess、权限/审计边界
