# P8 测试与证据报告

状态：收口完成（2026-09-21）

## 1. 结论

P8 门禁通过。快速检查和完整检查均实际执行成功；核心“项目 → 病例 → 素材 → 评审 → 看板”闭环同时具备 API 集成测试、前端组件测试、Mock E2E 和 Docker 真实后端 E2E 证据。

本结论只覆盖当前已实现范围。结构标记、标签/筛选和图片并排比较已在后续整改中补齐；真实鉴权、持久化审计表、reprocess 和 PostgreSQL 生产验证仍未被包装成“已通过”，详见第 6、9 节。

## 2. 环境与命令

| 项目 | 实际环境 |
|---|---|
| 日期 | 2026-09-21 |
| 宿主系统 | Windows / PowerShell |
| Python | 3.11.9 |
| Node.js / npm | 24.14.0 / 11.18.0 |
| Docker | 29.8.0 |
| 浏览器 | 本机 Chrome 通道，由 Playwright 驱动 |
| 应用运行 | Docker Compose 隔离门禁栈 `http://127.0.0.1:18080`；API/Web healthy；演示栈独立使用 8080 |
| 默认数据库 | SQLite 持久卷；PostgreSQL 仅保留切换路径 |

快速开发门禁：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

P8 完整门禁：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check-full.ps1
```

完整门禁会启动并等待 Compose、执行容器 seed、覆盖率、真实后端 E2E、运行日志隐私扫描和依赖审计。测试迁移使用临时 SQLite 文件，不会升降级开发数据库。

## 3. 实际结果

| 层级 | 结果 | 证据摘要 |
|---|---|---|
| Python 静态检查 | 通过 | Ruff、Mypy 通过 |
| API 单元/集成 | 29 passed | 覆盖业务闭环、文件解析、异常边界、标签/备注、结构标记、日志、seed、备份恢复和隐私扫描 |
| API 覆盖率 | 92% | 1063 statements，87 missed；关键路由 97%、领域错误 97%、主应用 98%、repository 96% |
| 数据库迁移 | 通过 | 隔离临时库执行 upgrade、downgrade，不污染运行数据库 |
| Web 静态/构建 | 通过 | ESLint、TypeScript/Vite 生产构建通过 |
| Web 组件 | 3 passed | 页面工作区、四种状态映射、可恢复错误提示 |
| Web 覆盖率 | 语句 40.65%；分支 39.31%；函数 27.83%；行 40.00% | 如实记录，复杂交互主要由真实后端 E2E 覆盖；不设置虚假覆盖率门槛 |
| Playwright | 7 passed | 2 条 Mock 流程 + 5 条 Docker 真实后端流程（主链、异常、标签、双图比较、结构标记） |
| 异常 E2E | 通过 | API abort 可恢复提示；真实后端不支持格式返回稳定提示与下一步 |
| 隐私日志扫描 | 通过 | 最新隔离门禁扫描 Docker API 日志 105 行，敏感模式命中 0 |
| Python 依赖审计 | 通过 | `pip-audit` 无已知漏洞；本地项目包 `medreview-api` 因不在 PyPI 被明确跳过 |
| Node 生产依赖审计 | 通过 | `npm audit --omit=dev --audit-level=high`：0 vulnerabilities |

真实后端 E2E 不是 `page.route` Mock：浏览器通过 Nginx 调用容器 API，实际创建项目/病例、上传合成 PNG、提交评审并校验看板；异常流实际上传不支持文件并检查用户下一步。

## 4. FR/NFR 追溯

| 需求 | P8 判定 | 自动化/运行证据 |
|---|---|---|
| FR-001 项目与病例 | 通过 | API 闭环测试；真实后端 E2E 经 UI 创建项目和病例 |
| FR-002 素材归档 | 通过（当前支持范围） | DICOM/STL/PNG/JPEG 上传与判型测试；真实 E2E 上传合成 PNG |
| FR-003 UUID/大小/哈希/格式 | 通过 | API 上传集成测试与真实 E2E |
| FR-004 卡片状态与备注 | 通过 | 四状态映射；素材级标签与备注可编辑（`PATCH /assets/{id}`）并展示在卡片上 |
| FR-005 DICOM 安全元数据/预览 | 通过 | 白名单、身份字段抑制、无 Pixel Data/预览降级测试 |
| FR-006 STL 交互/结构标记 | 通过 | 旋转/缩放/平移/复位；点击模型放置结构标记并持久化；E2E 覆盖标记落库 |
| FR-007 评审持久化 | 通过 | API 集成测试；真实 E2E 提交后查询看板确认 `accepted` |
| FR-008 类型/状态/标签筛选 | 通过 | API 与前端均支持类型、状态、标签筛选 |
| FR-009 图片浏览/并排比较/整理 | 通过 | 单图预览、双图并排比较、标签/状态整理与结论沉淀；真实后端 E2E 断言左右为不同且可解码的预览 |
| FR-010 异常可解释 | 通过 | P6 API 边界测试、前端错误组件、Mock/真实异常 E2E |
| FR-011 可追踪且不泄露的日志 | 通过 | request_id 测试；最新运行日志扫描 105 行、0 命中 |
| NFR-002 SQLite/PostgreSQL 路径 | 部分通过 | SQLite 迁移、持久卷、备份恢复已验证；PostgreSQL 仅文档化，未生产验证 |
| NFR-006 DICOM 白名单 | 通过 | 白名单单测、敏感描述字段抑制、日志隐私扫描 |

## 5. P8 门禁核对

- [x] 单元、集成、前端组件和 Playwright 主流程通过。
- [x] 至少一条异常 E2E 通过；本次包含 Mock abort 和真实不支持格式两条。
- [x] 运行日志隐私扫描通过，且扫描器本身有正反样例单测。
- [x] Python 与 Node 生产依赖安全检查通过或明确解释跳过项。
- [x] 报告包含环境、范围、实际结果、需求追溯和已知风险。
- [x] `scripts/check-full.ps1` 一键执行完整门禁并最终输出 `Full P8 gate passed.`。

### 修复后复验记录

历史问题：Mock E2E 的宽泛文本定位和未拦截预览请求曾导致严格模式冲突和伪预览成功。现在“白名单元数据”使用精确匹配，Mock 预览返回可解码合成 PNG，并断言 `naturalWidth > 0`。这些修复已包含在第 3、11 节的最新完整门禁结果中；不再用旧轮次数字代表交付状态。

## 6. 已知风险与延期项

以下项目不会阻塞 P8“验证现有能力”的退出。原先列出的“结构标记、标签、图片并排比较”三个 Must 已在 2026-09-21 补齐（见第 8 节），剩余项须在 P10 前决定补齐或以范围差异说明接受：

1. **真实权限、持久化审计表、reprocess、标注批量编辑延期**：它们不是当前闭环的隐藏“伪完成项”。
2. **PostgreSQL 未作生产验证**：仅验证了可选驱动/配置边界和 SQLite 运维路径。
3. **前端组件覆盖深度有限**：行覆盖率 40.00%，函数覆盖率 27.83%；真实 E2E 覆盖主链、异常、标签、双图比较与结构标记，不等于组件分支全覆盖。
4. **STL 拖拽旋转/缩放本身未做像素级断言**：标记落库与查看器加载失败兜底已自动化，手势精度仍依赖人工演示确认。
5. **非阻塞技术债**：FastAPI/Starlette TestClient 有上游弃用警告；`pip-audit` 无法审计不在 PyPI 的本地项目包。

## 7. 医疗与 AI 边界

- 测试只使用合成图片、明确清理的本地样例或测试内生成数据，不接入真实患者系统。
- 隐私扫描是工程保护证据，不等同于临床级去标识化认证，也不能证明像素中不存在烧录文字。
- 产品没有接入真实 AI；评审状态和备注由人工提交、人工确认。
- 本系统是术前规划素材工程评审工具，不输出诊断、治疗建议或自动分割结果。

## 8. 2026-09-21 整改记录

演示验收时发现四类问题，已修复并复验：

1. **演示库被测试数据污染**：`live-review-flow.spec.ts` 每次运行新建带时间戳项目，且与演示共用同一持久卷。整改：`check-full.ps1` 改用隔离 Compose 项目 `medreview-p8-gate` + 端口 `18080`，结束后 `down -v` 销毁；新增 `scripts/reset-demo.ps1` 清理历史脏数据。规范见 `docs/engineering/demo-and-test-data.md`。
2. **STL 视图空白**：查看器未做模型居中与相机自适应，真实心脏模型落在视锥外。整改：`StlViewer` 使用 `geometry.center()` + drei `<Bounds fit clip observe>`，并新增"视角复位"重新适配。
3. **UI 观感与开发残留**：移除顶栏 `P5 前端` 开发标签，重做布局/主题/卡片/资产详情，启用中文 locale，关闭 AntD 按钮自动空格。
4. **E2E 断言脆弱**：mock 用例因 P6 新增兜底 Alert 文案与卡片标题重复触发 strict mode 冲突；AntD 中文按钮自动空格导致 `查看`/`确定` 文本选择器失效。整改：断言改为 `{ exact: true }` 或 `.ant-modal-footer .ant-btn-primary`，并关闭按钮自动空格。

该轮整改后 `scripts/check-full.ps1` 实测输出 `Full P8 gate passed.`，且运行后演示卷中仍只有 `Demo - SHD preoperative asset review` 一个项目；最新结果见第 11 节。

## 9. 2026-09-21 功能补齐与交付材料

1. **三个 Must 需求补齐**：素材标签/备注（`PATCH /assets/{id}` + 标签筛选）、STL 结构标记（`annotations` CRUD + 点击模型放置）、图片并排比较。迁移 `0003_tags_annotations`；最新测试数量见第 3、11 节。
2. **前端拆包**：应用主包由约 946KB 降至约 54KB，`antd`/`react` 拆为可缓存 vendor chunk，`three.js` 仅在 STL 详情加载。
3. **交付截图**：`docs/screenshots/` 由 `apps/web/scripts/capture-screenshots.mjs` 从运行中的演示栈生成，并在 README 中引用。
4. **审计健壮性**：`check-full.ps1` 对 Python/Node 依赖审计增加 3 次重试，缓解网络抖动。

## 10. 公开仓库交付前复验（2026-09-21）

- 从原始 Word 面试题重新核对 Must：项目/病例/素材、图片浏览筛选比较整理、DICOM 读取、STL 操作、异常、文档、AI 与医疗边界。
- 修复全新克隆缺少 DICOM/STL 的演示缺口：seed 在外部样例缺席时确定性生成非临床 DICOM phantom 和曲管 STL；单测验证三类素材、DICOM 预览与幂等性。
- 该轮隔离完整门禁及随后双图比较补测均通过；当前交付数字统一见第 3、11 节。

## 11. 双图比较交付前复验（2026-09-21，最新）

- 比较弹窗的两侧选项改为安全标签/素材短 ID，不暴露原始文件名；已经选到左侧的素材不再出现在右侧可选列表，反之亦然。
- 新增真实后端 Playwright：上传仓库内第二张合成 PNG，在比较弹窗选择两张不同图片，断言左右预览均解码成功且 `src` 不同。
- 最新完整门禁：API `29 passed`、覆盖率 `92%`；Web 组件 `3 passed`，语句/分支/函数/行覆盖率分别为 `40.65% / 39.31% / 27.83% / 40.00%`；Playwright `7 passed (10.5s)`；隐私扫描 `scanned_lines=105 findings=0`；Python 依赖无已知漏洞，Node 生产依赖 `0 vulnerabilities`；最终输出 `Full P8 gate passed.`，并销毁隔离栈和卷。
