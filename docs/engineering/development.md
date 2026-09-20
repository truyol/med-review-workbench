# 开发规范

## 工作方式

采用垂直切片开发，每一项同时包含 UI、API、数据、错误、测试、文档和演示证据。

项目严格遵循：

`P0 环境准备 → P1 产品设计 → P2 技术设计 → P3 脚手架 → P4 后端 → P5 前端 → P6 异常/边界 → P7 运维化 → P8 测试 → P9 文档 → P10 交付验收`

具体阶段门禁见 `docs/PROJECT_LIFECYCLE.md`。功能开发内部继续采用可演示的垂直切片，避免把某一层全部写完后才联调。

## 提交门禁

- 变化关联需求编号或说明基础设施目的。
- `powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1` 通过。
- 数据库可从空库迁移。
- 无密钥、数据库、上传文件、预览或日志进入 Git。
- 文档与实际行为同步。

## 常用命令

后端：

```powershell
cd apps/api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
.\.venv\Scripts\python.exe -m alembic upgrade head
```

前端：

```powershell
cd apps/web
npm.cmd run dev
npm.cmd run lint
npm.cmd run test
npm.cmd run build
```

统一检查：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

## Windows 约定

- PowerShell ExecutionPolicy 当前限制 `.ps1` 命令代理；调用 npm/npx 时使用 `npm.cmd` 和 `npx.cmd`。
- Python 仅使用 `apps/api/.venv`，不污染全局环境。
- VS Code Tasks 调用仓库脚本，避免维护两套命令。
