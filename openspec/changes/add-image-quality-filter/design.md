## Context
需要过滤掉转场图片和没有文字的图片，只保留高质量且包含文字的图片用于绘本制作。

## Goals / Non-Goals
- Goals:
  - 检测并过滤转场图片（模糊、低对比度等）
  - 检测图片中是否包含文字
  - 只保留包含文字的图片
  - 在提取过程中实时筛选
- Non-Goals:
  - 图片内容理解
  - 文字识别和提取（仅检测是否存在）
  - 图片质量增强

## Decisions
- Decision: 使用拉普拉斯算子（Laplacian）检测图片清晰度
- Alternatives considered:
  - 方差检测: 简单但不够准确
  - 拉普拉斯算子: 能有效检测模糊图片
  - 频域分析: 准确但计算复杂
- Rationale: 拉普拉斯算子计算快速，能有效识别转场时的模糊图片

- Decision: 使用pytesseract进行文字检测
- Alternatives considered:
  - pytesseract: 成熟稳定，支持多语言
  - paddleocr: 对中文支持更好但依赖更多
  - easyocr: 功能强大但体积较大
- Rationale: pytesseract轻量级，支持中英文检测，满足当前需求

- Decision: 在提取时进行筛选，而非提取后批量处理
- Alternatives considered:
  - 提取后筛选: 需要二次处理，效率低
  - 提取时筛选: 实时过滤，节省存储
- Rationale: 提取时筛选更高效，避免保存无用图片

## Risks / Trade-offs
- OCR检测速度 → 使用快速模式，仅检测文字存在性，不进行完整识别
- 误判风险 → 设置合理的阈值，允许配置调整
- 依赖增加 → pytesseract需要系统安装Tesseract OCR引擎

## Open Questions
- 清晰度阈值（建议：默认100，可配置）
- 文字检测语言（建议：中英文，可配置）
- 是否允许无文字图片（当前需求：不允许）
