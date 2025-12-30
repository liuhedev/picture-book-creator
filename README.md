# 视频转图片工具 (Picture Book Creator)

这是一个基于 Python 和 Flask 的 Web 应用，旨在帮助用户高效地将视频文件转换为高质量的图片序列。它特别适合用于制作绘本、提取幻灯片或从视频中获取关键素材。

## 核心功能

- **智能去重**：利用 SSIM (结构相似性) 算法，自动跳过重复或高度相似的帧，减少冗余。
- **质量过滤**：内置清晰度检测（基于拉普拉斯方差），自动剔除模糊不清的图片。
- **文字检测**：集成 Tesseract OCR，支持只保留包含文字的画面（可选），非常适合提取 PPT 或字幕内容。
- **Web 界面**：提供直观的上传、参数配置、进度展示和预览界面。
- **一键打包**：处理完成后，支持一键下载所有图片的 ZIP 压缩包。

## 技术栈

- **后端**: Python 3, Flask
- **图像处理**: OpenCV, scikit-image, Pillow
- **OCR**: Tesseract
- **前端**: HTML5, CSS3, JavaScript

## 安装指南

### 前置要求

1.  **Python 3.8+**
2.  **Tesseract OCR 引擎**:
    *   **macOS**: `brew install tesseract`
    *   **Windows**: 下载并安装 [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki)，并确保添加到系统 PATH。
    *   **Linux**: `sudo apt-get install tesseract-ocr`

### 安装步骤

1.  克隆项目：
    ```bash
    git clone <repository_url>
    cd picture-book-creator
    ```

2.  创建并激活虚拟环境：
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

3.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

### 启动 Web 服务

```bash
python app.py
```

服务启动后，访问浏览器打开 `http://localhost:5001`。

### 界面操作

1.  **上传视频**：点击选择文件上传 MP4, AVI, MOV 等常见格式视频。
2.  **设置参数**：
    *   **提取间隔**：每隔多少秒提取一帧（默认 1.0秒）。
    *   **相似度阈值**：范围 0-1。数值越大去重越严格（默认 0.95）。
    *   **清晰度阈值**：数值越大要求越清晰（默认 100）。
    *   **文字检测**：勾选后仅保留包含文字的图片。
3.  **开始转换**：点击按钮开始处理，页面会实时显示进度。
4.  **预览与下载**：处理完成后预览生成的图片，点击“下载 ZIP”获取打包文件。

### 命令行工具

你也可以直接使用命令行脚本进行批量处理：

```bash
python video_to_images.py input_video.mp4 -o output_dir -i 1.0 -t 0.95
```

参数说明：
- `-o`: 输出目录
- `-i`: 提取间隔（秒）
- `-t`: 相似度阈值
- `-s`: 清晰度阈值
- `--no-text`: 关闭文字检测

## 目录结构

```
.
├── app.py                  # Flask Web 应用入口
├── video_to_images.py      # 核心视频处理脚本
├── requirements.txt        # 项目依赖
├── templates/              # HTML 模板
├── static/                 # 静态资源 (CSS, JS)
├── uploads/                # (自动生成) 临时上传目录
└── outputs/                # (自动生成) 处理结果目录
```

## 注意事项

- OCR 功能依赖于本地 Tesseract 安装，如果未安装 Tesseract，文字检测功能可能无法正常工作。
- 任务状态存储在内存中，重启服务会丢失当前的进度信息。
