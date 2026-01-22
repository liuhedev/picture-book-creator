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
const reviewSection = document.getElementById('reviewSection');
const imageGrid = document.getElementById('imageGrid');
const selectAllBtn = document.getElementById('selectAllBtn');
const selectNoneBtn = document.getElementById('selectNoneBtn');
const selectionCount = document.getElementById('selectionCount');
const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
const imagePreviewModal = document.getElementById('imagePreviewModal');
const imagePreviewCloseBtn = document.getElementById('imagePreviewCloseBtn');
const imagePreviewImg = document.getElementById('imagePreviewImg');
const imagePreviewFilename = document.getElementById('imagePreviewFilename');
const imagePreviewSelectCheckbox = document.getElementById('imagePreviewSelectCheckbox');
const imagePreviewPrevBtn = document.getElementById('imagePreviewPrevBtn');
const imagePreviewNextBtn = document.getElementById('imagePreviewNextBtn');
const hidePageTurnCheckbox = document.getElementById('hidePageTurnCheckbox');

let currentTaskId = null;
let statusInterval = null;
let imageList = [];
let imageMetadata = {};  // 存储图片元数据 {filename: {is_page_turn: bool}}
let selectedImages = new Set();
let currentPreviewFilename = null;
let hidePageTurnImages = true;  // 默认隐藏翻页图片

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

async function showResult(data) {
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
    
    await loadImages();
    
    submitBtn.disabled = false;
    submitBtn.textContent = '开始转换';
}

function updateResultInfoWithPageTurn(pageTurnCount) {
    const resultInfo = document.getElementById('resultInfo');
    if (resultInfo && pageTurnCount !== undefined) {
        const existingHtml = resultInfo.innerHTML;
        // 检查是否已经添加了翻页统计
        if (!existingHtml.includes('翻页图片')) {
            resultInfo.innerHTML = existingHtml + `<p><strong>翻页图片:</strong> ${pageTurnCount} 张</p>`;
        }
    }
}

async function loadImages() {
    try {
        const response = await fetch(`/api/images/${currentTaskId}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '加载图片列表失败');
        }
        
        // 处理新的数据结构
        const images = data.images || [];
        imageList = images.map(img => img.filename);
        imageMetadata = {};
        images.forEach(img => {
            imageMetadata[img.filename] = {
                is_page_turn: img.is_page_turn || false
            };
        });
        
        // 更新统计信息
        if (data.page_turn_count !== undefined) {
            updateResultInfoWithPageTurn(data.page_turn_count);
        }
        
        selectedImages.clear();
        // 默认选中所有可见图片
        const visibleImages = getVisibleImages();
        visibleImages.forEach(filename => selectedImages.add(filename));
        renderImageGrid();
        updateSelectionCount();
    } catch (error) {
        showError(error.message);
    }
}

function findImageItemByFilename(filename) {
    const items = imageGrid.querySelectorAll('.image-item');
    for (const item of items) {
        if (item.dataset.filename === filename) {
            return item;
        }
    }
    return null;
}

function syncGridSelectionUI(filename) {
    const item = findImageItemByFilename(filename);
    if (!item) {
        return;
    }
    const checkbox = item.querySelector('input[type="checkbox"]');
    if (checkbox) {
        checkbox.checked = selectedImages.has(filename);
    }
    updateImageItemState(item, filename);
}

function openImagePreview(filename) {
    currentPreviewFilename = filename;
    imagePreviewImg.src = `/api/image/${currentTaskId}/${filename}`;
    imagePreviewImg.alt = filename;
    imagePreviewFilename.textContent = filename;
    imagePreviewSelectCheckbox.checked = selectedImages.has(filename);
    updatePreviewNavState();
    imagePreviewModal.style.display = 'flex';
}

function closeImagePreview() {
    imagePreviewModal.style.display = 'none';
    imagePreviewImg.src = '';
    imagePreviewImg.alt = '';
    imagePreviewFilename.textContent = '';
    currentPreviewFilename = null;
}

function isPreviewOpen() {
    return imagePreviewModal.style.display !== 'none';
}

function getCurrentPreviewIndex() {
    if (!currentPreviewFilename) {
        return -1;
    }
    const visibleImages = getVisibleImages();
    return visibleImages.indexOf(currentPreviewFilename);
}

function updatePreviewNavState() {
    const visibleImages = getVisibleImages();
    const idx = getCurrentPreviewIndex();
    imagePreviewPrevBtn.disabled = idx <= 0;
    imagePreviewNextBtn.disabled = idx < 0 || idx >= visibleImages.length - 1;
}

function navigatePreview(delta) {
    const visibleImages = getVisibleImages();
    const idx = getCurrentPreviewIndex();
    if (idx < 0) {
        return;
    }
    const nextIdx = idx + delta;
    if (nextIdx < 0 || nextIdx >= visibleImages.length) {
        return;
    }
    openImagePreview(visibleImages[nextIdx]);
}

function getVisibleImages() {
    if (hidePageTurnImages) {
        return imageList.filter(filename => {
            const metadata = imageMetadata[filename];
            return !metadata || !metadata.is_page_turn;
        });
    }
    return imageList;
}

function renderImageGrid() {
    imageGrid.innerHTML = '';
    
    const visibleImages = getVisibleImages();
    let visibleIndex = 0;
    
    imageList.forEach((filename, index) => {
        const metadata = imageMetadata[filename] || {};
        const isPageTurn = metadata.is_page_turn || false;
        
        // 如果隐藏翻页图片且当前是翻页图片，则跳过
        if (hidePageTurnImages && isPageTurn) {
            return;
        }
        
        const imageItem = document.createElement('div');
        imageItem.className = 'image-item';
        imageItem.dataset.filename = filename;
        
        // 如果是翻页图片，添加视觉标记
        if (isPageTurn) {
            imageItem.classList.add('page-turn');
        }
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `img-${visibleIndex}`;
        checkbox.checked = selectedImages.has(filename);
        checkbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                selectedImages.add(filename);
            } else {
                selectedImages.delete(filename);
            }
            updateImageItemState(imageItem, filename);
            updateSelectionCount();
            if (currentPreviewFilename === filename) {
                imagePreviewSelectCheckbox.checked = selectedImages.has(filename);
            }
        });
        
        const img = document.createElement('img');
        img.src = `/api/image/${currentTaskId}/${filename}`;
        img.alt = filename;
        img.loading = 'lazy';
        img.addEventListener('click', (e) => {
            e.stopPropagation();
            openImagePreview(filename);
        });
        
        const imageName = document.createElement('div');
        imageName.className = 'image-name';
        imageName.textContent = filename;
        
        imageItem.appendChild(checkbox);
        imageItem.appendChild(img);
        imageItem.appendChild(imageName);
        
        imageItem.addEventListener('click', (e) => {
            if (e.target !== checkbox && e.target !== checkbox.parentElement) {
                checkbox.checked = !checkbox.checked;
                checkbox.dispatchEvent(new Event('change'));
            }
        });
        
        updateImageItemState(imageItem, filename);
        imageGrid.appendChild(imageItem);
        visibleIndex++;
    });
    
    reviewSection.style.display = 'block';
}

function updateImageItemState(item, filename) {
    if (selectedImages.has(filename)) {
        item.classList.add('selected');
    } else {
        item.classList.remove('selected');
    }
}

function updateSelectionCount() {
    const visibleImages = getVisibleImages();
    const visibleSelected = visibleImages.filter(filename => selectedImages.has(filename)).length;
    selectionCount.textContent = `已选择 ${visibleSelected} / ${visibleImages.length} 张`;
}

selectAllBtn.addEventListener('click', () => {
    const visibleImages = getVisibleImages();
    visibleImages.forEach(filename => selectedImages.add(filename));
    renderImageGrid();
    updateSelectionCount();
});

selectNoneBtn.addEventListener('click', () => {
    selectedImages.clear();
    renderImageGrid();
    updateSelectionCount();
});

downloadSelectedBtn.addEventListener('click', async () => {
    if (selectedImages.size === 0) {
        alert('请至少选择一张图片');
        return;
    }
    
    try {
        const response = await fetch(`/api/download/${currentTaskId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                files: Array.from(selectedImages)
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || '下载失败');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `frames_selected_${currentTaskId}.zip`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    } catch (error) {
        alert(error.message);
    }
});

imagePreviewCloseBtn.addEventListener('click', () => {
    closeImagePreview();
});

imagePreviewPrevBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    navigatePreview(-1);
});

imagePreviewNextBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    navigatePreview(1);
});

imagePreviewSelectCheckbox.addEventListener('change', (e) => {
    if (!currentPreviewFilename) {
        return;
    }
    if (e.target.checked) {
        selectedImages.add(currentPreviewFilename);
    } else {
        selectedImages.delete(currentPreviewFilename);
    }
    syncGridSelectionUI(currentPreviewFilename);
    updateSelectionCount();
});

imagePreviewModal.addEventListener('click', (e) => {
    if (e.target === imagePreviewModal) {
        closeImagePreview();
    }
});

hidePageTurnCheckbox.addEventListener('change', (e) => {
    hidePageTurnImages = e.target.checked;
    renderImageGrid();
    updateSelectionCount();
    // 如果当前预览的图片被隐藏，关闭预览
    if (currentPreviewFilename) {
        const visibleImages = getVisibleImages();
        if (!visibleImages.includes(currentPreviewFilename)) {
            closeImagePreview();
        } else {
            updatePreviewNavState();
        }
    }
});

document.addEventListener('keydown', (e) => {
    if (!isPreviewOpen()) {
        return;
    }
    if (e.key === 'ArrowLeft') {
        navigatePreview(-1);
    } else if (e.key === 'ArrowRight') {
        navigatePreview(1);
    }
});

function showError(message) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    errorMessage.textContent = message;
    
    submitBtn.disabled = false;
    submitBtn.textContent = '开始转换';
}
