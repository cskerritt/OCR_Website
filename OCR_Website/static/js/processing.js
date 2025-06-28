// Processing related JavaScript functions

// Status and log update functions
async function fetchStatus() {
    try {
        const response = await fetch('/status');
        if (response.ok) {
            const status = await response.json();
            
            if (status.is_processing) {
                // Update file progress
                const fileProgress = document.getElementById('file-progress');
                fileProgress.classList.remove('hidden');
                
                document.getElementById('current-file-index').textContent = status.current_file_index;
                document.getElementById('total-files').textContent = status.total_files;
                document.getElementById('current-filename').textContent = status.current_file || '';
                
                // Update progress bar
                const percentComplete = (status.current_file_index / status.total_files) * 100;
                document.getElementById('progress-bar').style.width = `${percentComplete}%`;
                
                // Update elapsed time
                if (status.elapsed_seconds) {
                    const minutes = Math.floor(status.elapsed_seconds / 60);
                    const seconds = Math.floor(status.elapsed_seconds % 60);
                    document.getElementById('time-elapsed').textContent = 
                        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    
                    // Show timeout warning if processing takes too long
                    if (status.elapsed_seconds > 120 || status.possible_hang) {
                        document.getElementById('timeout-warning').classList.remove('hidden');
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

async function fetchLogs() {
    try {
        const response = await fetch('/logs');
        if (response.ok) {
            const logs = await response.json();
            const logDisplay = document.getElementById('log-display');
            
            if (logs.length > 0) {
                // Add new logs
                logs.forEach(log => {
                    if (!lastLogTimestamp || log.timestamp > lastLogTimestamp) {
                        // Create log entry with appropriate color based on level
                        let levelClass = 'log-info'; // Default for INFO
                        if (log.level === 'ERROR') levelClass = 'log-error';
                        if (log.level === 'WARNING') levelClass = 'log-warning';
                        
                        const logEntry = document.createElement('div');
                        logEntry.className = `log-entry ${levelClass}`;
                        logEntry.innerHTML = `<span class="log-timestamp">[${log.timestamp}]</span> ${log.message}`;
                        logDisplay.appendChild(logEntry);
                        
                        lastLogTimestamp = log.timestamp;
                    }
                });
                
                // Auto-scroll to bottom if enabled
                if (document.getElementById('auto-scroll').checked) {
                    logDisplay.scrollTop = logDisplay.scrollHeight;
                }
            }
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
    }
}

function startUpdates() {
    // Clear any existing intervals
    if (logUpdateInterval) clearInterval(logUpdateInterval);
    if (statusUpdateInterval) clearInterval(statusUpdateInterval);
    
    // Reset log display and timestamp
    const logDisplay = document.getElementById('log-display');
    logDisplay.innerHTML = '<div class="log-entry">Starting process...</div>';
    lastLogTimestamp = null;
    processingStartTime = Date.now();
    
    // Start fetching logs and status periodically
    fetchLogs();
    fetchStatus();
    logUpdateInterval = setInterval(fetchLogs, 1000); // Update logs every second
    statusUpdateInterval = setInterval(fetchStatus, 1000); // Update status every second
    
    // Hide timeout warning initially
    document.getElementById('timeout-warning').classList.add('hidden');
}

function stopUpdates() {
    if (logUpdateInterval) {
        clearInterval(logUpdateInterval);
        logUpdateInterval = null;
    }
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
        statusUpdateInterval = null;
    }
}

// Add event listener for the auto-scroll checkbox
document.addEventListener('DOMContentLoaded', function() {
    const autoScrollCheckbox = document.getElementById('auto-scroll');
    if (autoScrollCheckbox) {
        autoScrollCheckbox.addEventListener('change', function() {
            if (this.checked) {
                const logDisplay = document.getElementById('log-display');
                logDisplay.scrollTop = logDisplay.scrollHeight;
            }
        });
    }
});

// Add a function to estimate remaining time
function estimateRemainingTime(currentIndex, totalFiles, elapsedSeconds) {
    if (currentIndex <= 0 || totalFiles <= 0 || elapsedSeconds <= 0) {
        return 'Calculating...';
    }
    
    const filesRemaining = totalFiles - currentIndex;
    const averageTimePerFile = elapsedSeconds / currentIndex;
    const estimatedSecondsRemaining = filesRemaining * averageTimePerFile;
    
    // Format the time
    if (estimatedSecondsRemaining < 60) {
        return 'Less than a minute';
    } else if (estimatedSecondsRemaining < 3600) {
        const minutes = Math.round(estimatedSecondsRemaining / 60);
        return `About ${minutes} minute${minutes !== 1 ? 's' : ''}`;
    } else {
        const hours = Math.floor(estimatedSecondsRemaining / 3600);
        const minutes = Math.round((estimatedSecondsRemaining % 3600) / 60);
        return `About ${hours} hour${hours !== 1 ? 's' : ''} ${minutes > 0 ? `and ${minutes} minute${minutes !== 1 ? 's' : ''}` : ''}`;
    }
}

// Update the UI to show estimated time remaining
function updateEstimatedTimeRemaining(status) {
    if (status.is_processing && status.current_file_index > 0 && status.elapsed_seconds > 0) {
        const estimatedTimeElement = document.getElementById('estimated-time-remaining');
        if (estimatedTimeElement) {
            const estimate = estimateRemainingTime(
                status.current_file_index,
                status.total_files,
                status.elapsed_seconds
            );
            estimatedTimeElement.textContent = estimate;
            estimatedTimeElement.parentElement.classList.remove('hidden');
        }
    }
}

// Add event listener for the download button to track analytics
document.addEventListener('DOMContentLoaded', function() {
    const downloadLink = document.getElementById('download-link');
    if (downloadLink) {
        downloadLink.addEventListener('click', function() {
            // Track download event (could be expanded to send analytics data)
            console.log('Download initiated at', new Date().toISOString());
            
            // Show a success message
            const successMessage = document.createElement('div');
            successMessage.className = 'success-message';
            successMessage.textContent = 'Download started! Your browser should prompt you to save the file.';
            
            const downloadSection = document.getElementById('download-section');
            downloadSection.appendChild(successMessage);
            
            // Remove the message after 5 seconds
            setTimeout(() => {
                successMessage.remove();
            }, 5000);
        });
    }
});
