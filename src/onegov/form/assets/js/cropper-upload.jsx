var CropperWidget = React.createClass({
    getInitialState: function() {
        return {
            language: document.documentElement.getAttribute("lang").split('-')[0] || "en",
            aspectRatio: this.props.initialAspectRatio
        };
    },
    getAspectRatioNumber: function(aspectRatio) {
        var components = aspectRatio.split(':');
        if (components.length === 2) {
            return parseInt(components[0]) / parseInt(components[1]);
        }
        return NaN
    },
    componentDidMount: function() {
        var node = $(ReactDOM.findDOMNode(this));
        node.find('.cropper-widget-canvas-container img').cropper({
            viewMode: 1,
            aspectRatio: this.getAspectRatioNumber(this.props.initialAspectRatio),
            autoCropArea: 1,
            dragMode: 'move',
            rotatable: false,
            scalable: false,
            toggleDragModeOnDblclick: false,
        });
    },
    componentWillUnmount: function() {
        var node = $(ReactDOM.findDOMNode(this));
        node.find('.cropper-widget-canvas-container img').data('cropper').destroy();
    },
    handleAspectRatioChange: function(e) {
        var node = $(ReactDOM.findDOMNode(this));
        var state = _.extend({}, this.state);
        state.aspectRatio = e.target.value;
        node.find('.cropper-widget-canvas-container img').data('cropper').setAspectRatio(
            this.getAspectRatioNumber(state.aspectRatio)
        );
        this.setState(state);
    },
    handleSubmit: function(e) {
        var self = this;
        var node = $(ReactDOM.findDOMNode(this));
        var cropper = node.find('.cropper-widget-canvas-container img').data('cropper');
        // if the cropped area is different from the canvas we will
        // generate a cropped canvas and pass it to the callback
        var canvasBox = cropper.getCanvasData();
        var cropBox = cropper.getCropBoxData();
        var canvas = null;
        if (canvasBox.width !== cropBox.width || canvasBox.height !== cropBox.height) {
            canvas = cropper.getCroppedCanvas({
                fillColor: '#fff',
                imageSmoothingEnabled: false,
                rounded: true,
            });
        }

        setTimeout(function() {
            self.props.onSubmit.call(node, canvas);
        }, 0);

        e.preventDefault();
    },
    handleCancel: function(e) {
        var self = this;
        var node = $(ReactDOM.findDOMNode(this));

        setTimeout(function() {
            self.props.onCancel.call(node);
        }, 0);

        e.preventDefault();
    },
    i18n: {
        de: {
            'Aspect ratio': 'Seitenverhältnis',
            'Free': 'Beliebig',
            'Confirm': 'Bestätigen',
            'Cancel': 'Abbrechen'
        },
        fr: {
            'Aspect ratio': 'Format',
            'Free': 'Libre',
            'Confirm': 'Sélectionner',
            'Cancel': 'Annuler'
        },
        it: {
            'Aspect ratio': 'Formato',
            'Free': 'Libero',
            'Confirm': 'Seleziona',
            'Cancel': 'Annulla'
        }
    },
    translate: function(text) {
        return this.i18n[this.state.language] && this.i18n[this.state.language][text] || text;
    },
    render: function() {
        return (
            <div className="cropper-widget">
                <div className="cropper-widget-canvas-container">
                    <img src={this.props.src} />
                </div>
                <div className="cropper-widget-toolbar">
                    {
                        !this.props.fixedAspectRatio &&
                        <label>
                            {this.translate('Aspect ratio')}
                            <select
                                name="aspect-ratio"
                                value={this.state.aspectRatio}
                                onChange={this.handleAspectRatioChange}
                            >
                                <option value="free">{this.translate('Free')}</option>
                                <option value="16:9">16:9</option>
                                <option value="4:3">4:3</option>
                                <option value="3:2">3:2</option>
                                <option value="1:1">1:1</option>
                                <option value="2:3">2:3</option>
                                <option value="4:5">4:5</option>
                                <option value="9:16">9:16</option>
                            </select>
                        </label>
                    }
                    <button className="button secondary prefix" onClick={this.handleCancel}>
                        {this.translate('Cancel')}
                    </button>
                    <button className="button postfix" onClick={this.handleSubmit}>
                        {this.translate('Confirm')}
                    </button>
                </div>
            </div>
        );
    }
});

CropperWidget.render = function(element, src, initialAspectRatio, fixedAspectRatio, onSubmit, onCancel) {

    ReactDOM.render(
        <CropperWidget
            src={src}
            initialAspectRatio={initialAspectRatio}
            fixedAspectRatio={fixedAspectRatio}
            onSubmit={onSubmit}
            onCancel={onCancel}
        />,
        element);
};

var initCropperUploadFields = function(elements) {
    $(elements).find('.cropper-upload-widget input[type="file"]').change(function() {
        if (
            $(this).data('ignore-change') ||
            this.files.length !== 1 ||
            ![
                'image/apng',
                'image/bmp',
                'image/gif',
                'image/jpeg',
                'image/pjpeg',
                'image/png',
                'image/webp'
            ].includes(this.files[0].type)
        ) {
            return;
        }

        var self = this;
        var container = $('<div class="cropper-widget-container" />');
        if ($(this).data('circular')) {
            container.addClass('cropper-widget-circular');
        }
        container.click(function(e) {
            // avoids the parent label seeing a click, which would
            // forward it to the first radio button
            e.preventDefault();
        });
        $(this).closest('.cropper-upload-widget').append(container);
        CropperWidget.render(
            container.get(0),
            URL.createObjectURL(this.files[0]),
            $(this).data('initial-aspect-ratio') || 'free',
            $(this).data('fixed-aspect-ratio') || false,
            function(canvas) {
                if (canvas) {
                    var targetType = 'image/png';
                    if (
                        [
                            'image/jpeg',
                            'image/pjpeg',
                            'image/webp'
                        ].includes(self.files[0].type)
                    ) {
                        targetType = 'image/jpeg';
                    }
                    container.hide();
                    canvas.toBlob(function(blob) {
                        container.remove();
                        if (!blob) {
                            // NOTE: for now we ignore this error and just leave
                            //       the original upload, in the future we may
                            //       want to display an error, but it won't really
                            //       help users solve this issue, so they'll be
                            //       frustrated either way. We could move the
                            //       cropping to the server-side to avoid this
                            //       if we find a lot of users have issues with
                            //       client-side cropping.
                            return;
                        }
                        var transfer = new DataTransfer();
                        var file = new File(
                            [blob],
                            self.files[0].name,
                            {
                                'type': targetType,
                                'lastModified': new Date().getTime()
                            }
                        );
                        transfer.items.add(file);
                        self.files = transfer.files;
                        $(self).data('ignore-change', true);
                        // for better browser compatibility we emit a change event
                        self.dispatchEvent(new Event('change', {'bubbles': true}));
                        $(self).data('ignore-change', false);
                    }, targetType, 0.9);
                } else {
                    container.remove();
                }
            },
            function() {
                container.remove();
            }
        );
    });
}

$(document).ready(function() {
    initCropperUploadFields($('body'));
});

$(document).on('process-common-nodes', initCropperUploadFields);
