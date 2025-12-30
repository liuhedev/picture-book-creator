## Context
需要为现有的视频转图片命令行工具添加Web界面，让用户通过浏览器操作，无需命令行知识。

## Goals / Non-Goals
- Goals:
  - 提供简洁的Web界面
  - 支持视频文件上传
  - 参数配置（间隔、阈值）
  - 显示转换进度
  - 下载转换结果
- Non-Goals:
  - 用户认证系统
  - 多用户管理
  - 视频预览功能
  - 图片在线编辑

## Decisions
- Decision: 使用 Flask 作为Web框架
- Alternatives considered:
  - FastAPI: 现代API框架，但需要更多配置
  - Django: 功能完整但过于复杂
  - Flask: 轻量级，适合简单Web应用
- Rationale: Flask简单易用，满足当前需求，学习曲线低

- Decision: 使用原生HTML/CSS/JavaScript构建前端
- Alternatives considered:
  - React/Vue等框架: 功能强大但增加复杂度
  - 原生HTML/CSS/JS: 简单直接，无需构建工具
- Rationale: 保持实现简单，满足基础需求即可

- Decision: 使用服务器端文件处理，异步任务处理转换
- Alternatives considered:
  - 客户端处理: 受浏览器限制，大文件处理困难
  - 服务器端同步处理: 会阻塞请求
  - 服务器端异步处理: 支持大文件，可显示进度
- Rationale: 服务器端处理更可靠，异步任务可提供进度反馈

## Risks / Trade-offs
- 文件上传大小限制 → 设置合理的上传限制（如100MB）
- 并发处理能力 → 单进程处理，后续可扩展
- 文件存储管理 → 临时文件需要清理机制
- 安全性 → 文件类型验证，防止恶意文件上传

## Open Questions
- 进度更新方式（轮询 vs WebSocket，建议：轮询）
- 文件保留时间（建议：转换完成后保留一段时间后自动清理）
