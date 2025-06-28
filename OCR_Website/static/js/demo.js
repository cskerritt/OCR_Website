// Demo JavaScript for OCR Website - GitHub Pages Version
// This simulates the OCR processing functionality without actual server-side processing

// Demo configuration
const DEMO_MODE = true;
const DEMO_PROCESSING_TIME = 5000; // 5 seconds for demo
const DEMO_FILES_DATA = [
    { name: 'document1.pdf', pages: 15, size: 2.3 },
    { name: 'report.pdf', pages: 8, size: 1.7 },
    { name: 'presentation.pdf', pages: 25, size: 4.1 }
];

// Override the process button functionality for demo
if (DEMO_MODE) {
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        const processBtn = document.getElementById('process-btn');
        const progress = document.getElementById('progress');
        const progressBar = document.getElementById('progress-bar');
        const downloadSection = document.getElementById('download-section');
        const logDisplay = document.getElementById('log-display');
        const fileProgress = document.getElementById('file-progress');
        const currentFileIndex = document.getElementById('current-file-index');
        const totalFiles = document.getElementById('total-files');
        const currentFilename = document.getElementById('current-filename');
        const timeElapsed = document.getElementById('time-elapsed');
        
        // Override the original process button click handler
        if (processBtn) {
            // Remove existing event listeners by cloning the element
            const newProcessBtn = processBtn.cloneNode(true);
            processBtn.parentNode.replaceChild(newProcessBtn, processBtn);
            
            newProcessBtn.addEventListener('click', function() {
                if (window.files && window.files.length === 0) {
                    showDemoError('Please select some PDF files first to see the demo.');
                    return;
                }
                
                startDemoProcessing();
            });
        }
    });
}

function showDemoError(message) {
    const errorSection = document.getElementById('error-section');
    const errorList = document.getElementById('error-list');
    errorList.innerHTML = `<div class="error-item">• ${message}</div>`;
    errorSection.classList.remove('hidden');
}

function hideDemoError() {
    const errorSection = document.getElementById('error-section');
    errorSection.classList.add('hidden');
}

function startDemoProcessing() {
    hideDemoError();
    updateStepHighlight(3);
    
    const progress = document.getElementById('progress');
    const progressBar = document.getElementById('progress-bar');
    const downloadSection = document.getElementById('download-section');
    const logDisplay = document.getElementById('log-display');
    const fileProgress = document.getElementById('file-progress');
    const processBtn = document.getElementById('process-btn');
    
    // Show progress section
    progress.classList.remove('hidden');
    downloadSection.classList.add('hidden');
    processBtn.disabled = true;
    fileProgress.classList.remove('hidden');
    
    // Clear previous logs
    logDisplay.innerHTML = '<div class="log-entry">Demo mode: Starting OCR processing simulation...</div>';
    
    // Get files from the global files array or use demo data
    const filesToProcess = window.files && window.files.length > 0 ? 
        window.files.map(f => ({ name: f.name, pages: Math.floor(Math.random() * 20) + 5, size: f.size / (1024 * 1024) })) :
        DEMO_FILES_DATA;
    
    const totalFiles = document.getElementById('total-files');
    const currentFileIndex = document.getElementById('current-file-index');
    const currentFilename = document.getElementById('current-filename');
    
    totalFiles.textContent = filesToProcess.length;
    
    let currentIndex = 0;
    let startTime = Date.now();
    let logIndex = 0;
    
    const demoLogs = [
        'Initializing OCR processor...',
        'Checking file permissions and validity...',
        'Setting up parallel processing with 4 CPU cores...',
        'Starting batch processing...'
    ];
    
    function updateProgress() {
        const elapsed = Date.now() - startTime;
        const progress = (currentIndex / filesToProcess.length) * 100;
        
        // Update progress bar
        progressBar.style.width = `${progress}%`;
        
        // Update time elapsed
        const timeElapsed = document.getElementById('time-elapsed');
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        timeElapsed.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Add demo logs
        if (logIndex < demoLogs.length && elapsed > logIndex * 500) {
            addLogEntry(demoLogs[logIndex]);
            logIndex++;
        }
        
        // Process each file
        if (currentIndex < filesToProcess.length) {
            const file = filesToProcess[currentIndex];
            currentFileIndex.textContent = currentIndex + 1;
            currentFilename.textContent = file.name;
            
            addLogEntry(`Processing file ${currentIndex + 1}/${filesToProcess.length}: ${file.name}`);
            addLogEntry(`File size: ${file.size.toFixed(2)} MB, estimated ${file.pages} pages`);
            
            if (Math.random() > 0.7) {
                addLogEntry(`Optimizing large PDF: ${file.name}`);
            }
            
            if (Math.random() > 0.8) {
                addLogEntry(`Cache hit for ${file.name} - loading from cache`);
            } else {
                addLogEntry(`Running OCR on ${file.name}...`);
                addLogEntry(`OCR processing complete for ${file.name}`);
            }
            
            currentIndex++;
            
            // Continue processing
            setTimeout(updateProgress, 800 + Math.random() * 400);
        } else {
            // Processing complete
            finishDemoProcessing(filesToProcess);
        }
    }
    
    // Start the demo processing
    setTimeout(updateProgress, 500);
}

function addLogEntry(message) {
    const logDisplay = document.getElementById('log-display');
    const autoScroll = document.getElementById('auto-scroll');
    
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = `[${timestamp}] ${message}`;
    
    logDisplay.appendChild(entry);
    
    // Auto-scroll if enabled
    if (autoScroll && autoScroll.checked) {
        logDisplay.scrollTop = logDisplay.scrollHeight;
    }
}

function finishDemoProcessing(filesToProcess) {
    addLogEntry('Creating ZIP archive...');
    addLogEntry('Processing complete!');
    addLogEntry(`Successfully processed ${filesToProcess.length} files`);
    
    setTimeout(() => {
        // Hide progress and show results
        const progress = document.getElementById('progress');
        const downloadSection = document.getElementById('download-section');
        const processBtn = document.getElementById('process-btn');
        
        progress.classList.add('hidden');
        downloadSection.classList.remove('hidden');
        processBtn.disabled = false;
        
        // Update page count information
        const totalPages = filesToProcess.reduce((sum, file) => sum + file.pages, 0);
        document.getElementById('total-pages').textContent = totalPages;
        
        const filePagesList = document.getElementById('file-pages-list');
        filePagesList.innerHTML = filesToProcess.map(file => 
            `<div class="file-info-item">• ${file.name}: ${file.pages} pages (${file.size.toFixed(1)} MB) 
            ${Math.random() > 0.7 ? '<span class="cached-tag">[from cache]</span>' : ''}
            ${Math.random() > 0.8 ? '<span class="optimized-tag">[optimized]</span>' : ''}</div>`
        ).join('');
        
        // Show optimization info
        const optInfo = document.getElementById('optimization-info');
        optInfo.classList.remove('hidden');
        
        document.getElementById('cached-files').textContent = Math.floor(filesToProcess.length * 0.3);
        document.getElementById('optimized-files').textContent = Math.floor(filesToProcess.length * 0.2);
        document.getElementById('cpu-cores').textContent = '4';
        
        // Update download link
        const downloadLink = document.getElementById('download-link');
        downloadLink.onclick = function(e) {
            e.preventDefault();
            alert('Demo Mode: In the full version, this would download a ZIP file containing your OCR-processed PDFs.\n\nTo get the actual functionality, deploy the application using the instructions below.');
        };
        
        updateStepHighlight(4);
        
    }, 1000);
}

// Override file handling to work with demo
document.addEventListener('DOMContentLoaded', function() {
    // Make files accessible globally for demo
    window.files = window.files || [];
    
    // Add demo notification when files are selected
    const originalHandleFiles = window.handleFiles;
    if (typeof originalHandleFiles === 'function') {
        window.handleFiles = function(e) {
            originalHandleFiles(e);
            
            // Show demo notification
            if (window.files && window.files.length > 0) {
                setTimeout(() => {
                    const notification = document.createElement('div');
                    notification.className = 'demo-notification fixed top-20 right-4 bg-blue-100 border border-blue-400 text-blue-700 px-4 py-2 rounded shadow-lg z-50';
                    notification.innerHTML = `
                        <div class="flex items-center">
                            <svg class="h-4 w-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>
                            </svg>
                            <span class="text-sm">Files ready for demo processing!</span>
                        </div>
                    `;
                    
                    document.body.appendChild(notification);
                    
                    // Remove notification after 3 seconds
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 3000);
                }, 500);
            }
        };
    }
});

// Add styles for demo-specific elements
const demoStyles = `
    <style>
    .cached-tag {
        background-color: #10B981;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    
    .optimized-tag {
        background-color: #F59E0B;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-left: 8px;
    }
    
    .file-info-item {
        margin-bottom: 4px;
    }
    
    .demo-notification {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    </style>
`;

document.head.insertAdjacentHTML('beforeend', demoStyles);