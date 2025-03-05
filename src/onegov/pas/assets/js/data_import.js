// Data Import Form JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.querySelector('.upload-dropzone');
    const fileInput = document.getElementById('fileElem');
    const peopleStatus = document.getElementById('people_upload_status');
    const organizationsStatus = document.getElementById('organizations_upload_status');
    const membershipsStatus = document.getElementById('memberships_upload_status');

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

    function preventDefaults (e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('highlight');
    }

    function unhighlight(e) {
        dropZone.classList.remove('highlight');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        files = [...files];
        files.forEach(uploadFile);
    }

    function uploadFile(file) {
        // Determine which form field to use based on filename
        let formField;
        let statusElement;

        if (file.name.toLowerCase().includes('people')) {
            formField = 'people_source';
            statusElement = peopleStatus;
        } else if (file.name.toLowerCase().includes('organization')) {
            formField = 'organizations_source';
            statusElement = organizationsStatus;
        } else if (file.name.toLowerCase().includes('membership')) {
            formField = 'memberships_source';
            statusElement = membershipsStatus;
        } else {
            console.error('Unknown file type:', file.name);
            return;
        }

        // Update status to uploading
        statusElement.className = 'callout warning';
        statusElement.innerHTML = '<p class="small">Uploading...</p>';

        const formData = new FormData();
        formData.append(formField, file);

        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => {
            if (response.ok) {
                statusElement.className = 'callout success';
                statusElement.innerHTML = '<p class="small">Upload Complete</p>';
            } else {
                throw new Error('Upload failed');
            }
        })
        .catch(error => {
            statusElement.className = 'callout alert';
            statusElement.innerHTML = '<p class="small">Upload Failed</p>';
            console.error('Error:', error);
        });
    }
});