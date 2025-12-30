# Project Context

## Purpose
视频转图片工具 (Picture Book Creator) 是一个 Web 应用，用于将视频文件自动转换为高质量的图片序列。核心功能包括从视频中提取关键帧，并通过智能算法进行去重（基于相似度）和质量过滤（基于清晰度），特别针对包含文字的画面进行优化。

## Tech Stack
- **Backend**: Python 3, Flask
- **Video Processing**: OpenCV (cv2)
- **Image Analysis**: scikit-image (SSIM), pytesseract (OCR)
- **Frontend**: HTML5, CSS3, JavaScript (原生)

## Project Conventions

### Code Style
- Python 代码遵循 PEP 8 规范。
- 使用 docstrings 描述函数功能、参数和返回值。
- 变量命名使用 snake_case。

### Architecture Patterns
- **Web Server**: Flask 应用作为入口 (`app.py`)。
- **Task Management**: 使用 `threading` 进行简单的异步任务处理，使用内存字典 `tasks` 存储任务状态（非持久化）。
- **File Structure**:
    - `app.py`: Web 服务器和 API 路由。
    - `video_to_images.py`: 核心视频处理逻辑。
    - `templates/`: Jinja2 HTML 模板。
    - `static/`: CSS, JS, 和其他静态资源。
    - `uploads/`: 临时存储上传的视频文件。
    - `outputs/`: 存储处理生成的图片。

### Git Workflow
- 分支管理：`master` 为主分支。
- 提交信息：遵循 Conventional Commits (`type(scope): subject`)。

## Domain Context
- **SSIM (Structural Similarity)**: 用于衡量两张图片的相似度（0-1）。用于去重，阈值越高保留越少。
- **Laplacian Variance**: 用于衡量图片清晰度。用于过滤模糊图片，阈值越高要求越清晰。
- **OCR (Optical Character Recognition)**: 使用 Tesseract 识别图片中的文字，可配置是否仅保留包含文字的帧。

## Important Constraints
- **Tesseract OCR**: 需要在部署环境中安装 Tesseract 引擎。
- **Concurrency**: 目前使用内存存储任务状态，服务重启会丢失进度；适合单实例部署。

## External Dependencies
- `tesseract`: OCR 引擎
