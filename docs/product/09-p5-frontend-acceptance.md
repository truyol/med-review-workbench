# P5 前端验收清单

状态：收口完成（主流程与优化项已验证）

## 已完成

- [x] `/projects` 项目列表、新建项目、空状态和加载失败重试
- [x] `/projects/:projectId` 病例列表与新建病例
- [x] `/cases/:caseId` 评审看板、素材上传、状态和最新评审摘要
- [x] `/assets/:assetId?caseId=...` 素材详情与评审表单
- [x] 图片预览通过后端 `/preview`；DICOM 无预览时展示白名单元数据和降级提示
- [x] STL 通过 `/model` 加载，支持旋转、缩放、平移
- [x] 评审成功后 Query 缓存失效刷新，状态回到看板
- [x] API 错误展示 `message + next_action`
- [x] 前端 lint、Vitest、TypeScript build 通过

## 明确不在本轮

- [ ] 标签全文检索、并排比较、多人实时协作
- [ ] 标注 CRUD（等待 2D/3D 坐标协议确认）
- [ ] 真实登录、权限控制和审计表
- [ ] 临床阅片器、诊断或治疗建议

## P5 下一步

- [x] Playwright 主流程：项目 → 病例 → 上传 → 详情 → 看板
- [x] Playwright API 失败可恢复提示验证
- [x] STL 查看器加载态、视角复位；图片预览不可用和上传错误沿用后端稳定错误提示
- [x] 将 STL/Three.js viewer 动态拆包，首屏主包从约 1.84MB 降至约 0.93MB
- [x] `scripts/seed-demo.py` 补充可复现的 seed/demo 数据入口

Playwright 主流程和异常流程已在本机 Chrome 通道执行通过（2 passed）。配置使用 `channel: "chrome"`，不依赖 Playwright 自带 Chromium 下载。
