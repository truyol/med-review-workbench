# 技术架构（P2 输入草案）

文档状态：Superseded by `TECH_DESIGN.md`（保留为 P2 输入记录）。  
说明：P2 的完整技术设计见仓库根目录 [`TECH_DESIGN.md`](../../TECH_DESIGN.md)，本文仅保留早期架构想法作为背景。

## 决策原则

- 单仓库、模块化单体，优先交付完整闭环。
- 本地优先，核心流程不得依赖第三方 API。
- 文件内容与元数据分离；数据库不保存大文件。
- 先 SQLite 和本地存储，通过接口抽象保留 PostgreSQL/对象存储替换能力。

## 组件

```text
React + TypeScript
  ├─ 项目/案例/素材/评审功能
  ├─ Three.js STL Viewer
  └─ API client + request ID
           │ REST /api/v1
FastAPI
  ├─ API routes
  ├─ services（业务规则）
  ├─ repositories（数据访问）
  ├─ pydicom parser / preview generator
  ├─ storage service
  └─ structured logging
           ├─ SQLite（开发）
           └─ var/uploads + var/previews
```

## 技术选择

- Web：React、TypeScript、Vite、Ant Design、TanStack Query、Zod。
- 3D：Three.js、React Three Fiber、Drei；STLLoader 来自 Three.js examples。
- API：FastAPI、Pydantic、SQLAlchemy、Alembic。
- 医学影像：pydicom、NumPy、Pillow。
- 日志：structlog；所有请求生成或透传 request ID。
- 测试：pytest、Vitest、Testing Library、Playwright。

## 暂不引入

Cornerstone/OHIF、Redux、Celery、Redis、WebSocket、微服务、Kubernetes 和大模型 SDK。
