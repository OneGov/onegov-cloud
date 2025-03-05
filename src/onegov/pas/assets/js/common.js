document.addEventListener('DOMContentLoaded', () => {
    // Required file types
    const REQUIRED_FILES = [
        { id: 'people_source', name: 'People Data (JSON)', status: 'people_upload_status' },
        { id: 'organizations_source', name: 'Organizations Data (JSON)', status: 'organizations_upload_status' },
        { id: 'memberships_source', name: 'Memberships Data (JSON)', status: 'memberships_upload_status' }
    ];

    // Track uploaded files
    const uploadedFiles = {
        people_source: null,
        organizations_source: null,
        memberships_source: null
    };

    // Function to update the visual status for a file input
    const updateUploadStatus = (inputId, file) => {
        const statusId = REQUIRED_FILES.find(f => f.id === inputId).status;
        const statusEl = document.getElementById(statusId);

        if (statusEl) {
            if (file) {
                uploadedFiles[inputId] = file;
                statusEl.classList.remove('alert');
                statusEl.classList.add('success');
                statusEl.innerHTML = `<p class="small">Uploaded: ${file.name}</p>`;
            } else {
                uploadedFiles[inputId] = null;
                statusEl.classList.remove('success');
                statusEl.classList.add('alert');
                statusEl.innerHTML = '<p class="small">Pending Upload</p>';
            }
        }

        // Check if all files are uploaded
        checkAllFilesUploaded();
    };

    // Function to check if all required files are uploaded
    const checkAllFilesUploaded = () => {
        const allUploaded = Object.values(uploadedFiles).every(file => file !== null);
        const submitBtn = document.querySelector('button[type="submit"]');

        if (submitBtn) {
            submitBtn.disabled = !allUploaded;
            if (allUploaded) {
                submitBtn.classList.remove('disabled');
            } else {
                submitBtn.classList.add('disabled');
            }
        }
    };

    // Handle dropped files
    const handleFiles = (files) => {
        // Check if we have the right number of files
        if (files.length !== 3) {
            alert('Please upload exactly 3 JSON files: People, Organizations, and Memberships');
            return;
        }

        // Try to match files to expected types by name pattern
        for (const file of files) {
            const fileName = file.name.toLowerCase();

            if (fileName.includes('people') || fileName.includes('person')) {
                createHiddenInput('people_source', file);
                updateUploadStatus('people_source', file);
            } else if (fileName.includes('org')) {
                createHiddenInput('organizations_source', file);
                updateUploadStatus('organizations_source', file);
            } else if (fileName.includes('member') || fileName.includes('membership')) {
                createHiddenInput('memberships_source', file);
                updateUploadStatus('memberships_source', file);
            } else {
                // If we can't determine file type by name, ask the user
                promptForFileType(file);
            }
        }
    };

    // Create a file input for the form submission
    const createHiddenInput = (name, file) => {
        // Remove existing input if present
        const existing = document.querySelector(`input[name="${name}"]`);
        if (existing) {
            existing.remove();
        }

        // Create a DataTransfer object and add our file
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);

        // Create the input
        const input = document.createElement('input');
        input.type = 'file';
        input.name = name;
        input.style.display = 'none';
        input.files = dataTransfer.files;

        // Add it to the form
        document.querySelector('form.upload').appendChild(input);
    };

    // Prompt user to identify which file is which
    const promptForFileType = (file) => {
        const fileType = prompt(`Unable to automatically identify file type for "${file.name}". Please specify:\n1 for People\n2 for Organizations\n3 for Memberships`);

        switch (fileType) {
            case '1':
                createHiddenInput('people_source', file);
                updateUploadStatus('people_source', file);
                break;
            case '2':
                createHiddenInput('organizations_source', file);
                updateUploadStatus('organizations_source', file);
                break;
            case '3':
                createHiddenInput('memberships_source', file);
                updateUploadStatus('memberships_source', file);
                break;
            default:
                alert('Invalid selection. File not assigned.');
                break;
        }
    };

    // Set up the dropzone
    const dropzone = document.querySelector('.upload-dropzone');
    const fileInput = document.getElementById('fileElem');

    if (dropzone && fileInput) {
        // Handle drag events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });

        // Add visual feedback
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('drag-over');
            });
        });

        // Handle file drop
        dropzone.addEventListener('drop', (e) => {
            handleFiles(e.dataTransfer.files);
        });

        // Handle file selection through button
        fileInput.addEventListener('change', () => {
            handleFiles(fileInput.files);
        });
    }

    // Add a submit button if it doesn't exist
    if (!document.querySelector('button[type="submit"]')) {
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'button disabled';
        submitBtn.disabled = true;
        submitBtn.textContent = 'Import Data';
        document.querySelector('form.upload').appendChild(submitBtn);
    }

    // Initialize status for all file inputs
    REQUIRED_FILES.forEach(file => {
        updateUploadStatus(file.id, null);
    });
});
