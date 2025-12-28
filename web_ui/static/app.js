// File upload state
let scriptFile = null;
let styleFile = null;

// DOM elements
const scriptUpload = document.getElementById('scriptUpload');
const styleUpload = document.getElementById('styleUpload');
const scriptFileInput = document.getElementById('scriptFile');
const styleFileInput = document.getElementById('styleFile');
const produceBtn = document.getElementById('produceBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusList = document.getElementById('statusList');

// Drag and drop handlers
function setupDragAndDrop(element, fileInput, fileType) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        element.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        element.addEventListener(eventName, () => {
            element.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        element.addEventListener(eventName, () => {
            element.classList.remove('drag-over');
        });
    });

    element.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0], fileType);
        }
    });
}

// Handle file selection
function handleFile(file, type) {
    if (type === 'script') {
        if (!file.name.endsWith('.json')) {
            alert('Please upload a JSON file for the script.');
            return;
        }
        scriptFile = file;
        document.getElementById('scriptFileName').textContent = `✓ ${file.name}`;
    } else if (type === 'style') {
        styleFile = file;
        document.getElementById('styleFileName').textContent = `✓ ${file.name}`;
    }

    updateProduceButton();
}

// File input change handlers
scriptFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0], 'script');
    }
});

styleFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0], 'style');
    }
});

// Update produce button state
function updateProduceButton() {
    produceBtn.disabled = !scriptFile;
}

// Upload files
async function uploadFiles() {
    if (!scriptFile) return;

    const formData = new FormData();
    formData.append('script', scriptFile);
    if (styleFile) {
        formData.append('style', styleFile);
    }

    // Show progress
    progressSection.hidden = false;
    produceBtn.querySelector('.btn-text').hidden = true;
    produceBtn.querySelector('.btn-loader').hidden = false;
    produceBtn.disabled = true;

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            // Success
            progressFill.style.width = '100%';
            progressText.textContent = '✅ Upload complete! Video production started.';

            // Add to status list
            addStatusItem(result);

            // Reset form
            setTimeout(() => {
                resetForm();
            }, 2000);
        } else {
            throw new Error(result.error || 'Upload failed');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        progressText.textContent = `❌ ${error.message}`;
    } finally {
        produceBtn.querySelector('.btn-text').hidden = false;
        produceBtn.querySelector('.btn-loader').hidden = true;
    }
}

// Add status item
function addStatusItem(data) {
    const emptyState = statusList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }

    const item = document.createElement('div');
    item.className = 'status-item';
    item.innerHTML = `
        <div>
            <strong>${data.filename}</strong>
            <p style="font-size: 0.875rem; color: var(--text-muted); margin-top: 0.25rem;">
                Uploaded at ${new Date().toLocaleTimeString()}
            </p>
        </div>
        <div style="text-align: right;">
            <span style="padding: 0.25rem 0.75rem; background: rgba(16, 185, 129, 0.2); color: var(--success); border-radius: 4px; font-size: 0.875rem;">
                Processing
            </span>
        </div>
    `;

    statusList.insertBefore(item, statusList.firstChild);
}

// Reset form
function resetForm() {
    scriptFile = null;
    styleFile = null;
    scriptFileInput.value = '';
    styleFileInput.value = '';
    document.getElementById('scriptFileName').textContent = '';
    document.getElementById('styleFileName').textContent = '';
    progressSection.hidden = true;
    progressFill.style.width = '0%';
    updateProduceButton();
}

// Event listeners
setupDragAndDrop(scriptUpload, scriptFileInput, 'script');
setupDragAndDrop(styleUpload, styleFileInput, 'style');
produceBtn.addEventListener('click', uploadFiles);

// Simulate progress (since we don't have real-time updates yet)
let progressInterval;
function simulateProgress() {
    let progress = 0;
    progressInterval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 95) {
            clearInterval(progressInterval);
            progress = 95;
        }
        progressFill.style.width = `${progress}%`;
    }, 500);
}
