# 演示数据与测试数据规范

状态：生效中（2026-09-21）

本文件定义演示环境与自动化测试数据的边界，避免测试产物污染演示数据、避免开发机与容器数据库混用。

## 1. 两套独立环境

| 环境 | Compose 项目 | 卷 | 端口 | 用途 |
|---|---|---|---|---|
| 演示栈 | `med-review-workbench` | `med-review-workbench_medreview_data` | `8080` | 人工演示、录屏、验收 |
| P8 门禁栈 | `medreview-p8-gate` | `medreview-p8-gate_medreview_data` | `18080` | 自动化测试专用 |

**硬性规则**：自动化门禁与测试（尤其是会创建临时项目的 Playwright E2E）**不得写入演示栈**。显式执行的 `seed_demo` 和人工演示操作是演示栈的预期写入，不属于这条禁令。`scripts/check-full.ps1` 通过 `docker compose -p medreview-p8-gate` + `WEB_PORT=18080` 使用隔离栈，并在 `finally` 中以 `down -v` 彻底销毁（含卷）。

## 2. 为什么必须隔离

`live-review-flow.spec.ts` 每次运行都会**新建一个带时间戳的项目**（`P8 Live <timestamp>`）。若它打在演示栈上，演示库会不断累积 `P8 Live …` 之类的一次性数据，导致演示页面出现大量"脏数据"。历史事故即由此产生。

隔离后：
- 演示栈的卷永远只包含 `seed_demo` 写入的干净数据；
- 门禁栈每次运行后连卷一起删除，不留残留。

## 3. 演示数据重置

当演示库被手动验证或历史测试污染时，执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\reset-demo.ps1
```

该脚本会：删除演示栈与演示卷 → 重建镜像 → 重新 `seed_demo`。执行后演示页只应出现一个项目：`Demo - SHD preoperative asset review`。

## 4. 演示种子内容

`scripts/seed-demo.py`（宿主机）与 `apps/api/app/ops/seed_demo.py`（容器内）写入同一份种子，均**幂等**（重复执行返回相同项目/病例 ID）：

- 项目：`Demo - SHD preoperative asset review`
- 病例：`DEMO-TAVR-001`
- 素材：合成 PNG（已通过评审）、DICOM、STL。全新克隆 seed 使用仓库内有 CC BY 4.0 署名的心脏参考 STL，并在缺少本地清理 DICOM 时生成非临床 phantom；仅当心脏 STL 文件缺失时回退到合成曲管。本地提供清理 DICOM 时优先读取；题目 `aorta.stl` 需手动上传，不再作为默认 seed。已有演示库再次 seed 会新增心脏素材，不会删除旧曲管或 `aorta.stl`，录屏时请确认选择“心脏参考模型”标签的素材。

容器内 seed 通过只读挂载 `../sample-data:/sample-data:ro` 读取样例，命令：

```powershell
docker compose -f .\deploy\docker-compose.yml exec -T api python -m app.ops.seed_demo --sample-root /sample-data
```

## 5. 宿主机与容器数据库不可混用

`assets.preview_path` / `storage_path` 是**创建时的绝对路径**：

- 容器内创建 → `/data/previews/…`
- 宿主机创建 → `apps/api/var/previews/…`（Windows 绝对路径）

因此**同一个 SQLite 文件不能在宿主机与容器之间来回切换使用**，否则预览/模型会因路径不存在而 404。选择一种运行方式：

- 演示与验收：只用 Docker 栈（`http://localhost:8080`）；
- 本地开发：只用宿主机（uvicorn + `npm run dev`，`var/` 目录）。

如需切换，先 `reset-demo` 或删除 `apps/api/var/medreview.db` 重新 seed。

## 6. 前端 UI 与 E2E 选择器约定

- AntD v6 默认会在**两个中文字符**的按钮中插入空格（`查看` → `查 看`），导致文本选择器不稳定。项目已在 `ConfigProvider` 设置 `button={{ autoInsertSpace: false }}` 关闭该行为。**新增按钮文案不需要为空格做兼容。**
- 弹窗主按钮统一用 `.ant-modal-footer .ant-btn-primary` 选择，避免依赖按钮文案与语言。
- 页面文案（如"白名单元数据"）如被多处包含，断言必须使用 `{ exact: true }` 或更精确的 role/选择器，避免 Playwright strict mode 冲突。

## 7. 门禁入口

```powershell
# 快速门禁（日常开发）：静态检查 + 单元/集成 + 前端构建
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1

# 完整门禁（P8 收口）：+ 隔离栈 + 覆盖率 + 真实 E2E + 隐私扫描 + 依赖审计
powershell -ExecutionPolicy Bypass -File .\scripts\check-full.ps1
```

完整门禁通过时应输出 `Full P8 gate passed.`，且结束后 `docker volume ls` 中**不应残留** `medreview-p8-gate_medreview_data`。
