# Project progress

最后更新：2026-09-21
项目根目录：仓库根目录（本地路径不进入公开文档）

| 阶段 | 状态 | 退出门禁 | 当前证据/下一步 |
|---|---|---|---|
| P0 环境准备 | 完成 | IDE、运行时、项目隔离依赖、Git 与环境核验完成 | 环境记录见 `docs/engineering/environment.md` |
| P1 产品设计 | 完成 | 定位、首要用户、痛点、流程、范围、PRD 与验收矩阵确认 | 定位为“结构性心脏病术前规划素材评审工作台”，见 `docs/product/` |
| P2 技术设计 | 完成 | 架构、数据模型、API、文件、隐私、日志和 ADR 评审完成 | `TECH_DESIGN.md`；DICOM 白名单见 `docs/design/dicom-metadata-whitelist.md` |
| P3 脚手架 | 完成 | 前后端空工程、健康检查、迁移、基础日志和 CI 可运行 | 健康/就绪检查、request_id、JSON 日志、Alembic baseline、统一检查入口 |
| P4 后端 | 收口完成 | 核心数据/API/文件/DICOM 服务达到需求验收 | `docs/product/08-p4-backend-acceptance.md` |
| P5 前端 | 收口完成 | 核心页面、状态和 3D/DICOM 交互达到需求验收 | `docs/product/09-p5-frontend-acceptance.md` |
| P6 异常/边界 | 收口完成 | 损坏、缺失、伪造、超限、保存失败等路径有明确处理 | `docs/product/10-p6-boundary-acceptance.md` |
| P7 运维化 | 收口完成 | Docker Compose、Nginx、配置、健康检查和运维说明完成 | `docs/product/11-p7-operations-acceptance.md`；`docs/engineering/ops.md` |
| P8 测试 | 收口完成 | 单元、集成、E2E、隐私扫描与测试报告通过 | `docs/product/12-p8-test-report.md`；`scripts/check-full.ps1` 输出 `Full P8 gate passed.` |
| P9 文档 | 未开始 | README、PRD、设计、部署、AI 使用和演示材料一致 | 收口文档一致性、移除过期内容、补齐交付说明 |
| P10 交付验收 | 未开始 | 新环境可复现，五分钟演示和交付清单全部通过 | 新环境复现 + 五分钟演示 + 交付清单 |

## 当前决策

- 使用小型单仓库；开发期使用 SQLite，本地文件系统保存素材；生产演进目标为 PostgreSQL。
- 演示与测试使用**隔离的 Compose 环境**：演示栈 `med-review-workbench`（端口 8080），门禁栈 `medreview-p8-gate`（端口 18080，用完连卷销毁）。规范见 `docs/engineering/demo-and-test-data.md`。
- 演示库重置入口：`scripts/reset-demo.ps1`。
- 宿主机数据库与容器卷不可混用（预览/模型记录创建时的绝对路径）。
- 面试题要求的图片浏览/筛选/比较/整理已作为 Must 实现，样例为两张可提交的非临床合成 PNG。
- DICOM 演示使用 `prepare-dicom-samples.py` 生成的本地清理副本，原始样例不直接进入应用或演示。

## 当前门禁

进入 P9：收口 README、PRD、技术设计、运维手册、AI 使用记录与演示材料的一致性；清理过期内容；确保文档与 `check-full.ps1` 的实际行为一致。

## 已完成（2026-09-21 补齐）

- 素材标签与备注（`PATCH /assets/{id}`）与按标签筛选。
- STL 结构标记：点击模型放置标记点并持久化（`annotations`）。
- 图片并排比较。
- 前端拆包（应用主包约 54KB，vendor 可缓存，three.js 懒加载）。
- 交付截图：`docs/screenshots/`。

## 已知延期项（不阻塞 P9，须在 P10 前决定补齐或以范围差异说明）

- 真实鉴权、持久化审计表、reprocess、标注批量编辑。
- PostgreSQL 仅提供可配置切换路径，未做生产负载验证。
