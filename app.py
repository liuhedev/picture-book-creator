#!/usr/bin/env python3
"""
Flask Web应用
提供视频转图片的Web界面
"""
import threading
import uuid
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

from video_to_images import extract_frames, is_page_turn_image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

tasks = {}
tasks_lock = threading.Lock()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def process_video(task_id, video_path, interval, threshold, sharpness_threshold, require_text, text_lang):
    """异步处理视频转换"""
    output_dir = Path(app.config['OUTPUT_FOLDER']) / task_id
    
    def progress_callback(frame_count, total_frames, saved_count, skipped_count, quality_filtered, text_filtered):
        with tasks_lock:
            if task_id in tasks:
                tasks[task_id]['progress'] = {
                    'frame_count': frame_count,
                    'total_frames': total_frames,
                    'saved_count': saved_count,
                    'skipped_count': skipped_count,
                    'quality_filtered': quality_filtered,
                    'text_filtered': text_filtered,
                    'percentage': int((frame_count / total_frames * 100)) if total_frames > 0 else 0
                }
    
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'processing'
        
        result = extract_frames(
            video_path,
            output_dir,
            interval=interval,
            similarity_threshold=threshold,
            progress_callback=progress_callback,
            sharpness_threshold=sharpness_threshold,
            require_text=require_text,
            text_lang=text_lang
        )
        
        with tasks_lock:
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['result'] = result
            tasks[task_id]['output_dir'] = str(output_dir)
    except Exception as e:
        with tasks_lock:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = str(e)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件格式'}), 400
    
    interval = float(request.form.get('interval', 1.0))
    threshold = float(request.form.get('threshold', 0.95))
    sharpness_threshold = float(request.form.get('sharpness', 100))
    require_text = request.form.get('require_text', 'true').lower() == 'true'
    text_lang = request.form.get('text_lang', 'chi_sim+eng')
    
    if interval <= 0 or threshold < 0 or threshold > 1 or sharpness_threshold < 0:
        return jsonify({'error': '参数无效'}), 400
    
    task_id = str(uuid.uuid4())
    upload_dir = Path(app.config['UPLOAD_FOLDER'])
    upload_dir.mkdir(exist_ok=True)
    
    filename = secure_filename(file.filename)
    video_path = upload_dir / f"{task_id}_{filename}"
    file.save(video_path)
    
    with tasks_lock:
        tasks[task_id] = {
            'status': 'pending',
            'progress': None,
            'result': None,
            'error': None
        }
    
    thread = threading.Thread(
        target=process_video,
        args=(task_id, str(video_path), interval, threshold, sharpness_threshold, require_text, text_lang)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'task_id': task_id})


@app.route('/api/status/<task_id>')
def status(task_id):
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id]
        return jsonify({
            'status': task['status'],
            'progress': task['progress'],
            'error': task.get('error'),
            'result': task.get('result')
        })


@app.route('/api/images/<task_id>')
def list_images(task_id):
    """获取任务的所有图片文件列表，包含翻页检测结果"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        if tasks[task_id]['status'] != 'completed':
            return jsonify({'error': '任务未完成'}), 400
        
        output_dir = tasks[task_id].get('output_dir')
        if not output_dir:
            return jsonify({'error': '输出目录不存在'}), 404
    
    output_path = Path(output_dir)
    if not output_path.exists():
        return jsonify({'error': '输出目录不存在'}), 404
    
    image_files = sorted([f.name for f in output_path.glob('*.png')])
    
    # 检测每张图片是否为翻页图片
    image_metadata = []
    page_turn_count = 0
    
    for i, filename in enumerate(image_files):
        image_path = output_path / filename
        prev_path = output_path / image_files[i - 1] if i > 0 else None
        next_path = output_path / image_files[i + 1] if i < len(image_files) - 1 else None
        
        is_page_turn = is_page_turn_image(
            image_path,
            prev_path,
            next_path
        )
        
        if is_page_turn:
            page_turn_count += 1
        
        image_metadata.append({
            'filename': filename,
            'is_page_turn': is_page_turn
        })
    
    return jsonify({
        'images': image_metadata,
        'count': len(image_files),
        'page_turn_count': page_turn_count
    })


@app.route('/api/image/<task_id>/<filename>')
def get_image(task_id, filename):
    """获取图片文件"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        output_dir = tasks[task_id].get('output_dir')
        if not output_dir:
            return jsonify({'error': '输出目录不存在'}), 404
    
    output_path = Path(output_dir)
    image_path = output_path / filename
    
    if not image_path.exists() or not image_path.is_file():
        return jsonify({'error': '图片不存在'}), 404
    
    return send_from_directory(str(output_path), filename)


@app.route('/api/download/<task_id>', methods=['POST'])
def download(task_id):
    """下载选中的图片"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        if tasks[task_id]['status'] != 'completed':
            return jsonify({'error': '任务未完成'}), 400
        
        output_dir = tasks[task_id].get('output_dir')
        if not output_dir:
            return jsonify({'error': '输出目录不存在'}), 404
    
    output_path = Path(output_dir)
    if not output_path.exists():
        return jsonify({'error': '输出目录不存在'}), 404
    
    selected_files = request.json.get('files', [])
    
    if not selected_files:
        return jsonify({'error': '请至少选择一张图片'}), 400
    
    zip_path = Path(app.config['OUTPUT_FOLDER']) / f"{task_id}_selected.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in selected_files:
            file_path = output_path / filename
            if file_path.exists() and file_path.is_file():
                zipf.write(file_path, filename)
    
    return send_file(
        str(zip_path),
        as_attachment=True,
        download_name=f'frames_selected_{task_id}.zip',
        mimetype='application/zip'
    )


if __name__ == '__main__':
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5001)
