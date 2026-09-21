# 运维手册

适用范围：Med Review Workbench 单机演示与面试验收环境。默认使用 Docker Compose、Nginx、FastAPI 和持久化 SQLite 卷。本文不把该配置描述为临床生产系统。

## 1. 部署边界

- Web 只暴露 `http://localhost:8080`；Nginx 提供 SPA fallback，并把 `/api/` 反向代理到 API。
- API 以 UID/GID `10001` 的非 root 用户运行，根文件系统只读；数据库、上传和预览只写入 `/data` 持久卷。
- API 容器启动时自动执行 `alembic upgrade head`，不会自动 seed，避免重启时修改演示数据。
- `.dockerignore` 排除 `.git`、`.env`、虚拟环境、依赖目录、运行数据和样例素材。
- 当前没有真实鉴权、审计表或临床级高可用能力，不得用于真实患者数据。

## 2. 首次部署

前置条件：Docker Desktop 已启动，且 `docker info` 和 `docker compose version` 可执行。

```powershell
docker compose -f .\deploy\docker-compose.yml config
docker compose -f .\deploy\docker-compose.yml up --build -d
docker compose -f .\deploy\docker-compose.yml ps
```

浏览器访问 `http://localhost:8080`。不要直接对外暴露 API 8000 端口。

Compose 首次启动只创建数据库结构，不会隐式写入演示数据。需要五分钟演示数据时，明确执行一次容器内 seed；该命令写入 `/data/medreview.db`，并且可以重复执行：

```powershell
docker compose -f .\deploy\docker-compose.yml exec -T api `
  python -m app.ops.seed_demo --sample-root /sample-data
```

全新克隆无需额外素材下载：缺少本地清理 DICOM/STL 时，seed 会生成非临床 DICOM phantom 与曲管 STL，并使用仓库中的合成 PNG。若需要展示题目给出的真实 STL 或特定开源 DICOM，先按 README 的样例准备步骤放入 `sample-data/`，再对干净演示库 seed；已入库的其他素材不会被 seed 删除。

宿主机开发模式仍使用 `scripts/seed-demo.py` 和 `apps/api/var/medreview.db`。两者用途和数据库路径不同，不能用宿主机 seed 代替容器 seed。

## 3. 健康检查

```powershell
Invoke-RestMethod http://localhost:8080/api/v1/health
Invoke-RestMethod http://localhost:8080/api/v1/health/ready
docker compose -f .\deploy\docker-compose.yml ps
```

- `/health` 只证明进程存活。
- `/health/ready` 同时检查数据库与存储；任何依赖失败应返回 503，Compose 据此判断 API 是否 healthy。
- Web 必须等 API healthy 后启动。

## 4. 日志与 30 秒排障

先从用户错误响应或浏览器 Network 面板取得 `request_id`：

```powershell
docker compose -f .\deploy\docker-compose.yml logs --since 15m api |
  Select-String 'request_id-value'
```

同一 `request_id` 应能串起访问日志与错误日志。建议顺序：

1. 找 `request.completed`，确认 path、status 和 duration。
2. 同 request_id 查 `request.failed`，确认稳定 `error_code`，不要依赖堆栈向用户解释。
3. `docker compose ps` 查看 health；再访问 `/health/ready` 区分数据库与存储问题。
4. 检查 `docker compose logs --tail 200 api web`，确认是 API、Nginx 还是浏览器侧加载失败。

日志不得记录 PatientName、PatientID、原始文件名、请求正文或完整 DICOM 标签。

## 5. SQLite 备份与恢复

宿主机开发数据库备份：

```powershell
.\scripts\backup.ps1 -Mode backup
.\scripts\backup.ps1 -Mode verify -Source .\var\backups\medreview-YYYYMMDD-HHMMSS.db
```

容器卷在线备份，并复制到宿主机形成独立副本：

```powershell
docker compose -f .\deploy\docker-compose.yml exec -T api `
  python -m app.ops.sqlite_backup backup /data/medreview.db /data/backups/medreview-manual.db
New-Item -ItemType Directory -Force .\var\backups | Out-Null
docker compose -f .\deploy\docker-compose.yml cp `
  api:/data/backups/medreview-manual.db .\var\backups\medreview-manual.db
```

恢复会替换目标数据库。先停止 API，并确认备份完整性：

```powershell
docker compose -f .\deploy\docker-compose.yml stop api
docker compose -f .\deploy\docker-compose.yml run --rm api `
  python -m app.ops.sqlite_backup verify /data/backups/medreview-manual.db
docker compose -f .\deploy\docker-compose.yml run --rm api `
  python -m app.ops.sqlite_backup restore /data/backups/medreview-manual.db /data/medreview.db
docker compose -f .\deploy\docker-compose.yml start api
Invoke-RestMethod http://localhost:8080/api/v1/health/ready
```

备份工具使用 SQLite online backup API、恢复前完整性检查和临时文件原子替换。只保存在同一 Docker 卷内不算灾备，必须复制到宿主机或受控备份位置。

## 6. 升级、重启与回滚

升级前先备份，然后：

```powershell
docker compose -f .\deploy\docker-compose.yml build --pull
docker compose -f .\deploy\docker-compose.yml up -d
docker compose -f .\deploy\docker-compose.yml ps
Invoke-RestMethod http://localhost:8080/api/v1/health/ready
```

普通重启不会丢数据，因为 `/data` 使用命名卷。回滚应用版本时应先保留数据库备份，再切换到上一个已验收的源码标签或镜像标签重新部署。Alembic downgrade 只用于已验证的迁移回退，不能替代数据备份。

## 7. PostgreSQL 切换路径与限制

默认 SQLite 镜像不安装 `psycopg`，避免让未启用的数据库驱动增加镜像体积。需要 PostgreSQL 时先构建可选变体：

```powershell
$env:INSTALL_POSTGRES='true'
docker compose -f .\deploy\docker-compose.yml build api
```

随后设置：

```text
APP_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

随后在目标环境执行 `alembic upgrade head` 和 `/health/ready` 检查。现有 UUID 使用 `String(36)`、状态使用字符串、JSON 使用 SQLAlchemy 通用类型，可由 PostgreSQL 承载。

当前限制必须如实说明：Compose 默认不捆绑 PostgreSQL；尚未完成 SQLite 到 PostgreSQL 的在线数据迁移、连接池调优、TLS、凭据托管、PostgreSQL 备份恢复和真实负载验证。因此它是明确的切换路径，不是已完成的生产数据库方案。

## 8. 常见故障

- `docker info` 失败：启动 Docker Desktop，确认当前用户有权访问 Docker engine。
- 拉取基础镜像时 Docker Hub token 超时：这是外部网络/代理问题；不要通过关闭 TLS 校验规避。先逐个验证：

  ```powershell
  docker pull python:3.11-slim
  docker pull node:22-alpine
  docker pull nginxinc/nginx-unprivileged:1.27-alpine
  ```

三个基础镜像均可用后，重新执行 `compose up --build -d`。

- Web 502：检查 API health 和 Alembic 启动日志。
- readiness 503：响应中的 `database`/`storage` 字段会指出依赖；检查 `/data` 卷权限和数据库完整性。
- 8080 被占用：修改 Compose 的宿主机端口，例如 `8081:8080`，容器端口不要变。
- 上传 413：同时核对 `APP_MAX_UPLOAD_MB` 和 Nginx `client_max_body_size`。
- SPA 深链接 404：确认使用本仓库的 Nginx 配置及 `try_files ... /index.html`。

## 9. 停止与清理

```powershell
docker compose -f .\deploy\docker-compose.yml down
```

不要在未备份时执行 `down -v`；`-v` 会删除数据库、上传和预览所在的持久卷。

## 10. 当前验收基线

2026-09-21 已实测：Compose 构建启动、API/Web health、SPA 深链接、容器 seed 幂等、重启及镜像重建后的数据持久性、request_id 日志检索、SQLite 备份和隔离恢复均通过。默认 API 镜像约 406MB；其中主要体积来自 NumPy、Pillow 和压缩 DICOM 解码插件，属于当前题目能力成本。PostgreSQL 驱动只在 `INSTALL_POSTGRES=true` 时加入镜像。
