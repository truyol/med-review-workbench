# P10 面试交付清单

状态：进行中。自动化结果、独立克隆和人工演示分别判定，不互相替代。

## 交付物与范围

- [x] 公开 GitHub 仓库包含代码、README、PRD、技术设计、运维手册、测试报告、演示脚本、截图、两张非临床合成 PNG 和一份有 CC BY 4.0 署名的心脏参考 STL。
- [x] Git 不含数据库、上传文件、原始 DICOM、题目提供的 STL、`.env`、虚拟环境或 `node_modules`；全新克隆的 seed 会生成非临床 DICOM phantom 并读取心脏参考 STL。
- [x] 面试题能力逐项映射和已知范围差异见 `docs/product/13-delivery-readiness.md`，不把原型说成临床系统。
- [x] 根 README 给出面试官可复制的 Compose 启动、seed 和停止命令。
- [x] 最新完整 P8 门禁：API 29 / 92%、组件 3、Playwright 9、隐私日志扫描 127 行零命中、依赖审计通过，详见 `docs/product/12-p8-test-report.md`。

## P10 实机复核

- [x] 心脏模型入库前，从 GitHub `main` 独立克隆（`--depth 1`），只按当时 README 启动并 seed：隔离栈 `medreview-p10-check`（端口 18082）进入 healthy，seed 得到 1 项目、`DEMO-TAVR-001` 与 PNG/DICOM/STL 三类素材；DICOM 元数据为 `PHANTOM`/64×64，预览 HTTP 200、模型流 HTTP 200。该历史记录中的 STL 是合成曲管，不冒充新模型验证。
- [x] 在独立克隆运行真实后端 Playwright：`7 passed (10.2s)`（Mock 2 + 真实后端 5）。
- [x] 写入一条评审（自定义 `X-Request-ID: p10-persist-check`），重启 API 容器（不加 `-v`）后评审仍在（素材 `accepted`、评审人 `p10-checker`），并在结构化日志中按该 request_id 定位到 `request.completed`（POST 201，12.52ms）。
- [ ] 人工按 `docs/product/06-demo-script.md` 完整走通五分钟路线，包括图片比较、DICOM 白名单、STL 四项操作/结构标记、评审与刷新。
- [ ] 请面试官在其设备上按 README 复现（若尚未发生，不能宣称已完成）。

复核环境：Windows 11 + Docker 29.8.0；克隆与验证栈使用隔离 Compose 项目并在验证后 `down -v` 销毁，未影响正式演示栈。

## 授权与诚实披露

- [x] 当前未添加 `LICENSE`：公开可供面试评估，但不等于授予第三方通用二次使用许可。是否采用 MIT 等许可证由仓库所有者决定。
- [x] 外部 DICOM 与题目 STL 不随 Git 再分发；仅单独入库并署名 CC BY 4.0 心脏参考 STL。默认 DICOM phantom 与 PNG 为工程合成样例，心脏模型不是其病例重建。
- [x] 真实鉴权、持久化审计表、reprocess、标注批量编辑与 PostgreSQL 生产验证尚未实现或完成，见 README 与交付复核文档。

只有上面的实机复核和人工演示完成后，P10 才能标记为“收口完成”。
