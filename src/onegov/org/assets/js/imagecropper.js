if (!RedactorPlugins) var RedactorPlugins = {};

(function($)
{
    RedactorPlugins.imagecropper = function()
    {
        return {
            init: function()
            {
                this.imagecropper.baseTraverseFile = this.upload.traverseFile;
                this.upload.traverseFile = this.imagecropper.traverseFile;
            },
            traverseFile: function(file, e)
            {
                if (
                    this.upload.$el.closest('#redactor-modal-image-insert').length === 0 ||
                    ![
                        'image/apng',
                        'image/bmp',
                        'image/gif',
                        'image/jpeg',
                        'image/pjpeg',
                        'image/png',
                        'image/webp'
                    ].includes(file.type)
                ) {
                    this.imagecropper.baseTraverseFile(file, e);
                    return;
                }

                this.upload.$cropper = $('<div class="redactor-cropper" />');
                if (this.opts.imageCropperCircular) {
                    this.upload.$cropper.addClass('cropper-widget-circular');
                }
                this.upload.$el.append(this.upload.$cropper);
                $('#redactor-modal-tabber').hide();
                this.upload.$droparea.hide();
                var self = this;
                CropperWidget.render(
                    this.upload.$cropper.get(0),
                    URL.createObjectURL(file),
                    this.opts.imageCropperInitialAspectRatio || 'free',
                    this.opts.imageCropperFixedAspectRatio || false,
                    function(canvas) {
                        if (canvas) {
                            var targetType = 'image/png';
                            if (
                                [
                                    'image/jpeg',
                                    'image/pjpeg',
                                    'image/webp'
                                ].includes(file.type)
                            ) {
                                targetType = 'image/jpeg';
                            }
                            self.upload.$cropper.hide();
                            canvas.toBlob(function(blob) {
                                self.upload.$cropper.remove();
                                if (!blob) {
                                    // NOTE: for now we ignore this error and just leave
                                    //       the original upload, in the future we may
                                    //       want to display an error, but it won't really
                                    //       help users solve this issue, so they'll be
                                    //       frustrated either way. We could move the
                                    //       cropping to the server-side to avoid this
                                    //       if we find a lot of users have issues with
                                    //       client-side cropping.
                                    self.imagecropper.baseTraverseFile(file, e);
                                    self.upload.$cropper.remove();
                                    return;
                                }
                                var cropped = new File(
                                    [blob],
                                    file.name,
                                    {
                                        'type': targetType,
                                        'lastModified': new Date().getTime()
                                    }
                                );
                                self.imagecropper.baseTraverseFile(cropped, e);
                            }, targetType, 0.9);
                        } else {
                            self.imagecropper.baseTraverseFile(file, e);
                            self.upload.$cropper.remove();
                        }
                        $('#redactor-modal-tabber').show();
                        self.upload.$droparea.show();
                    },
                    function() {
                        self.upload.$input.val(null);
                        self.upload.$cropper.remove();
                        $('#redactor-modal-tabber').show();
                        self.upload.$droparea.show();
                    }
                );
            }
        };
    };
})(jQuery);
