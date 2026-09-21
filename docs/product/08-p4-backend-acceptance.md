# P4 后端收口验收清单

状态：Ready for P5（2026-09-21）

本清单只验收“病例下素材评审闭环”，不把后续增强能力伪装成 P4 已完成。

## 1. P4 必须通过

- [x] 项目创建与列表：`POST/GET /api/v1/projects`
- [x] 病例创建与列表：`POST/GET /api/v1/projects/{project_id}/cases`
- [x] 同一项目内 `case_code` 唯一，冲突返回 `CASE_CODE_CONFLICT`（409）
- [x] 素材上传：服务端识别 DICOM、STL、PNG/JPEG，不信任前端 `type`
- [x] 上传记录保存 UUID、大小、SHA256、服务端判定类型和来源标签
- [x] DICOM 只返回白名单元数据；`PatientName`、`PatientID` 不进入响应或日志
- [x] 无 Pixel Data 或压缩解码不可用时降级为“可读元数据、无预览”，不返回 500
- [x] STL ASCII/二进制结构校验，记录编码与三角面数量；损坏文件返回 `MODEL_PARSE_FAILED`
- [x] 素材列表支持有上限的 `limit/offset`，并支持 `kind/status` 基础筛选
- [x] 图片预览和 STL 模型读取端点可供 P5 使用；文件缺失返回稳定错误码
- [x] 评审记录追加保存；素材当前状态由最新评审派生，评审后硬删除返回 `DELETE_RESTRICTED`
- [x] 病例评审看板可返回素材与最新评审，组成完整闭环
- [x] 错误响应包含稳定 `code/message/next_action/request_id`，响应头包含 `X-Request-ID`
- [x] API ruff、mypy、pytest、Alembic upgrade/downgrade、前端 lint/test/build 全部通过

## 2. 本阶段明确延期

| 能力 | 决策 | 原因 | 计划阶段 |
|---|---|---|---|
| `reprocess` 重处理 | 延期 | 当前上传时已完成解析；P5 没有失败后重试入口的用户流程 | P6：异常恢复时实现，要求旧记录不被破坏 |
| `audit_events` 审计表 | 延期 | P4 已有 request_id、结构化日志和追加式评审历史，足以支撑演示追踪；真实审计需先确定 actor/保留期/导出策略 | P7/P8：运维与合规增强 |
| 真实权限控制 | 延期 | 当前是无登录演示产品；现在伪造 RBAC 会造成安全假象 | P7：接入认证后再做服务端授权矩阵 |
| 标注 CRUD | 延期 | 标注依赖 P5 的 2D/3D 交互和数据坐标协议，提前做会形成孤立 API | P5：先确定交互和格式，再实现最小 CRUD |

延期不是删除设计：相关数据模型、API 方向和边界已在 `TECH_DESIGN.md` 中保留，进入对应阶段时再落地。

## 3. P4 不纳入验收的边界

- 不做临床诊断、治疗建议、自动分割或真实 AI 推理。
- 不接入真实患者系统、PACS、账号系统或多租户权限。
- 不把原始 DICOM、患者身份信息或原始文件名提交到 Git、日志和默认响应。
- 不做并排比较、标签全文检索和多人实时协作；这些属于 P5/P6 产品增强。

## 4. 验收证据

执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

通过后应将本地 SQLite 恢复到最新迁移：

```powershell
.\apps\api\.venv\Scripts\python.exe -m alembic upgrade head
```

