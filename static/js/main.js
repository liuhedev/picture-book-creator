const uploadForm = document.getElementById('uploadForm');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const progressFill = document.getElementById('progressFill');
const progressInfo = document.getElementById('progressInfo');
const statusDiv = document.getElementById('status');
const resultInfo = document.getElementById('resultInfo');
const downloadLink = document.getElementById('downloadLink');
const errorMessage = document.getElementById('errorMessage');
const submitBtn = document.getElementById('submitBtn');

let currentTaskId = null;
let statusInterval = null;

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(uploadForm);
    
    const requireText = document.getElementById('require_text').checked;
    formData.append('require_text', requireText.toString());
    
    try {
        submitBtn.disabled = true;
        submitBtn.textContent = '上传中...';
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '上传失败');
        }
        
        currentTaskId = data.task_id;
        progressSection.style.display = 'block';
        resultSection.style.display = 'none';
        errorSection.style.display = 'none';
        
        startStatusPolling();
    } catch (error) {
        showError(error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = '开始转换';
    }
});

function startStatusPolling() {
    if (statusInterval) {
        clearInterval(statusInterval);
    }
    
    statusInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentTaskId}`);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || '查询状态失败');
            }
            
            updateProgress(data);
            
            if (data.status === 'completed') {
                clearInterval(statusInterval);
                showResult(data);
            } else if (data.status === 'error') {
                clearInterval(statusInterval);
                showError(data.error || '转换失败');
            }
        } catch (error) {
            clearInterval(statusInterval);
            showError(error.message);
        }
    }, 1000);
}

function updateProgress(data) {
    if (data.progress) {
        const progress = data.progress;
        const percentage = progress.percentage || 0;
        
        progressFill.style.width = percentage + '%';
        progressFill.textContent = percentage + '%';
        
        let infoText = `已处理: ${progress.frame_count}/${progress.total_frames} 帧 | 已保存: ${progress.saved_count} 张 | 跳过相似: ${progress.skipped_count} 张`;
        if (progress.quality_filtered !== undefined) {
            infoText += ` | 质量过滤: ${progress.quality_filtered} 张`;
        }
        if (progress.text_filtered !== undefined) {
            infoText += ` | 文字过滤: ${progress.text_filtered} 张`;
        }
        progressInfo.textContent = infoText;
        
        if (data.status === 'processing') {
            statusDiv.textContent = '正在转换...';
        } else if (data.status === 'pending') {
            statusDiv.textContent = '等待开始...';
        }
    }
}

function showResult(data) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    
    if (data.result) {
        let resultHtml = `
            <p><strong>总帧数:</strong> ${data.result.total_frames}</p>
            <p><strong>保存图片:</strong> ${data.result.saved_count} 张</p>
            <p><strong>跳过相似:</strong> ${data.result.skipped_count} 张</p>
        `;
        if (data.result.quality_filtered !== undefined) {
            resultHtml += `<p><strong>质量过滤:</strong> ${data.result.quality_filtered} 张</p>`;
        }
        if (data.result.text_filtered !== undefined) {
            resultHtml += `<p><strong>文字过滤:</strong> ${data.result.text_filtered} 张</p>`;
        }
        resultInfo.innerHTML = resultHtml;
    }
    
    downloadLink.href = `/api/download/${currentTaskId}`;
    downloadLink.download = `frames_${currentTaskId}.zip`;
    
    submitBtn.disabled = false;
    submitBtn.textContent = '开始转换';
}

function showError(message) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    
    submitBtn.disabled = false;
    submitBtn.textContent = '开始转换';
}
