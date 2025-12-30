## Context
需要实现视频转图片功能，用于提取视频帧并保存为图片文件，供打印绘本使用。

## Goals / Non-Goals
- Goals:
  - 支持常见视频格式（MP4等）
  - 按时间间隔提取帧
  - 输出高质量PNG图片
  - 命令行工具接口
- Non-Goals:
  - 视频编辑功能
  - 图片后处理（裁剪、滤镜等）
  - GUI界面

## Decisions
- Decision: 使用 opencv-python 作为视频处理库
- Alternatives considered:
  - ffmpeg-python: 功能强大但API较复杂
  - opencv-python: 简单易用，适合基础帧提取需求
- Rationale: opencv-python 提供简洁的API，满足当前需求，学习曲线低

- Decision: 使用结构相似性指数（SSIM）进行帧去重
- Alternatives considered:
  - 感知哈希（pHash）: 计算快速但可能误判
  - 直方图比较: 简单但不够准确
  - SSIM: 更准确反映图像结构相似性
- Rationale: SSIM能更好地识别视觉上相似的帧，适合绘本打印场景，避免重复图片

## Risks / Trade-offs
- 视频格式兼容性 → 使用 opencv-python 支持常见格式
- 大视频文件内存占用 → 流式处理，逐帧读取
- 输出图片质量 → 使用PNG无损格式
- 相似度阈值设置 → 默认0.95（可配置），平衡去重效果和保留关键帧

## Open Questions
- 默认提取间隔时间（建议：1秒或可配置）
- 输出图片尺寸（建议：保持原始分辨率或可配置）
- 相似度阈值（建议：0.95，可配置）