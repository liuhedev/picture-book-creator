#!/usr/bin/env python3
"""
视频转图片工具
从视频文件中提取图片帧，支持去重功能
"""
import argparse
import sys
from pathlib import Path

import cv2
import pytesseract
from skimage.metrics import structural_similarity as ssim


def calculate_ssim(img1, img2):
    """计算两张图片的结构相似性指数"""
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    if len(img1.shape) == 3:
        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        img1_gray = img1
        img2_gray = img2
    
    return ssim(img1_gray, img2_gray)


def check_image_sharpness(frame, threshold=100, contrast_threshold=20):
    """
    检测图片清晰度和对比度，过滤转场图片
    
    Args:
        frame: 图片帧（BGR格式）
        threshold: 清晰度阈值（拉普拉斯方差），默认100
        contrast_threshold: 对比度阈值（标准差），默认20
    
    Returns:
        bool: True表示质量足够，False表示质量差（转场图片）
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 清晰度检测（拉普拉斯算子）
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_ok = laplacian_var >= threshold
    
    # 对比度检测（标准差）
    contrast = gray.std()
    contrast_ok = contrast >= contrast_threshold
    
    return sharpness_ok and contrast_ok


def has_text(frame, lang='chi_sim+eng'):
    """
    检测图片中是否包含文字
    
    Args:
        frame: 图片帧（BGR格式）
        lang: OCR语言，默认中英文
    
    Returns:
        bool: True表示包含文字，False表示无文字
    """
    try:
        text = pytesseract.image_to_string(frame, lang=lang, config='--psm 6')
        return len(text.strip()) > 0
    except Exception:
        return False


def extract_frames(video_path, output_dir, interval=1.0, similarity_threshold=0.95, 
                   progress_callback=None, sharpness_threshold=150, contrast_threshold=20, require_text=True, text_lang='chi_sim+eng'):
    """
    从视频中提取帧并保存为图片
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        interval: 提取间隔（秒）
        similarity_threshold: 相似度阈值，超过此值则跳过
        progress_callback: 进度回调函数，接收 (frame_count, total_frames, saved_count, skipped_count, quality_filtered, text_filtered) 参数
        sharpness_threshold: 清晰度阈值，默认150
        contrast_threshold: 对比度阈值，默认20
        require_text: 是否要求包含文字，默认True
        text_lang: OCR语言，默认中英文
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_interval = int(fps * interval)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    saved_frames = []
    frame_count = 0
    saved_count = 0
    skipped_count = 0
    quality_filtered = 0
    text_filtered = 0
    
    if progress_callback is None:
        print(f"视频信息: {total_frames} 帧, {fps:.2f} FPS")
        print(f"提取间隔: {interval} 秒 ({frame_interval} 帧)")
        print(f"相似度阈值: {similarity_threshold}")
        print(f"清晰度阈值: {sharpness_threshold}")
        print(f"文字检测: {'启用' if require_text else '禁用'}")
        print("开始提取...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            is_similar = False
            
            for saved_frame in saved_frames:
                similarity = calculate_ssim(frame, saved_frame)
                if similarity >= similarity_threshold:
                    is_similar = True
                    skipped_count += 1
                    if progress_callback is None:
                        print(f"帧 {frame_count}: 相似度 {similarity:.3f}, 跳过")
                    break
            
            if not is_similar:
                quality_ok = check_image_sharpness(frame, sharpness_threshold, contrast_threshold)
                if not quality_ok:
                    quality_filtered += 1
                    if progress_callback is None:
                        print(f"帧 {frame_count}: 清晰度不足, 跳过")
                else:
                    has_text_content = True
                    if require_text:
                        has_text_content = has_text(frame, text_lang)
                        if not has_text_content:
                            text_filtered += 1
                            if progress_callback is None:
                                print(f"帧 {frame_count}: 未检测到文字, 跳过")
                    
                    if has_text_content:
                        filename = output_dir / f"frame_{saved_count + 1:04d}.png"
                        cv2.imwrite(str(filename), frame)
                        saved_frames.append(frame.copy())
                        saved_count += 1
                        if progress_callback is None:
                            print(f"帧 {frame_count}: 已保存 -> {filename.name}")
        
        frame_count += 1
        
        if progress_callback and frame_count % 10 == 0:
            progress_callback(frame_count, total_frames, saved_count, skipped_count, quality_filtered, text_filtered)
    
    cap.release()
    
    if progress_callback:
        progress_callback(frame_count, total_frames, saved_count, skipped_count, quality_filtered, text_filtered)
    else:
        print(f"\n提取完成:")
        print(f"  总帧数: {frame_count}")
        print(f"  保存图片: {saved_count}")
        print(f"  跳过相似: {skipped_count}")
        print(f"  质量过滤: {quality_filtered}")
        print(f"  文字过滤: {text_filtered}")
        print(f"  输出目录: {output_dir}")
    
    return {
        'total_frames': frame_count,
        'saved_count': saved_count,
        'skipped_count': skipped_count,
        'quality_filtered': quality_filtered,
        'text_filtered': text_filtered,
        'output_dir': str(output_dir)
    }


def main():
    parser = argparse.ArgumentParser(description="视频转图片工具")
    parser.add_argument("video", help="视频文件路径")
    parser.add_argument("-o", "--output", default="output", help="输出目录（默认: output）")
    parser.add_argument("-i", "--interval", type=float, default=1.0, help="提取间隔（秒，默认: 1.0）")
    parser.add_argument("-t", "--threshold", type=float, default=0.95, help="相似度阈值（默认: 0.95）")
    parser.add_argument("-s", "--sharpness", type=float, default=150, help="清晰度阈值（默认: 150）")
    parser.add_argument("-c", "--contrast", type=float, default=20, help="对比度阈值（默认: 20）")
    parser.add_argument("--no-text", action="store_true", help="不要求包含文字")
    parser.add_argument("--text-lang", default="chi_sim+eng", help="OCR语言（默认: chi_sim+eng）")
    
    args = parser.parse_args()
    
    try:
        extract_frames(
            args.video,
            args.output,
            interval=args.interval,
            similarity_threshold=args.threshold,
            sharpness_threshold=args.sharpness,
            require_text=not args.no_text,
            text_lang=args.text_lang
        )
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
