# Sample Data Register

最后更新：2026-09-20

示例数据必须记录：数据集/页面名称、来源链接、格式、许可或使用条件、获取日期、使用范围、文件哈希和去标识化说明。

这些素材仅用于本 demo 的解析、预览、3D 查看和评审流程演示，不用于临床。

## DICOM

原始样例和生成的清理副本均默认不进入 Git。应用与演示只使用 `*_anonymized` 清理副本；原始文件仅作为可复现输入。

| 本地文件 | 来源与使用条件 | 获取日期 | 格式/说明 | SHA256 | 去标识化状态与用途 |
|---|---|---|---|---|---|
| `sample-data/dicom/CT_small.dcm` | [pydicom `CT_small.dcm`](https://github.com/pydicom/pydicom/blob/main/src/pydicom/data/test_files/CT_small.dcm)；仓库为 [MIT License](https://github.com/pydicom/pydicom/blob/main/LICENSE)，保留许可说明，仅用于测试 | 2026-09-20 | CT, 128x128, Explicit VR Little Endian | `3DD31E5CC835B3F2CDD46C9DA1982F59251E78518FEFA8163D914631C66437D6` | 原文件含已填充的演示身份标签，禁止直接进入应用或演示 |
| `sample-data/dicom/CT_small_anonymized.dcm` | 由上项通过 `scripts/prepare-dicom-samples.py` 本地生成 | 2026-09-20 | CT 清理副本 | `533A5C9D9F0EEA64B3E420BB0124827189200E25CF54EE850B349EC326EA03D7` | 直接身份标签已清空、私有标签已删除、UID 已确定性替换；用于解析、白名单元数据和缩略图 |
| `sample-data/dicom/rubo_angiogram_0002/0002.DCM` | [Rubo Sample DICOM files](https://www.rubomedical.com/dicom_files/)；页面声明用于 DICOM Viewer 评价，遵循其 [EULA](https://www.rubomedical.com/help/DicomViewer/Html/License_Terms.html)，不随仓库再分发 | 2026-09-20 | XA, 512x512, 96 frames, 多帧单文件 | `EE1FCF71FECB6A8AEE3B1219388CC7DED40A804056A7647674BA1A77B797AE8E` | 原文件含已填充身份标签，禁止直接进入应用或演示 |
| `sample-data/dicom/rubo_angiogram_0002/0002_anonymized.DCM` | 由上项通过 `scripts/prepare-dicom-samples.py` 本地生成；仅作本地评价 | 2026-09-20 | XA 清理副本，96 帧 | `0D0A4FE9E42D3CAF90864EF579735A01475F87AB4594BF01D31399BD62BFF6B3` | 直接身份标签已清空、私有标签已删除、UID 已确定性替换；用于多帧与压缩解码边界演示 |

`prepare-dicom-samples.py` 是 demo 头字段清理工具，不等同于临床级 DICOM 去标识化。它不证明像素中不存在烧录文字；交付前仍需人工检查预览。产品页面仅展示白名单元数据。

## STL

STL 由面试题随 `DEMO SET/stl/` 提供，2026-09-20 复制到本地，仅用于本次面试 Demo 和工程验证，不主张额外授权；文件不进入 Git。

| 文件 | 大小 | SHA256 | 用途 |
|---|---:|---|---|
| `sample-data/stl/aorta.stl` | 3,943,284 bytes | `32F00A98A69178A023ACD845EB9C48F5F7E68FBFF2AC55C4CCECB3CE924513E2` | 主 3D 演示模型 |
| `sample-data/stl/CB.stl` | 4,211,884 bytes | `05CF0329A036CD3BD9E77138203CC8A5A4A8A747789DE6E5E71B45201202B7C2` | 心脏结构模型 |
| `sample-data/stl/LA.stl` | 14,159,984 bytes | `31CEB1904F52E033FC2E285A77E34BFBF1ED64212E0273CF4BE80C6BB37DF847` | 左房模型和加载压力样例 |
| `sample-data/stl/LVOT.stl` | 8,037,084 bytes | `AA737CAEB209133EC191A65564C0306B81C23024883A99D36E25678585EA3EE0` | LVOT 结构模型 |

## Image

图片浏览、筛选、比较、整理和结论沉淀是面试题 Must。下列两张图片由 OpenAI ImageGen 通过 Codex 于 2026-09-20 为本项目生成，明确为合成、非临床素材，不来自患者，也不用于诊断；文件进入 Git 以保证面试项目可复现。

| 文件 | 大小 | SHA256 | 生成说明与用途 |
|---|---:|---|---|
| `sample-data/image/synthetic-cardiac-ct-baseline.png` | 2,057,420 bytes | `F1B4E607B7D5FA41AB3E35AF5F1F085AC380A09A8A263E7CE067EA1B1B2586A5` | 合成灰度心脏 CT 风格基线图；无文字、无标识，用于缩略图浏览和比较左侧 |
| `sample-data/image/synthetic-cardiac-ct-annotated.png` | 1,888,649 bytes | `0109C5D350E202D472EF34B4E57A420E6F46E09B0C71CECA7DAB7507703BB481` | 基于同一合成画面的彩色轮廓和结构点版本；用于比较右侧和标签/状态/备注整理 |

生成提示词要求：合成轴位心脏 CT 风格、非真实患者、无身份信息、无诊断文字；第二张仅增加青色/琥珀色轮廓和结构点。生成过程及人工边界记录见 `docs/engineering/ai-usage.md`。

## 隐私约束

- 不提交真实患者数据。
- 应用和演示不得直接使用含已填充身份标签的原始 DICOM，只能使用清理副本。
- 不在日志中输出 PatientName、PatientID、完整 DICOM 标签集合或原始文件名。
- 页面仅展示白名单 DICOM 元数据。
- 上传文件、数据库、日志和生成预览默认不进入 Git。
