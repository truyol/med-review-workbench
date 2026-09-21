# GitHub 面试交付复核

复核日期：2026-09-21。对照原始《医疗 DICOM、3D 素材与方案评审工作台》Word 题目；不把项目内部 PRD 当作唯一验收来源。

## 交付入口

- 公开仓库：<https://github.com/truyol/med-review-workbench>
- 面试官按根 README 的“面试官快速启动”两条 Docker Compose 命令启动并 seed，然后打开 `http://localhost:8080`。
- `README.md`、`TECH_DESIGN.md`、`docs/product/`、`docs/engineering/ops.md`、`sample-data/README.md`、演示截图均在仓库中。
- Git 不包含 `.env`、数据库、上传素材、原始 DICOM/STL、私钥、虚拟环境或 `node_modules`。

## 原始题目逐项对照

| 题目项 | 本项目证据与边界 |
|---|---|
| 自定义用户、场景、定位 | 面向术前规划工程师的素材工程评审；`docs/product/00-product-brief.md`、`03-prd.md` |
| 项目/病例/素材结构、来源、标签、状态、备注和结论 | SQLAlchemy 模型、迁移、API 与前端；真实后端 E2E 覆盖主链与标签 |
| 图片浏览、筛选、比较、整理、结论沉淀 | 两张合成 PNG、标签/状态筛选、双图并排、评审结论；`docs/product/12-p8-test-report.md` |
| DICOM 读取 | 白名单元数据、单帧缩略图、多帧识别与失败降级；默认 seed 使用无患者来源的 64×64 phantom，开源外部样例获取步骤见 `sample-data/README.md` |
| 3D 加载与至少三项操作 | STL 旋转、缩放、平移、复位和结构标记；全新克隆默认生成曲管 STL，题目 STL 可选本地加载 |
| API/模块边界 | `TECH_DESIGN.md` 和根 README API 一览；路由/服务/repository 分层 |
| 异常处理 | 损坏/不支持/超限/保存失败/预览与模型加载失败；稳定错误码、下一步、request_id；P6 与 P8 证据 |
| 技术与运维文档 | README 快速启动、技术设计、运维手册、健康检查、备份恢复、已知问题 |
| 真实医疗软件差距 | `docs/engineering/real-world-readiness.md`；明确真实权限、审计、隐私合规、脱敏与协作缺口 |
| AI 使用与医疗边界 | `docs/engineering/ai-usage.md` 与 `docs/product/07-ai-product-boundary.md`；没有真实 AI 接入，医疗结论由人工确认 |

## 新克隆实测

在只含 Git 跟踪文件的本地克隆中，没有 DICOM/STL 外部文件，也没有开发机的运行数据：

1. 隔离 Compose 项目 `medreview-clone-check` 在端口 `18081` 完成镜像构建并进入 healthy。
2. 容器 seed 成功：1 项目、1 病例、3 类素材（PNG、DICOM、STL）。DICOM 元数据为 `PHANTOM`/64 行，预览 HTTP 200；STL 模型流 HTTP 200。
3. 对该克隆栈运行 Playwright：`6 passed (9.9s)`，包括真实后端主链、异常、标签和结构标记。
4. 验证完成后销毁隔离容器/卷和临时克隆；正式演示栈未被清理。

当前源码完整门禁另行通过：API 29 项、覆盖率 92%；组件 3 项；Playwright 7 项（新增双图比较真实后端用例）；日志隐私扫描 105 行零命中；依赖审计无已知漏洞。详细输出见 P8 报告。上方干净克隆的 6 条 E2E 是新增比较用例前的独立验证，不冒称为 7 条。

## 交付时需要如实说明

- 本项目是面试工程原型，不是临床诊断、治疗或医疗器械软件；生成的 phantom/曲管不是患者影像或真实解剖。
- 题目原始 STL 和外部 DICOM 不随 Git 分发。若面试官要验证指定样例，按 README 和 `sample-data/README.md` 自行获取，并仅使用清理副本。
- 没有真实登录/权限、持久化业务审计表、reprocess、多人协作或 PostgreSQL 生产负载验证。原始题目明确不要求复杂权限等能力；这些不应被描述成已实现。
- 前端组件覆盖率仍偏低；自动化 E2E 不等于临床级验证或完整 WebGL 像素级验收。
- 仓库目前未选择开源许可证；公开可供面试评估，但不得把“公开”描述为已授予通用二次使用许可。若要开放复用，需由仓库所有者决定许可证。
- P10 的人工五分钟演示、刷新/重启持久性最终展示和面试官设备复现仍需实际完成后才能标为“交付验收完成”。
