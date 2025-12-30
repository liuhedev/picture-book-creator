# video-to-image-conversion Specification

## Purpose
TBD - created by archiving change add-video-to-image-conversion. Update Purpose after archive.
## Requirements
### Requirement: 视频转图片转换
系统必须（MUST）能够从视频文件中提取图片帧并保存为PNG格式图片文件。

#### Scenario: 按时间间隔提取帧
- **WHEN** 用户提供视频文件和时间间隔参数
- **THEN** 系统按指定间隔提取视频帧
- **AND** 将提取的帧保存为PNG格式图片文件
- **AND** 图片文件名包含帧序号（如 frame_0001.png, frame_0002.png）

#### Scenario: 处理视频文件
- **WHEN** 用户提供支持的视频格式文件（如MP4）
- **THEN** 系统能够读取并解析视频文件
- **AND** 提取视频中的帧数据

#### Scenario: 输出图片文件
- **WHEN** 视频帧提取完成
- **THEN** 系统将每帧保存为独立的PNG文件
- **AND** 图片文件保存在指定输出目录
- **AND** 图片保持原始分辨率或按配置调整

#### Scenario: 命令行接口
- **WHEN** 用户通过命令行调用转换工具
- **THEN** 系统接受视频文件路径和输出目录参数
- **AND** 执行转换并显示进度信息
- **AND** 转换完成后显示输出文件信息

#### Scenario: 去重相似帧
- **WHEN** 提取的帧与已保存的帧相似度超过阈值
- **THEN** 系统跳过保存该帧
- **AND** 仅保存与已有帧差异明显的帧
- **AND** 避免输出重复或高度相似的图片

