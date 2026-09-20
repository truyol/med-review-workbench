# P0 环境准备记录

最后更新：2026-09-20

## 项目根目录

仓库根目录（克隆位置由开发者自行选择）

VS Code 已打开该目录。后续所有代码、文档、测试和交付材料均以该目录为准。

## 已确认工具

| 项目 | 状态 | 版本/说明 |
|---|---|---|
| VS Code | 已安装 | 1.138.0，路径 `D:\app\Microsoft VS Code\bin\code.cmd` |
| Node.js | 已安装 | v24.14.0 |
| npm | 已安装 | 11.18.0 |
| Python | 已安装 | 3.11.9 |
| pip | 已安装 | 24.0 |
| Git | 已安装 | 2.53.0.windows.2 |
| Docker | 暂缺 | P7 运维化阶段处理，当前不阻塞 P0-P6 |

## 已安装 VS Code 扩展

| 扩展 | 状态 |
|---|---|
| `ms-python.python` | 已安装 |
| `charliermarsh.ruff` | 已安装 |
| `dbaeumer.vscode-eslint` | 已安装 |
| `esbenp.prettier-vscode` | 已安装 |
| `ms-playwright.playwright` | 已安装 |

## 待重试 VS Code 扩展

| 扩展 | 当前状态 | 处理方式 |
|---|---|---|
| `openai.chatgpt` | Marketplace 安装长时间无响应 | 保留在 `.vscode/extensions.json`，可在 VS Code 扩展面板重试 |
| `ms-python.vscode-pylance` | Marketplace 安装长时间无响应 | 不影响后端依赖安装，后续重试 |
| `ms-azuretools.vscode-docker` | Marketplace 返回 aborted | P7 前重试即可 |
| `qwtel.sqlite-viewer` | Marketplace 安装长时间无响应 | 可选工具，不阻塞；FastAPI/SQLite 开发仍可继续 |

## 后端依赖

后端虚拟环境位于 `apps/api/.venv`。已完成 `pip install -e ".[dev]"`，并验证以下核心包可导入：

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- pydicom
- NumPy
- Pillow
- pytest

## 前端依赖

前端依赖位于 `apps/web/node_modules`，锁文件为 `apps/web/package-lock.json`。当前核心栈：

- React 19.2
- TypeScript
- Vite
- Ant Design
- React Router
- TanStack Query
- Three.js
- React Three Fiber
- Drei
- Vitest
- Playwright

## 应用推荐

当前阶段推荐组合：

- IDE：VS Code。
- AI 协作：Codex 桌面端继续作为主控；VS Code 的 OpenAI/Codex 扩展待 Marketplace 稳定后补装。
- API 调试：优先用 FastAPI 自带 Swagger/ReDoc；暂不强依赖 Postman。
- 数据库查看：开发期 SQLite，SQLite Viewer 可选；生产切 PostgreSQL 只写入设计与部署路径。
- 浏览器：Edge 或 Chrome，用于前端调试和 Playwright。
- 容器：Docker Desktop + WSL2 放到 P7 运维化阶段统一处理。

## P0 结论

P0 环境准备已满足进入 P1 的条件：项目目录已固定、Git 已初始化、前后端依赖已安装、VS Code 可打开项目、缺失项已有阶段归属和处理方式。
