# DICOM 元数据白名单

文档状态：当前运行时契约（2026-09-21）。唯一实现来源是 `apps/api/app/services/asset_processing.py` 中的 `DICOM_METADATA_ALLOWLIST`；早期 P2 的“12 字段最终白名单”是**未落地的历史提案**，不能用于介绍当前 API。

## 目的与当前响应

只返回工程评审所需的有限字段，不把患者身份信息、自由文本描述、完整标签集合或原始文件名送到页面和日志。当前字段位于素材响应的 `metadata_summary` 对象中，键名是下表的 `snake_case`；前端直接展示键和值。**没有**单独的 DICOM 元数据接口，也没有后端返回的 `keyword + label + value` 三元组。

| DICOM 字段 | 响应键 | 用途 |
|---|---|---|
| `Modality` | `modality` | 影像模态，如 CT/XA |
| `BodyPartExamined` | `body_part_examined` | 检查部位；演示 phantom 为 `PHANTOM` |
| `SOPClassUID` | `sop_class_uid` | SOP 类别 |
| `Rows` | `rows` | 图像行数 |
| `Columns` | `columns` | 图像列数 |
| `NumberOfFrames` | `number_of_frames` | 单文件多帧数量，字段存在时才返回 |

当前总数是 **6 个候选键**，不是保证每份文件都返回 6 项；未存在的标签不补造。像素可用时生成单张 PNG 缩略图；无 `PixelData` 或解码失败时保留已取出的白名单元数据，在 `ingest_warnings` 说明预览不可用。该行为不是完整 DICOM 阅片，也不表示素材已通过临床级脱敏。

## 明确不展示

`PatientName`、`PatientID`、`PatientBirthDate`、`InstitutionName`、`ReferringPhysicianName`、`StudyDescription`、`SeriesDescription`、`StudyDate`、`SeriesDate`、`ImageType`、传输语法细节、完整 DICOM 标签转储及原始文件名均不在展示白名单。`StudyDescription`/`SeriesDescription` 等自由文本可能携带身份或临床信息。解析器检测到 `PatientName` 或 `PatientID` 时只写通用警告，不把值写入响应或日志。

## P2 提案与当前实现的差异

P2 曾考虑 `SamplesPerPixel`、`PhotometricInterpretation`、`BitsAllocated`、`BitsStored`、`HighBit`、`PixelRepresentation`、`TransferSyntaxUID` 等解析辅助字段，并设想由后端返回中文 label。P4 隐私复核后把展示集合收紧为上表 6 项；辅助字段即使被解析用于像素处理，也不因此进入公开响应。今后新增字段必须同时修改代码、测试和本文，并复核自由文本与身份关联风险。

## 验收边界

- API 测试验证只返回白名单键，并且不泄露 `PatientName`、`PatientID`。
- 日志扫描验证请求记录不包含患者身份值、原始文件名或完整标签集合。
- 本地 DICOM 清理脚本只处理已知标签和 UID；像素烧录文字需要人工检查，不能用“白名单展示”代替去标识化认证。
