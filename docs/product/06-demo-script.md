# 五分钟演示脚本

文档状态：Approved for P1  
更新时间：2026-09-20

## 演示目标

证明本项目不是“展示技术栈”，而是解决术前讨论前素材散落、状态不清、结论不可追溯的问题。

## 演示角色

术前规划工程师。

## 演示数据

- 脱敏病例：`DEMO-TAVR-001`
- 图片基线：`sample-data/image/synthetic-cardiac-ct-baseline.png`
- 图片标注对照：`sample-data/image/synthetic-cardiac-ct-annotated.png`
- DICOM 快速验证：`sample-data/dicom/CT_small_anonymized.dcm`
- 心血管多帧 DICOM：`sample-data/dicom/rubo_angiogram_0002/0002_anonymized.DCM`
- 3D 模型：`sample-data/stl/aorta.stl`
- 3D 模型：`sample-data/stl/LA.stl`

## 演示步骤

1. 打开系统，进入 Demo 项目。
2. 创建或打开脱敏病例 `DEMO-TAVR-001`。
3. 关联两张合成 PNG、两份 DICOM 清理副本和两个 STL 到该病例。
4. 浏览图片缩略图，按图片类型/待评审状态筛选，选择基线图和标注图并排比较。
5. 给图片添加标签、状态和备注，证明“整理”结果可保存。
6. 查看 `CT_small_anonymized.dcm` 的安全元数据和缩略图。
7. 查看 Rubo `0002_anonymized.DCM`，说明它是多帧单文件。
8. 打开 `aorta.stl`，进行旋转、缩放、平移和复位。
9. P5 当前不执行结构标记 CRUD；说明标注坐标协议尚未进入本阶段，保留 STL 视角复位和素材评审记录。
10. 将素材评审为“通过”或“需补充”，前端状态映射为 `accepted` / `needs_changes`。
11. 填写评审结论：状态、文本、评审人、时间、下一步。
12. 刷新页面，确认图片整理结果和评审结论仍然存在。

## 讲解重点

- 为什么做：讨论前素材状态不清，结论不可追溯。
- 做到哪：完成工程评审闭环，不进入临床判断。
- 先做什么：先做病例下素材验证和结论保存。
- 怎么验证：五分钟主流程加三条异常流程。

## 不讲或少讲

- 不把重点放在“用了哪些框架”。
- 不承诺诊断、治疗、自动分割或真实医院系统接入。
- 不展示真实患者信息。
