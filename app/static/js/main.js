// Main JavaScript file for the application

// Show loading spinner
function showSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    document.body.appendChild(spinner);
}

// Hide loading spinner
function hideSpinner() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Handle file upload
function handleFileUpload(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    showSpinner();

    fetch(form.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
        } else {
            showAlert('success', data.message);
            form.reset();
            if (typeof updateFileList === 'function') {
                updateFileList();
            }
        }
    })
    .catch(error => {
        showAlert('error', 'An error occurred while uploading the file.');
        console.error('Upload error:', error);
    })
    .finally(() => {
        hideSpinner();
    });
}

// Show alert message
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    alertContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

// Delete file
function deleteFile(fileId) {
    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }

    showSpinner();

    fetch(`/files/${fileId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
        } else {
            showAlert('success', data.message);
            if (typeof updateFileList === 'function') {
                updateFileList();
            }
        }
    })
    .catch(error => {
        showAlert('error', 'An error occurred while deleting the file.');
        console.error('Delete error:', error);
    })
    .finally(() => {
        hideSpinner();
    });
}

// Share file
function shareFile(fileId) {
    const email = prompt('Enter the email address to share with:');
    if (!email) return;

    showSpinner();

    fetch(`/files/${fileId}/share`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showAlert('error', data.error);
        } else {
            showAlert('success', data.message);
        }
    })
    .catch(error => {
        showAlert('error', 'An error occurred while sharing the file.');
        console.error('Share error:', error);
    })
    .finally(() => {
        hideSpinner();
    });
}

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

    // Initialize Bootstrap popovers
    const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
    popovers.forEach(popover => new bootstrap.Popover(popover));

    // Add form submit handlers
    const uploadForms = document.querySelectorAll('form[data-upload]');
    uploadForms.forEach(form => {
        form.addEventListener('submit', handleFileUpload);
    });
}); 