# P7 运维化验收

状态：收口完成（2026-09-21）

## 已有证据

- [x] API 多阶段镜像、非 root 用户、只读根文件系统设计。
- [x] Web 多阶段镜像、Nginx SPA fallback、`/api` 反向代理与 request_id 透传。
- [x] Compose 持久卷、API readiness healthcheck、Web healthcheck、重启策略。
- [x] `.dockerignore` 排除密钥、依赖、运行数据、Git 与样例数据。
- [x] SQLite 备份、恢复、完整性检查实现及自动化 round-trip 测试。
- [x] 容器内显式 seed 命令使用 `/data/medreview.db`，并有独立数据库、幂等执行测试。
- [x] PostgreSQL 驱动改为可选镜像构建项；默认 SQLite 镜像不承担未启用驱动的体积。
- [x] Nginx 同源访问下关闭容器 CORS 白名单，避免保留无效开放项。
- [x] 运维手册覆盖部署、健康检查、日志排障、备份恢复、升级回滚和 PostgreSQL 边界。
- [x] `docker compose config` 静态解析通过。

## 运行验收证据

- [x] Python、Node、Nginx 基础镜像拉取成功，API/Web 镜像实际构建成功。
- [x] `docker compose up --build -d` 成功；API 和 Web 均进入 healthy 状态。
- [x] `/api/v1/health/ready` 返回数据库、存储均为 `ok`。
- [x] Nginx 深链接返回 200 和 SPA 根节点；API 只通过 `/api` 反向代理访问。
- [x] 容器 seed 连续执行返回相同项目/病例 ID；容器重启和 API 镜像重建后数据仍存在。
- [x] 自定义 `X-Request-ID` 原样返回，并能在结构化 `request.completed` 日志中定位。
- [x] 容器内 SQLite backup、隔离 restore 和 integrity check 实际执行通过。
- [x] 默认镜像未安装 `psycopg`；API 镜像由约 564MB 降至约 406MB，保留压缩 DICOM 解码依赖。
- [x] 未授权 Origin 不返回 `Access-Control-Allow-Origin`。

P7 已满足面试题的部署、健康检查、持久化、日志排障、备份恢复和运维说明门禁。PostgreSQL 仍是明确的可选切换路径，不声称已经完成生产负载验证。
