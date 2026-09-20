# DICOM 元数据白名单

文档状态：Approved for P2  
更新时间：2026-09-20

## 目的

只展示能帮助工程评审的低敏字段，避免把患者身份信息、完整标签集合或原始文件内容暴露到界面、日志和测试快照中。

## 初始白名单候选

| DICOM Tag | Keyword | 用途 |
|---|---|---|
| `(0008,0060)` | `Modality` | 判断影像类型，例如 CT/XA/MR |
| `(0028,0010)` | `Rows` | 图像高度 |
| `(0028,0011)` | `Columns` | 图像宽度 |
| `(0028,0008)` | `NumberOfFrames` | 判断单帧或多帧文件 |
| `(0028,0002)` | `SamplesPerPixel` | 预览生成所需基础信息 |
| `(0028,0004)` | `PhotometricInterpretation` | 预览生成所需基础信息 |
| `(0028,0100)` | `BitsAllocated` | 预览生成所需基础信息 |
| `(0028,0101)` | `BitsStored` | 预览生成所需基础信息 |
| `(0028,0102)` | `HighBit` | 预览生成所需基础信息 |
| `(0028,0103)` | `PixelRepresentation` | 预览生成所需基础信息 |
| `(0002,0010)` | `TransferSyntaxUID` | 判断解码方式 |

## 默认禁止展示

- `PatientName`
- `PatientID`
- `PatientBirthDate`
- `PatientSex`
- `InstitutionName`
- `ReferringPhysicianName`
- `StudyDescription`
- `SeriesDescription`
- 原始文件名
- 完整 DICOM tag dump

## P2 决策结论

- **时间字段**：`StudyDate`、`SeriesDate` 默认不展示，避免任何可关联身份的时间线索；如后续需要，必须先定义脱敏策略。
- **`SOPClassUID`**：加入白名单，用于判断 SOP 类别（工程评审需要）。
- **`ImageType`**：暂不加入，MVP 无明确评审用途。
- **前端展示**：使用中文 label，由后端返回 `keyword + label + value`，前端不自行映射。
- **集中定义**：白名单在后端 `media/dicom.py` 集中定义，前端不得直接展示未过滤的 DICOM 元数据。

## 最终白名单

在上述候选基础上新增 `SOPClassUID`，共 12 个字段；其余候选维持。`StudyDate`、`SeriesDate`、`ImageType` 不展示。

## 验收要求

- 单元测试必须覆盖白名单过滤。
- 日志扫描必须确认不包含禁止字段。
- UI 快照不得出现患者身份相关字段。
