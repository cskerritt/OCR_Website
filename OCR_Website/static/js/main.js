// Main JavaScript for OCR Website

// DOM elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const processBtn = document.getElementById('process-btn');
const progress = document.getElementById('progress');
const progressBar = document.getElementById('progress-bar');
const downloadSection = document.getElementById('download-section');
const downloadLink = document.getElementById('download-link');
const steps = document.querySelectorAll('.instruction-step');
const darkModeToggle = document.getElementById('dark-mode-toggle');

// Global variables
let files = [];
// Make files globally accessible for demo
window.files = files;
let lastLogTimestamp = null;
let logUpdateInterval = null;
let statusUpdateInterval = null;
let processingStartTime = null;
let currentProcessId = null;
let processingPollInterval = null;

// Dark mode functionality
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
    
    // Update toggle button text
    if (darkModeToggle) {
        darkModeToggle.textContent = isDarkMode ? '☀️ Light Mode' : '🌙 Dark Mode';
    }
}

// Check for saved dark mode preference
function checkDarkModePreference() {
    if (localStorage.getItem('darkMode') === 'enabled') {
        document.body.classList.add('dark-mode');
        if (darkModeToggle) {
            darkModeToggle.textContent = '☀️ Light Mode';
        }
    }
}

// Initialize dark mode
document.addEventListener('DOMContentLoaded', checkDarkModePreference);
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', toggleDarkMode);
}

// Update step highlighting
function updateStepHighlight(stepNumber) {
    steps.forEach((step, index) => {
        if (index + 1 <= stepNumber) {
            step.classList.add('active');
        } else {
            step.classList.remove('active');
        }
    });
}

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

// Highlight drop zone when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

// Handle dropped files
dropZone.addEventListener('drop', handleDrop, false);
fileInput.addEventListener('change', handleFiles, false);

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight(e) {
    dropZone.classList.add('dragover');
}

function unhighlight(e) {
    dropZone.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const droppedFiles = dt.files;
    handleFiles({ target: { files: droppedFiles } });
}

// Make handleFiles available globally for demo override
window.handleFiles = function(e) {
    updateStepHighlight(1);
    const newFilesArray = [...e.target.files];
    
    // Filter for PDF files only
    const newPdfFiles = newFilesArray.filter(file => file.type === 'application/pdf');
    
    // Check if any non-PDF files were filtered out
    if (newPdfFiles.length < newFilesArray.length) {
        showError("Some files were skipped because they are not PDFs.");
    }
    
    // Check file size limit (1.5GB total)
    const currentSize = files.reduce((total, file) => total + file.size, 0);
    const newFilesSize = newPdfFiles.reduce((total, file) => total + file.size, 0);
    const totalSize = currentSize + newFilesSize;
    const maxSize = 1.5 * 1024 * 1024 * 1024; // 1.5GB in bytes
    
    if (totalSize > maxSize) {
        showError(`Total file size exceeds the 1.5GB limit. Current total: ${(totalSize / (1024 * 1024 * 1024)).toFixed(2)}GB`);
        
        // Only add files up to the limit
        let availableSize = maxSize - currentSize;
        let i = 0;
        
        while (i < newPdfFiles.length && availableSize > 0) {
            if (newPdfFiles[i].size <= availableSize) {
                files.push(newPdfFiles[i]);
                availableSize -= newPdfFiles[i].size;
            }
            i++;
        }
    } else {
        files = [...files, ...newPdfFiles];
    }
    
    // Update global reference for demo compatibility
    window.files = files;
    
    updateFileList();
    processBtn.disabled = files.length === 0;
    if (files.length > 0) {
        updateStepHighlight(2);
    }
}

function updateFileList() {
    fileList.innerHTML = files.map((file, index) => `
        <div class="file-item">
            <div>
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
            </div>
            <button onclick="removeFile(${index})" class="btn-remove">
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
    `).join('');
    
    // Add total size display if files exist
    if (files.length > 0) {
        const totalSize = files.reduce((total, file) => total + file.size, 0);
        fileList.innerHTML += `
            <div class="total-size">
                Total size: ${formatFileSize(totalSize)}
            </div>
        `;
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// This function needs to be in global scope for the onclick handler
window.removeFile = function(index) {
    files.splice(index, 1);
    // Update global reference for demo compatibility
    window.files = files;
    updateFileList();
    processBtn.disabled = files.length === 0;
    if (files.length === 0) {
        updateStepHighlight(1);
    }
};

function showError(message) {
    const errorSection = document.getElementById('error-section');
    const errorList = document.getElementById('error-list');
    errorList.innerHTML = `<div class="error-item">• ${message}</div>`;
    errorSection.classList.remove('hidden');
}

// Process status checking
async function checkProcessStatus(processId) {
    try {
        const response = await fetch(`/process-status/${processId}`);
        if (!response.ok) {
            console.error('Error fetching process status');
            return null;
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error checking process status:', error);
        return null;
    }
}

function pollProcessStatus() {
    if (!currentProcessId) return;
    
    const poll = async () => {
        const status = await checkProcessStatus(currentProcessId);
        if (!status) return;
        
        if (status.process_id && !status.success && !status.error) {
            // Still processing, continue polling
            setTimeout(poll, 2000);
        } else {
            // Processing complete, handle results
            clearInterval(processingPollInterval);
            handleProcessingComplete(status);
        }
    };
    
    poll();
}

function handleProcessingComplete(data) {
    // Stop updates
    stopUpdates();
    
    if (data.success === false || data.error) {
        const errorSection = document.getElementById('error-section');
        const errorList = document.getElementById('error-list');
        errorList.innerHTML = `<div class="error-item">• ${data.error || 'An unknown error occurred'}</div>`;
        errorSection.classList.remove('hidden');
        updateStepHighlight(2);
        progress.classList.add('hidden');
        processBtn.disabled = false;
        return;
    }
    
    downloadLink.href = data.download_url;
    downloadSection.classList.remove('hidden');
    
    // Display page count information
    if (data.total_pages !== undefined) {
        document.getElementById('total-pages').textContent = data.total_pages;
        const filePagesList = document.getElementById('file-pages-list');
        
        if (data.file_info && data.file_info.length > 0) {
            filePagesList.innerHTML = data.file_info.map(file => 
                `<div class="file-info-item">• ${file.name}: ${file.page_count} pages ${file.size_mb ? `(${file.size_mb} MB)` : ''} 
                ${file.from_cache ? '<span class="cached-tag">[from cache]</span>' : ''}
                ${file.optimized ? '<span class="optimized-tag">[optimized]</span>' : ''}</div>`
            ).join('');
        }
    }
    
    // Display optimization information if available
    if (data.stats) {
        const optInfo = document.getElementById('optimization-info');
        optInfo.classList.remove('hidden');
        
        document.getElementById('cached-files').textContent = data.stats.from_cache || 0;
        document.getElementById('optimized-files').textContent = data.stats.optimized_files || 0;
        
        // If parallel processing info is available
        const cpuCoresElement = document.getElementById('cpu-cores');
        if (data.stats.cpu_cores) {
            cpuCoresElement.textContent = data.stats.cpu_cores;
        } else {
            // Estimate based on typical configuration
            const totalFiles = data.stats.total_files || 1;
            const estimatedCores = Math.min(4, totalFiles);
            cpuCoresElement.textContent = estimatedCores;
        }
    }
    
    // Show errors if any
    if (data.errors && data.errors.length > 0) {
        const errorSection = document.getElementById('error-section');
        const errorList = document.getElementById('error-list');
        errorList.innerHTML = data.errors.map(error => `<div class="error-item">• ${error}</div>`).join('');
        errorSection.classList.remove('hidden');
    }
    
    updateStepHighlight(4);
    progress.classList.add('hidden');
    processBtn.disabled = false;
}

// Process button click handler
processBtn.addEventListener('click', async () => {
    if (files.length === 0) return;

    updateStepHighlight(3);
    const formData = new FormData();
    files.forEach(file => formData.append('files[]', file));

    progress.classList.remove('hidden');
    processBtn.disabled = true;
    downloadSection.classList.add('hidden');
    document.getElementById('error-section').classList.add('hidden');
    
    // Start log and status updates
    startUpdates();

    try {
        const response = await fetch('/process', {
            method: 'POST',
            body: formData
        });

        // Check for specific error status codes
        if (response.status === 413) {
            showError("File size limit exceeded (maximum 1.5GB combined). Please upload smaller files or fewer files at once.");
            stopUpdates();
            progress.classList.add('hidden');
            processBtn.disabled = false;
            return;
        }

        if (!response.ok) {
            const data = await response.json();
            showError(data.error || 'An unknown error occurred');
            stopUpdates();
            progress.classList.add('hidden');
            processBtn.disabled = false;
            updateStepHighlight(2);
            return;
        }
        
        const data = await response.json();
        
        // Save the process ID for status polling
        currentProcessId = data.process_id;
        
        // Start polling for process status
        pollProcessStatus();
        
    } catch (error) {
        stopUpdates();
        showError('An error occurred while processing the files');
        updateStepHighlight(2);
        progress.classList.add('hidden');
        processBtn.disabled = false;
    }
});

// Setup cancel button
document.getElementById('cancel-btn').addEventListener('click', async () => {
    if (confirm('Are you sure you want to cancel the current processing? Any progress will be lost.')) {
        try {
            // Call the cancel endpoint
            const response = await fetch(`/cancel-process/${currentProcessId}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                stopUpdates();
                progress.classList.add('hidden');
                processBtn.disabled = false;
                updateStepHighlight(2);
                showError('Processing was canceled');
            } else {
                // Fallback to page reload if cancel fails
                window.location.reload();
            }
        } catch (error) {
            console.error('Error canceling processing:', error);
            window.location.reload();
        }
    }
});

// Setup clear cache button
document.getElementById('clear-cache-btn').addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear the processing cache? This will free up disk space but may result in slower processing for repeat files.')) {
        try {
            const response = await fetch('/clear-cache');
            const data = await response.json();
            
            const cacheMessage = document.getElementById('cache-message');
            cacheMessage.textContent = data.message;
            cacheMessage.className = data.success ? 
                'cache-message success' : 'cache-message error';
            cacheMessage.classList.remove('hidden');
            
            // Hide message after 5 seconds
            setTimeout(() => {
                cacheMessage.classList.add('hidden');
            }, 5000);
        } catch (error) {
            console.error('Error clearing cache:', error);
            alert('An error occurred while clearing the cache');
        }
    }
});
