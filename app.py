#!/usr/bin/env python3
"""
Flask Web应用
提供视频转图片的Web界面
"""
import threading
import uuid
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

from video_to_images import extract_frames

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['ALLOWED_EXTENSIONS'] = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}

tasks = {}
tasks_lock = threading.Lock()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def process_video(task_id, video_path, interval, threshold, sharpness_threshold, contrast_threshold, require_text, text_lang):
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
            contrast_threshold=contrast_threshold,
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
    sharpness_threshold = float(request.form.get('sharpness', 150))
    contrast_threshold = float(request.form.get('contrast', 20))
    require_text = request.form.get('require_text', 'true').lower() == 'true'
    text_lang = request.form.get('text_lang', 'chi_sim+eng')
    
    if interval <= 0 or threshold < 0 or threshold > 1 or sharpness_threshold < 0 or contrast_threshold < 0:
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
        args=(task_id, str(video_path), interval, threshold, sharpness_threshold, contrast_threshold, require_text, text_lang)
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


@app.route('/api/download/<task_id>')
def download(task_id):
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
    
    zip_path = Path(app.config['OUTPUT_FOLDER']) / f"{task_id}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in output_path.glob('*.png'):
            zipf.write(file_path, file_path.name)
    
    return send_file(
        str(zip_path),
        as_attachment=True,
        download_name=f'frames_{task_id}.zip',
        mimetype='application/zip'
    )


if __name__ == '__main__':
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5001)
