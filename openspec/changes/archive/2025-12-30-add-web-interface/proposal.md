# Change: 添加Web可视化界面

## Why
当前只有命令行工具，需要提供Web界面让用户通过浏览器直接操作视频转图片功能，提升易用性。

## What Changes
- 新增Web服务器和前端界面
- 支持视频文件上传
- 提供参数配置界面（提取间隔、相似度阈值）
- 显示转换进度和结果
- 支持下载转换后的图片

## Impact
- 新增能力：`web-interface`
- 新增代码：Web服务器（Flask/FastAPI）、前端页面（HTML/CSS/JavaScript）
- 依赖：Web框架、文件上传处理库
- 修改：复用现有 `video_to_images.py` 核心功能
