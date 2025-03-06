// /*
//     Modified Upload function to handle specific files for data import.
//     Using the existing upload mechanism with the correct endpoint.
// */
// var DataImportUpload = function(element) {
//     // Use the specific upload endpoint for JSON imports
//     var uploadUrl = element.data('upload-url') || element.attr('action').replace('/import', '/upload-json-import-files');
//     var form = element;
//     var dropzone = $(element.find('.upload-dropzone'));
//     var drop_button = $(element.find('#fileElem'));
//     var progress = $(element.find('.upload-progress'));
//     var filelist = $(element.find('.upload-filelist'));
//     var filelist_header = $(element.find('.upload-filelist-header'));
//
//     console.log("Upload URL: " + uploadUrl);
//
//     // Track required files and their upload IDs
//     var required_files = {
//         'people_source': { uploaded: false, name: 'People Data', fileId: null },
//         'organizations_source': { uploaded: false, name: 'Organizations Data', fileId: null },
//         'memberships_source': { uploaded: false, name: 'Memberships Data', fileId: null }
//     };
//
//     // Function to update status indicators
//     var updateStatus = function(file_type, file_name, success, fileId) {
//         var status_id = file_type + '_upload_status';
//         var status_el = $('#' + status_id);
//
//         if (status_el.length) {
//             if (success) {
//                 status_el.removeClass('alert').addClass('success');
//                 status_el.html('<p class="small">Uploaded: ' + file_name + '</p>');
//                 required_files[file_type].uploaded = true;
//                 required_files[file_type].fileId = fileId;
//             } else {
//                 status_el.removeClass('success').addClass('alert');
//                 status_el.html('<p class="small">Pending Upload</p>');
//                 required_files[file_type].uploaded = false;
//                 required_files[file_type].fileId = null;
//             }
//         }
//
//         // Check if all files are uploaded
//         checkAllUploaded();
//     };
//
//     // Function to check if all required files are uploaded
//     var checkAllUploaded = function() {
//         var all_uploaded = true;
//         $.each(required_files, function(key, value) {
//             if (!value.uploaded) {
//                 all_uploaded = false;
//                 return false; // break loop
//             }
//         });
//
//         // Create or update submit button
//         var submit_btn = $('#import-submit-btn');
//         if (submit_btn.length === 0) {
//             submit_btn = $('<button id="import-submit-btn" class="button large">Import Data</button>')
//                 .css({
//                     'margin-top': '20px',
//                     'margin-bottom': '20px',
//                     'width': '100%',
//                     'padding': '15px'
//                 });
//             filelist.after(submit_btn);
//
//             // Add click handler
//             submit_btn.on('click', function() {
//                 var importUrl = form.attr('action');
//                 console.log("Import URL: " + importUrl);
//
//                 // Show processing state
//                 var results = $('<div id="import-processing" class="callout warning">')
//                     .html('<h3>Processing Import</h3><div class="progress"><div class="progress-meter" style="width: 100%"></div></div><p>Processing your files. This may take a few minutes. Please do not close this page.</p>')
//                     .insertAfter(filelist);
//
//                 // Disable the button
//                 submit_btn.prop('disabled', true).addClass('disabled').text('Processing...');
//
//                 // Create a form to submit with the file IDs
//                 var submitForm = $('<form>')
//                     .attr('method', 'POST')
//                     .attr('action', importUrl)
//                     .css('display', 'none');
//
//                 // Add CSRF token if it exists
//                 var csrf = $('input[name="csrf-token"]').val();
//                 if (csrf) {
//                     submitForm.append($('<input>').attr({
//                         type: 'hidden',
//                         name: 'csrf-token',
//                         value: csrf
//                     }));
//                 }
//
//                 // Add file IDs as hidden inputs
//                 $.each(required_files, function(key, value) {
//                     if (value.fileId) {
//                         submitForm.append($('<input>').attr({
//                             type: 'hidden',
//                             name: key + '_id',
//                             value: value.fileId
//                         }));
//                     }
//                 });
//
//                 // Add form to body and submit
//                 $('body').append(submitForm);
//                 submitForm.submit();
//             });
//         }
//
//         // Update button state
//         if (all_uploaded) {
//             submit_btn.prop('disabled', false).removeClass('disabled');
//         } else {
//             submit_btn.prop('disabled', true).addClass('disabled');
//         }
//     };
//
//     // Determine file type from name
//     var determineFileType = function(file_name) {
//         var lower_name = file_name.toLowerCase();
//
//         if (lower_name.indexOf('people') !== -1 || lower_name.indexOf('person') !== -1) {
//             return 'people_source';
//         } else if (lower_name.indexOf('org') !== -1) {
//             return 'organizations_source';
//         } else if (lower_name.indexOf('member') !== -1) {
//             return 'memberships_source';
//         }
//
//         // Ask the user if we can't determine
//         return promptForFileType(file_name);
//     };
//
//     // Prompt user to identify file type
//     var promptForFileType = function(file_name) {
//         var type = prompt(
//             'Unable to determine file type for "' + file_name + '". Please specify:\n' +
//             '1 for People\n' +
//             '2 for Organizations\n' +
//             '3 for Memberships'
//         );
//
//         switch (type) {
//             case '1': return 'people_source';
//             case '2': return 'organizations_source';
//             case '3': return 'memberships_source';
//             default: return null;
//         }
//     };
//
//     // Upload file using the existing mechanism
//     var upload = function(file, bar, file_type) {
//         // Use existing upload code
//         var xhr = new XMLHttpRequest();
//         xhr.open('POST', uploadUrl, true);
//         var data = new FormData();
//         data.append('file', file);
//
//         // Add CSRF token if it exists
//         var csrf = $('input[name="csrf-token"]').val();
//         if (csrf) {
//             data.append('csrf-token', csrf);
//         }
//
//         // Add file type as metadata
//         data.append('file_type', file_type);
//
//         xhr.upload.addEventListener('progress', function(e) {
//             bar.find('.meter').css('width', (e.loaded / e.total * 100 || 100) + '%');
//         });
//
//         xhr.addEventListener('readystatechange', function() {
//             if (xhr.readyState !== 4) {
//                 return;
//             }
//
//             pending_upload = false;
//
//             if (xhr.status === 200) {
//                 bar.remove();
//
//                 try {
//                     // Try to extract file ID from response
//                     var response = JSON.parse(xhr.responseText);
//                     var fileId = response.id || response.file_id;
//
//                     if (!fileId && xhr.responseText.indexOf('<') === 0) {
//                         // If response is HTML, extract ID from it
//                         var tempDiv = $('<div>').html(xhr.responseText);
//                         var fileItem = tempDiv.find('.file-item');
//                         if (fileItem.length) {
//                             fileId = fileItem.data('id');
//                         }
//                     }
//
//                     updateStatus(file_type, file.name, true, fileId);
//                 } catch (e) {
//                     console.error("Error parsing response: ", e);
//                     // Still mark as uploaded even if we can't parse the ID
//                     updateStatus(file_type, file.name, true, 'unknown');
//                 }
//
//                 // Process next file in queue
//                 process_upload_queue();
//             } else {
//                 bar.find('.meter').css('width', '100%');
//                 bar.addClass('alert').attr('data-error', xhr.statusText);
//                 process_upload_queue();
//             }
//         });
//
//         xhr.send(data);
//     };
//
//     // Queue for uploads
//     var upload_queue = [];
//     var pending_upload = false;
//
//     var process_upload_queue = function() {
//         if (pending_upload || upload_queue.length === 0) {
//             return;
//         }
//
//         pending_upload = true;
//         var data = upload_queue.shift();
//         upload(data.file, data.bar, data.file_type);
//     };
//
//     var queue_upload = function(file) {
//         // Determine file type
//         var file_type = determineFileType(file.name);
//         if (!file_type) {
//             console.error("Unknown file type for: " + file.name);
//             return;
//         }
//
//         var bar = $('<div class="progress"><span class="meter" style="width: 0%"></span></div>')
//             .attr('data-filename', file.name)
//             .attr('data-filetype', file_type)
//             .prependTo(progress);
//
//         upload_queue.push({
//             file: file,
//             bar: bar,
//             file_type: file_type
//         });
//     };
//
//     // Set up dropzone event handlers
//     dropzone.on('dragenter', function() {
//         $(this).toggleClass('drag-over', true);
//     });
//
//     dropzone.on('dragleave drop', function() {
//         $(this).toggleClass('drag-over', false);
//     });
//
//     dropzone.on('dragover', function() {
//         return false;
//     });
//
//     dropzone.on('drop', function(e) {
//         var files = e.originalEvent.dataTransfer.files;
//         for (var i = 0; i < files.length; i++) {
//             queue_upload(files[i]);
//         }
//         process_upload_queue();
//         return false;
//     });
//
//     drop_button.on('change', function() {
//         var files = this.files;
//         for (var i = 0; i < files.length; i++) {
//             queue_upload(files[i]);
//         }
//         process_upload_queue();
//     });
//
//     // Initialize status indicators
//     $.each(required_files, function(key, value) {
//         updateStatus(key, '', false);
//     });
// };
//
// // Initialize on document ready
// $(document).ready(function() {
//     $('.upload').each(function() {
//         DataImportUpload($(this));
//     });
// });
