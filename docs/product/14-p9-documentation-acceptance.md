# P9 文档一致性验收

状态：收口完成（2026-09-21）。此处只确认文档与已实现范围、已取得的自动化证据一致，不代替 P10 人工演示。

## 核对结果

| 项目 | 当前交付口径 | 依据 |
|---|---|---|
| 面试题功能 | 病例下图片/DICOM/STL 归档、浏览、筛选、双图比较、3D 结构标记与评审闭环；不宣称临床用途 | `docs/product/13-delivery-readiness.md`、`docs/product/04-acceptance-matrix.md` |
| 测试 | 最新完整门禁：API 31（覆盖率 92%）、前端组件 3、Playwright 8（Mock 2 + 真实后端 6）、隐私日志扫描 131 行零命中 | `docs/product/12-p8-test-report.md` 第 3、12 节 |
| 首屏体积 | 当前应用主包约 54KB，vendor 单独拆分；旧 P5 体积数字只属于历史版本 | `README.md`、`docs/product/09-p5-frontend-acceptance.md` |
| 新克隆样例 | Git 内有两张非临床 PNG、一份已脱敏的公开 CT DICOM（pydicom MIT 清理副本）和一份 CC BY 4.0 心脏参考 STL；仅当文件缺失时 seed 才生成非临床 phantom，题目原始大样例不入库 | `README.md`、`sample-data/README.md`、`sample-data/stl/ATTRIBUTION.md` |
| 部署与运维 | Compose + SQLite 持久卷；seed 为显式步骤；`down` 不删卷，`down -v` 会删卷 | `README.md`、`docs/engineering/ops.md` |
| AI/医疗边界 | 无真实 AI 诊断；人工评审，不接入真实患者系统；隐私扫描不等于临床级脱敏认证 | `docs/engineering/ai-usage.md`、`docs/engineering/real-world-readiness.md` |

## 修正和边界

- P9 当时曾把验收矩阵中的 Playwright 数量从旧轮次修订为 7，随后测试继续增加；当前数量以表格和 P8 测试报告为准。P5 历史报告只保留阶段记录，不冒充当前证据。
- 公开仓库代码目前没有 `LICENSE`。不擅自添加 MIT 或宣称代码通用复用授权；仓库所有者可另行决定许可证。心脏参考 STL 单独按 CC BY 4.0 署名分发。
- 真实鉴权、持久化业务审计表、reprocess、标注批量编辑及 PostgreSQL 生产验证未完成，按范围差异公开披露。
- 截图和自动化 E2E 不是人工五分钟演示；这一项保留在 P10 清单中。

## 交付入口

面试官从根 README 的“快速启动”执行 Docker Compose + seed；技术/API 见 `TECH_DESIGN.md`，运维和排障见 `docs/engineering/ops.md`，五分钟路线见 `docs/product/06-demo-script.md`，当前交付状态见根目录 `DELIVERY_CHECKLIST.md`。

